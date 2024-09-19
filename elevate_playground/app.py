"""
Name: LegalHubChatbot
Description: A chatbot aimed to answer legal questions
Features: Gemini powered chatbot experience

Installation and setup: 
    Python 3.11

    Flask
    python-dotenv
    langchain-core
    langchain-google-genai
    langchain-chroma
    langgraph

    Google Cloud CLI 
        Install at https://cloud.google.com/sdk/docs/install. Run "gcloud auth application-default login" to set application default credentials

    .env must have GOOGLE_API_KEY, LANGCHAIN_API_KEY, and a FLASK_SECRET_KEY
    How I created my secret key:
        import secrets
        secret_key = secrets.token_hex(32))

Usage:
    Run "python3 app.py" to host the app locally

Design:
    
app.py
    The chatbot is initialized when app.py is run. The Gemini model is initialized through langchain (specific model can be changed at this
    step). Flask app is created and the folders for file uploads and the vector store are created. A retriever and an agent are created 
    and langgraph is used to create a workflow between them (discussed more later). The async gemini_call function feeds the user query 
    to the langgraph runnable to generate the response. The /api/generate route gets the user query, makes the API calls, and then returns
    the response. The /upload route handles loading uploaded files.

    API calls:
    The /api/generate route takes in the user query and feeds it to the langgraph. The final response is yielded back. The intermediate 
    interactions between the agent and the retriever are printed to the terminal. This is an async function.

    Workflow:
    The chatbot allows users to upload documents and ask questions about them. Langgraph allows the LLM to use its reasoning
    to decide when looking through the documents is appropriate for the task at hand. The graph for this app only has an agent node 
    and a tool node which contains only a retriever. The agent takes in the user's query and decides if a tool call is necessary.
    If so, the retriever is called and returns the information it thought was relevant to the query. The agent uses the new context
    to generate a response that is then sent to the user. If the retriever wasn't deemed necessary, the agent generates a response
    for the user directly.
    https://langchain-ai.github.io/langgraph/how-tos/tool-calling/

    Document uploading:
    The application supports user-uploaded documents. When a document is uploaded via the /upload route, the PyPDFLoader is used to load
    the file. The text is split into chunks using one of Langchain's text splitters. The splits are added to the vectorstore. A retriever is
    created from the vectorstore object. The retriever is used to create a retriever tool. The tool is bound to the LLM model. Then, the 
    agent is created using the model, the tools, and a MemorySaver object.

main.js
    This file handles the form submission and the suggested prompt buttons. On submission, it makes a call to streamGemini in gemini-api.js.

gemini-api.js
    This file makes the POST request to app.py to make the API call. It also handles streaming the response back to main.js.

Contact:
    Author: Jeremy Brinas
    Email: jt.brinas@gmail.com

"""


import json
import os
from typing import Annotated, Literal
from typing_extensions import TypedDict
import time
import asyncio
from flask import Flask, jsonify, request, send_file, send_from_directory, session, render_template
import uuid
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_core.tools import tool
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
system_prompt = "Respond only in Italian"
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

# @tool("search")
# def search_tool(query: str):
#     """Searches through documents that were uploaded by the user. Search query must be provided
#     in natural language and be verbose."""
#     vectorstore = PineconeVectorStore(index=index, embedding=embedding, namespace=session['user_id'])
#     print(vectorstore.similarity_search(query))
#     return "\n".join([x.content for x in vectorstore.similarity_search(query)])

# Create tool from retriever
retriever_tool = create_retriever_tool(
    retriever,
    "retriever",
    "contains uploaded documents",
)
tools = [retriever_tool]
# tools = [search_tool]

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
agent_executor = create_react_agent(model, tools=tools, checkpointer=memory) #, state_modifier=system_prompt)

inputs = {
    "messages": "using the search tool, tell me about nikes international markets in 2023",
    "intermediate_steps": []
}
out = agent_executor.invoke(inputs, config={"configurable": {"thread_id": "abc123"}})

# print(out[-1].message_log[-1].additional_kwargs["tool_calls"][-1])


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
    user = {'id': session['user_id']} 
    return render_template('index.html', user=user)


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
    # print(None)