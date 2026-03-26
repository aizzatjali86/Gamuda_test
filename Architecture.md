# **Technical Architecture Report: Gamuda Intelligence System**

**Date:** March 26, 2026  
**Subject:** Multi-Agent Orchestration for Construction Intelligence  
**Classification:** Technical Design Document (Confidential)  
**Version:** 2.0.1

## **1\. Executive Summary**

The **Gamuda Intelligence System** is a decision-support platform designed to unify unstructured site narratives (PDFs, project reports, site logs) with structured financial datasets (CSV-based ERP exports).  
By leveraging a **State-Aware Multi-Agent Architecture** via LangGraph, the system automates the cross-referencing of engineering risks (e.g., Soil Acidity) with budgetary impacts (e.g., Mitigation Costs). The system acts as an intelligent interface for project managers to query complex site data with high-fidelity grounding.

## **2\. System Methodology: State-Aware Orchestration**

The core architectural pattern is **Multi-Agent Orchestration** implemented via **LangGraph**. This directed acyclic graph (DAG) structure allows for specialized processing nodes and conditional routing based on the semantic intent of the user's query.

### **2.1 Architectural Component Diagram**

graph TD  
    User((User)) \--\> API\[FastAPI Gateway\]  
    API \--\> Router{Intelligent Router}  
      
    subgraph "Specialized Processing Layer"  
        Router \--\>|Tabular Intent| DataAgent\[Data Analysis Agent\]  
        Router \--\>|Narrative Intent| DocAgent\[Document Q\&A Agent\]  
    end  
      
    subgraph "Intelligence Engine"  
        DocAgent \--\> Hybrid\[Hybrid Retrieval Pipeline\]  
        Hybrid \--\> BM25\[Lexical Search\]  
        Hybrid \--\> Vector\[Semantic Search\]  
        DataAgent \--\> Pandas\[DataFrame Execution\]  
    end  
      
    DataAgent \--\> Synthesis\[Response Synthesis\]  
    DocAgent \--\> Synthesis  
    Synthesis \--\> User

### **2.2 Agent Node Definitions**

* **Intelligent Router (router\_agent):** A zero-shot classifier that evaluates the "intent" of a query. It scans for keywords like "budget," "spend," "cost," or "table" to route to the **Data Agent**. Otherwise, it defaults to the **Doc Agent**.  
* **Data Analysis Agent (data\_agent):** Interfaces with pandas to read CSV files directly from the /data directory (e.g., financial\_summary.csv). It converts dataframes to string context, ensuring mathematical calculations are grounded in raw data.  
* **Document Q\&A Agent (doc\_agent):** Manages the retrieval-augmented generation flow. It queries the hybrid retriever to find context from reports (e.g., project\_alpha\_report.md) and synthesizes answers with mandatory source citations.

## **3\. Technology Stack and Justification**

| Layer | Component | Selection | Justification |
| :---- | :---- | :---- | :---- |
| **Inference** | LLM | Gemini 3.0 Flash | 1M+ token context window allows for exhaustive document injection without information loss. |
| **Orchestration** | Framework | LangGraph | Supports stateful persistence and cyclic reasoning, allowing the system to maintain conversation history. |
| **Storage** | Vector Store | ChromaDB (Local) | Ensures data residency and eliminates dependency on external third-party cloud indexing. |
| **Retrieval** | Algorithm | Hybrid (BM25 \+ Vector) | Offsets vector "fuzziness" with lexical precision for critical technical IDs like "SR-992". |
| **Backend** | API | FastAPI | Provides high-performance, asynchronous handling for concurrent agent execution. |

## **4\. Data Engineering & Retrieval Strategy**

### **4.1 Hybrid Retrieval Logic (Ensemble Model)**

The system utilizes a specialized EnsembleRetriever to fuse two distinct search algorithms:

* **BM25 (Weight: 0.4):** Targets keyword-specific tokens. This is critical for finding specific technical codes (e.g., "LOG-A12") that vector embeddings might ignore.  
* **Vector (Weight: 0.6):** Uses models/embedding-001 to find chunks based on semantic meaning (e.g., linking "soil acidity" to "reinforcement corrosion").

### **4.2 Chunking and Token Management**

A **Recursive Character Splitting** strategy is employed:

* **Chunk Size:** 500 tokens. Sized to keep a specific Risk ID and its associated cost in a single retrieval window.  
* **Overlap:** 100 tokens (20%). Ensures continuity of context across chunks to prevent data loss at split points.

## **5\. System Guardrails & Observability**

### **5.1 Structured Logging**

The system implements a custom logging decorator to capture:

* **Latency Tracking:** Measures latency\_sec for every agent node to identify performance bottlenecks.  
* **Traceability:** Logs agent\_name, timestamp, and query\_preview in machine-readable JSON format.

### **5.2 Grounding & Reliability**

* **Deterministic Inference:** The LLM temperature is fixed at 0.0 to ensure reproducibility across sessions.  
* **Contextual Bound:** The system is prompted to answer *only* based on the provided data. If information is missing, it reports "I don't have access to the site reports currently."  
* **Source Attribution:** Metadata is extracted from Chroma chunks to append source filenames to every response.

## **6\. Infrastructure & Deployment**

### **6.1 Cloud Run Configuration**

* **Memory:** 4GiB allocation is required to handle the initialization of heavy libraries (ChromaDB, LangChain, Pandas) during the startup phase.  
* **CPU:** 2 vCPUs are utilized to manage concurrent processing and compute-heavy embedding calculations.  
* **Docker:** A multi-stage build processes the React frontend and serves it via a Python 3.11-slim backend.

**End of Document**