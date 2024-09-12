import json
import os
from typing import Annotated, Literal
from typing_extensions import TypedDict
import time
import asyncio
from flask import Flask, jsonify, request, send_file, send_from_directory, session
import uuid
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import HumanMessage
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.tools.retriever import create_retriever_tool
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent, ToolNode
from langgraph.graph.message import add_messages
from langgraph.graph import END, START, StateGraph


# Used to get configs from the store dictionary. Configs are used to maintain separate chat histories.
def get_session_history(session_id: str):
    return store[session_id]


# Passes the original user input to the state graph
async def gemini_call(inputs, config):
    async for event in runnable.astream_events({"messages": inputs}, config, version="v1"):
        kind = event["event"]
        if kind == "on_chat_model_stream":
            content = event["data"]["chunk"].content
            if content:
                # Empty content in the context of OpenAI or Anthropic usually means
                # that the model is asking for a tool to be invoked.
                # So we only print non-empty content
                # print(event, end="|")
                yield event["data"]["chunk"]
        elif kind == "on_tool_start":
            print("--")
            print(
                f"Starting tool: {event['name']} with inputs: {event['data'].get('input')}"
            )
        elif kind == "on_tool_end":
            print(f"Done tool: {event['name']}")
            print(f"Tool output was: {event['data'].get('output')}")
            print("--")


# Add messages essentially does this with more
# robust handling
# def add_messages(left: list, right: list):
#     return left + right
class State(TypedDict):
    messages: Annotated[list, add_messages]


# Define the function that determines whether to continue or not in the graph
def should_continue(state: State) -> Literal["__end__", "tools"]:
    messages = state["messages"]
    last_message = messages[-1]
    # If there is no function call, then we finish
    if not last_message.tool_calls:
        return END
    # Otherwise if there is, we continue
    else:
        return "tools"


# Define the function that calls the model
async def call_model(state: State, config: RunnableConfig):
    messages = state["messages"]
    # Note: Passing the config through explicitly is required for python < 3.11
    # Since context var support wasn't added before then: https://docs.python.org/3/library/asyncio-task.html#creating-tasks
    response = await model.ainvoke(messages, config)
    # We return a list, because this will get added to the existing list
    return {"messages": response}


# Load API keys from .env
load_dotenv()

# Initialize dictionary of configs. Configs hold the thread_ids.
store = {} # {session_id : {"configurable": {"thread_id" : thread_id}}}

# Create system prompt (Not implemented yet)
system_prompt = (
    "Placeholder"
)
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        ("human", "{input}"),
    ]
)

# Initialize pinecone vector store and create retriever
pinecone_api_key = os.environ.get("PINECONE_API_KEY")
pc = Pinecone(api_key=pinecone_api_key)
index_name = "langchain-test"  # change if desired
existing_indexes = [index_info["name"] for index_info in pc.list_indexes()]
if index_name not in existing_indexes:
    pc.create_index(
        name=index_name,
        dimension=768,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1"),
    )
    while not pc.describe_index(index_name).status["ready"]:
        time.sleep(1)
index = pc.Index(index_name)
embedding = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
vectorstore = PineconeVectorStore(index=index, embedding=embedding)
memory = MemorySaver()
retriever = vectorstore.as_retriever()

# Create tool from retriever
tool = create_retriever_tool(
    retriever,
    "retriever",
    "contains uploaded documents",
)
tools = [tool]

# Make ToolNode using list tools
tool_node = ToolNode(tools)

# Initialize Gemini model
model = ChatGoogleGenerativeAI(model="gemini-1.5-flash")

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY')

# Set up upload folder for documents
app.config['UPLOAD_FOLDER'] = 'uploads/'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Bind tools to model and create react agent
model = model.bind_tools(tools)
agent_executor = create_react_agent(model, tools, checkpointer=memory, state_modifier=system_prompt)

# Define a new graph
workflow = StateGraph(State)

