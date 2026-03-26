# **Key Technical Trade-offs**

This log tracks critical decisions made during the development of the Gamuda Intelligence System, justifying the technical reasoning behind the current implementation.

| ID | Decision | Rationale |
| :---- | :---- | :---- |
| **D01** | **LangGraph Orchestration** | Unlike linear chains, LangGraph supports stateful persistence and conditional routing between the Data Agent and Doc Agent. |
| **D02** | **Hybrid Search (BM25 \+ Vector)** | Vector search alone often misses specific codes like "SR-992". BM25 ensures 100% accuracy for keyword lookups. |
| **D03** | **Local ChromaDB** | Chosen to ensure data residency and eliminate dependency on external cloud indexing for sensitive construction data. |
| **D04** | **Gemini 3.0 Flash** | Selected for production to balance high-speed inference with reliable tool-calling and reasoning. |
| **D05** | **Temperature \= 0.0** | Forced deterministic output. In construction auditing, "creativity" is a hallucination risk; reproducibility is a requirement. |
| **D06** | **Ensemble Weights (0.4/0.6)** | Optimized to prioritize semantic meaning (Vector) while maintaining strong keyword adherence (BM25). |
| **D07** | **Recursive Splitting (500/100)** | Balanced to ensure technical IDs and their descriptions remain in the same retrieval window. |
| **D08** | **Cloud Run Memory (4GiB)** | Allocated to prevent startup "TCP probe" failures caused by the heavy resource load of AI and data science libraries. |

