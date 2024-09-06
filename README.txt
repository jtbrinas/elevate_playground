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

    .env must have GOOGLE_API_KEY and LANGCHAIN_API_KEY     

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
