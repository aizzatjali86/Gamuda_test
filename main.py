import os
import time
import json
import logging
import pandas as pd
from typing import Annotated, List, Union, TypedDict
from datetime import datetime
from dotenv import load_dotenv

# LangChain & Google Generative AI
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import TextLoader, PyPDFLoader, DirectoryLoader
# UPDATED: Import from the specific text_splitters package
try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END

# MOST STABLE IMPORT PATH FOR ENSEMBLE RETRIEVER
try:
    from langchain.retrievers import EnsembleRetriever
except ImportError:
    try:
        from langchain_community.retrievers import EnsembleRetriever
    except ImportError:
        # Fallback for very specific modular versions
        from langchain_community.retrievers.ensemble import EnsembleRetriever

from langchain_community.retrievers import BM25Retriever

# Load environment
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

# --- OBSERVABILITY: STRUCTURED LOGGING ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("GamudaIntel")


def log_agent_call(agent_name: str, input_text: str, output_text: str, start_time: float):
    latency = time.time() - start_time
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "agent": agent_name,
        "latency_sec": round(latency, 3),
        "input_preview": input_text[:50] + "...",
        "output_preview": output_text[:50] + "..."
    }
    logger.info(json.dumps(log_entry))


# --- 1. INITIALIZE MODELS ---
llm = ChatGoogleGenerativeAI(
    model="gemini-3-flash-preview",
    google_api_key=api_key,
    temperature=0,
    max_retries=0
)

embeddings = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-001",
    task_type="retrieval_document",
    google_api_key=api_key
)

# --- 2. ADVANCED RAG PIPELINE (HYBRID SEARCH) ---
DATA_DIR = "./data/"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)


def ingest_documents():
    """Builds a Hybrid Search (Vector + BM25) retriever."""
    loaders = [
        DirectoryLoader(DATA_DIR, glob="**/*.md", loader_cls=TextLoader),
        DirectoryLoader(DATA_DIR, glob="**/*.pdf", loader_cls=PyPDFLoader),
    ]

    docs = []
    for loader in loaders:
        try:
            docs.extend(loader.load())
        except Exception as e:
            logger.error(f"Load error: {e}")

    if not docs: return None

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
    splits = text_splitter.split_documents(docs)

    # 1. Vector Retriever (Semantic)
    vectorstore = Chroma.from_documents(splits, embeddings, collection_name="gamuda_hybrid")
    vector_retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

    # 2. BM25 Retriever (Keyword/ID matching like 'SR-992')
    bm25_retriever = BM25Retriever.from_documents(splits)
    bm25_retriever.k = 4

    # 3. Ensemble (Hybrid)
    return EnsembleRetriever(
        retrievers=[bm25_retriever, vector_retriever],
        weights=[0.4, 0.6]
    )


retriever = ingest_documents()


# --- 3. AGENT DEFINITIONS ---
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], "Conversation history"]
    next_step: str


def invoke_llm_with_backoff(prompt):
    for i in range(5):
        try:
            return llm.invoke(prompt)
        except Exception as e:
            if "429" in str(e):
                time.sleep((2 ** i) * 5)
            else:
                raise e
    return AIMessage(content="API Timeout.")


def router_agent(state: AgentState):
    start = time.time()
    last_msg = state["messages"][-1].content
    prompt = f"Categorize as 'data' (CSVs/tables) or 'docs' (reports/narrative). Request: {last_msg}. Return only the word."
    res = invoke_llm_with_backoff(prompt)
    choice = res.content.strip().lower()
    log_agent_call("Router", last_msg, choice, start)
    return {"next_step": "data" if "data" in choice else "docs"}


def data_agent(state: AgentState):
    start = time.time()
    question = state["messages"][-1].content
    csv_files = [f for f in os.listdir(DATA_DIR) if f.endswith('.csv')]

    if not csv_files:
        return {"messages": [AIMessage(content="No CSV files found in data directory.")]}

    context = ""
    for f in csv_files:
        df = pd.read_csv(os.path.join(DATA_DIR, f))
        context += f"\nSource File: {f}\n{df.to_string()}\n"

    prompt = f"""
    Answer the question using ONLY the provided structured data. 
    You MUST include the 'Source File' name in your answer.

    Question: {question}
    Data:
    {context}
    """
    res = invoke_llm_with_backoff(prompt)
    log_agent_call("DataAgent", question, res.content, start)
    return {"messages": [res]}


def doc_agent(state: AgentState):
    start = time.time()
    question = state["messages"][-1].content
    if not retriever: return {"messages": [AIMessage(content="No docs found.")]}

    hits = retriever.invoke(question)
    context = "\n\n".join([h.page_content for h in hits])
    # Extract unique sources from metadata
    sources = list(set([h.metadata.get('source', 'Unknown') for h in hits]))
    sources_str = ", ".join(sources)

    prompt = f"""
    Context:
    {context}

    Question: {question}

    Instructions:
    - Provide a detailed answer based ONLY on the context.
    - At the end of your response, you MUST provide a 'Sources:' section listing the following files: {sources_str}
    """
    res = invoke_llm_with_backoff(prompt)
    log_agent_call("DocAgent", question, res.content, start)
    return {"messages": [res]}


# --- 4. GRAPH ---
workflow = StateGraph(AgentState)
workflow.add_node("router", router_agent)
workflow.add_node("data_agent", data_agent)
workflow.add_node("doc_agent", doc_agent)
workflow.set_entry_point("router")
workflow.add_conditional_edges("router", lambda x: x["next_step"], {"data": "data_agent", "docs": "doc_agent"})
workflow.add_edge("data_agent", END)
workflow.add_edge("doc_agent", END)
app = workflow.compile()

if __name__ == "__main__":
    while True:
        u = input("\nQuery: ")
        if u.lower() == 'exit': break
        for output in app.stream({"messages": [HumanMessage(content=u)]}):
            for k, v in output.items():
                if k != "router":
                    print(f"\n[{k.upper()} RESPONDING...]")
                    print(f"{v['messages'][-1].content}")