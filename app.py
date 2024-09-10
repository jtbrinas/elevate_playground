# The json module is used to work with JSON data.
# The os module is used to interact with the operating system.

import json
import os

# Flask: Creates the Flask web application.
# jsonify: Converts data to JSON format for responses.
# request: Accesses incoming request data.
# send_file: Sends files to the client.
# send_from_directory: Sends files from a specified directory.

from flask import Flask, jsonify, request, send_file, send_from_directory, session
import uuid

# HumanMessage from langchain_core.messages: Represents a message from a human user.
# ChatGoogleGenerativeAI from langchain_google_genai: Provides a chat interface for Google's generative AI.

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

# Load the API key hidden in .env
from dotenv import load_dotenv
load_dotenv()

from langchain_core.chat_history import (
    BaseChatMessageHistory,
    InMemoryChatMessageHistory,
)
from langchain_core.runnables.history import RunnableWithMessageHistory

from langchain_community.document_loaders import PyPDFLoader

from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain_core.prompts import ChatPromptTemplate

from langchain.tools.retriever import create_retriever_tool

from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent



# {session_id : {"configurable": {"thread_id" : thread_id}}}
store = {}

def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]


from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages

# Add messages essentially does this with more
# robust handling
# def add_messages(left: list, right: list):
#     return left + right


class State(TypedDict):
    messages: Annotated[list, add_messages]



# Initialize Gemini model
model = ChatGoogleGenerativeAI(model="gemini-1.5-flash")

# Creates a Flask web application named app.
app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY')

# Set up upload folder for documents
app.config['UPLOAD_FOLDER'] = 'uploads/'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# TEST: load demo PDF, split the text, embed, and store
# file_path = "uploads/nike.pdf"
# loader = PyPDFLoader(file_path)
# docs = loader.load()
# text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
# splits = text_splitter.split_documents(docs)
# vectorstore = Chroma.from_documents(documents=splits, embedding=GoogleGenerativeAIEmbeddings(model="models/embedding-001"))
# Initialize the vector store at the start of the app

vectorstore_path = 'vectorstore/'
if not os.path.exists(vectorstore_path):
    os.makedirs(vectorstore_path)

# Initialize an empty vector store
vectorstore = Chroma(
    persist_directory=vectorstore_path, 
    embedding_function=GoogleGenerativeAIEmbeddings(model="models/embedding-001")
)
# vectorstore.add_documents(splits)

memory = MemorySaver()
retriever = vectorstore.as_retriever()

# Create tool
tool = create_retriever_tool(
    retriever,
    "retriever",
    "contains uploaded documents",
)
tools = [tool]

system_prompt = (
    "Your name is Peter Shmeater. You are sarcastic in all your responses."
)

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        ("human", "{input}"),
    ]
)

from langgraph.prebuilt import ToolNode

tool_node = ToolNode(tools)

model = model.bind_tools(tools)

agent_executor = create_react_agent(model, tools, checkpointer=memory, state_modifier=system_prompt)

from typing import Literal

from langchain_core.runnables import RunnableConfig

from langgraph.graph import END, START, StateGraph

# Define the function that determines whether to continue or not
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

from langchain_core.messages import HumanMessage

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


# Defines a route for the home page (/) that sends the index.html file from the web directory.
@app.route('/')
def home():
    if 'user_id' not in session:
        # Generate a unique ID for the user
        session['user_id'] = str(uuid.uuid4())

    user_id = session['user_id']
    store[user_id] = {'configurable': {'thread_id': user_id}}
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
            # def stream():
            #     for chunk in response:
            #         yield 'data: %s\n\n' % json.dumps({ "text": chunk.content })

            return stream(), {'Content-Type': 'text/event-stream'}

        except Exception as e:
            return jsonify({ "error": str(e) })


@app.route('/upload', methods=['POST'])
def upload_file():
    global tools, agent_executor, model, vectorstore

    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    # Process the file (save it, validate it, etc.)
    file.save(f'uploads/{file.filename}')
    file_path = f'uploads/{file.filename}'
    try:
        loader = PyPDFLoader(file_path)
        docs = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        splits = text_splitter.split_documents(docs)

        # Add new documents to the existing vector store
        vectorstore.add_documents(splits)

        # Create retriever and tool after updating the vector store
        retriever = vectorstore.as_retriever()
        tool = create_retriever_tool(
            retriever,
            "retriever",
            "retrieve outside information needed to respond",
        )
        tools = [tool]

        # Rebind tools to the model and recreate agent_executor
        model = model.bind_tools(tools)
        agent_executor = create_react_agent(model, tools, checkpointer=memory)

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
import asyncio
if __name__ == '__main__':
    app.run(debug=True, port=8000)