# Define the two nodes we will cycle between
workflow.add_node("agent", call_model)
workflow.add_node("tools", tool_node)

# Set the entrypoint as `agent`
# This means that this node is the first one called
workflow.add_edge(START, "agent")

# We now add a conditional edge
workflow.add_conditional_edges(
    # First, we define the start node. We use `agent`.
    # This means these are the edges taken after the `agent` node is called.
    "agent",
    # Next, we pass in the function that will determine which node is called next.
    should_continue,
)

workflow.add_edge("tools", "agent")

# Finally, we compile it!
# This compiles it into a LangChain Runnable,
# meaning you can use it as you would any other runnable
runnable = workflow.compile(checkpointer=memory)


# Defines a route for the home page (/) that sends the index.html file from the web directory.
@app.route('/')
def home():
    if 'user_id' not in session:
        # Generate a unique ID for the user
        session['user_id'] = str(uuid.uuid4())

    user_id = session['user_id']
    store[user_id] = {'configurable': {'thread_id': user_id}}
    print(session['user_id'])
    return send_file('templates/index.html')


# Defines a route for the /api/generate endpoint that accepts POST requests.
# When a POST request is received, it gets the JSON data from the request body.
# Extracts the "contents" and "model" from the JSON data.
# Creates a ChatGoogleGenerativeAI model and a HumanMessage with the content.
# Streams the model's response in chunks, sending each chunk as a JSON event stream.
# If an error occurs, it returns a JSON response with the error message.
@app.route("/api/generate", methods=["POST"])
def generate_api():
    if request.method == "POST":
        try:
            req_body = request.get_json()
            content = req_body.get("contents")            
            # Create the human message with the user input
            human_message = HumanMessage(content=content)
            system = SystemMessage(content=system_prompt)
            config = store[session['user_id']]
            async def async_stream():
                async for chunk in gemini_call([human_message], config):
                    yield chunk

            # Generator function to stream the response
            def stream():
                # Run the async generator in a synchronous context
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                async_gen = async_stream()

                while True:
                    try:
                        chunk = loop.run_until_complete(async_gen.__anext__())
                        yield 'data: %s\n\n' % json.dumps({"text": chunk.content})
                    except StopAsyncIteration:
                        break
            return stream(), {'Content-Type': 'text/event-stream'}

        except Exception as e:
            return jsonify({ "error": str(e) })


@app.route('/upload', methods=['POST'])
def upload_file():
    global tools, agent_executor, model, vectorstore, embedding

    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    # Process the file (save it, validate it, etc.)
    file.save(f'uploads/{file.filename}')
    file_path = f'uploads/{file.filename}'
    try:
        # vectorstore = PineconeVectorStore(index=index, embedding=embedding)

        loader = PyPDFLoader(file_path)
        docs = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        splits = text_splitter.split_documents(docs)
        uuids = [str(uuid.uuid4()) for _ in range(len(splits))]

        # Add new documents to the existing vector store
        vectorstore.add_documents(documents=splits, ids=uuids)

        # # Create retriever and tool after updating the vector store
        # retriever = vectorstore.as_retriever()
        # tool = create_retriever_tool(
        #     retriever,
        #     "retriever",
        #     "retrieve outside information needed to respond",
        # )
        # tools = [tool]

        # Rebind tools to the model and recreate agent_executor
        # model = model.bind_tools(tools)
        # agent_executor = create_react_agent(model, tools, checkpointer=memory)

        print("UPLOADED")

        return jsonify({'message': 'File uploaded and added to vector store successfully'})
    finally:
        # Delete the file after processing it
        if os.path.exists(file_path):
            os.remove(file_path)


# Defines a route to serve static files from the web directory for any given path.
# When a request matches the path, it sends the requested file from the web directory.
@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('templates', path)


# If the script is run directly, it starts the Flask app in debug mode.
if __name__ == '__main__':
    app.run(debug=True, port=8000)