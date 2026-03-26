# **Gamuda Intelligence System**

## **1\. Functional Overview**

The Gamuda Intelligence System is a centralized decision-support platform engineered to integrate heterogeneous data sources for construction project oversight. The system facilitates the automated cross-referencing of unstructured engineering narratives (e.g., site status reports) with structured financial datasets (e.g., budgetary CSV files).

## **2\. Technical Architecture**

The system is built upon a state-aware multi-agent graph orchestrated via **LangGraph**. This architecture ensures deterministic routing of queries based on semantic intent:

* **Intelligent Router:** Analyzes the user's input to determine if the query requires tabular data processing or document-based context extraction.  
* **Data Analysis Agent:** Utilizes the pandas library to perform calculations and data extraction from structured CSV files located in the /data directory.  
* **Document Q\&A Agent:** Executes a Retrieval-Augmented Generation (RAG) pipeline. It utilizes a hybrid search strategy combining BM25 lexical ranking and vector similarity (0.4/0.6 weighting) to ensure precision for technical identifiers.  
* **Response Synthesis:** Fuses inputs from the active agents into a single, grounded response containing mandatory source attributions.

## **3\. Implementation Details**

* **Inference Engine:** Gemini 2.0 Flash / Gemini 3.0 Flash Preview.  
* **Vector Store:** Local ChromaDB instance for data residency compliance.  
* **Retrieval Logic:** Recursive character splitting with a 500-token chunk size and a 100-token overlap.  
* **Sampling:** Temperature is set to 0.0 to ensure deterministic, reproducible outputs.

## **4\. Operational Setup**

### **4.1 Local Development Environment**

1. **Prerequisites:** Python 3.11 or higher and Node.js 18 or higher are required.  
2. **Environment Configuration:** Define the GOOGLE\_API\_KEY and PORT in a .env file at the project root.  
3. **Dependency Installation:**  
   pip install \-r requirements.txt  
   npm install

4. **Execution:**  
   * Start the backend: python server.py  
   * Start the frontend: npm run dev

### **4.2 Production Deployment**

The system is containerized for Google Cloud Run deployment. The following resource specifications are mandatory for stable operation:

* **Memory:** 4GiB (required for initializing the ChromaDB and LangChain libraries).  
* **CPU:** 2 vCPUs.

**Deployment Command:**  
gcloud run deploy gamuda-intel-system \\  
  \--source . \\  
  \--region \[REGION\] \\  
  \--memory 4Gi \\  
  \--cpu 2 \\  
  \--allow-unauthenticated

## **5\. Performance Evaluation**

The system's retrieval and grounding capabilities are validated using the RAGAS framework, specifically monitoring **Faithfulness** (contextual grounding) and **Answer Relevancy**.  
**Notice:** This document and the associated source code are proprietary to Gamuda's digital transformation initiatives and are intended for authorized use only.