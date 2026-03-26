import os
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
# This imports your original agent logic
from main import app as agent_graph
from langchain_core.messages import HumanMessage

server = FastAPI()

server.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    message: str

@server.post("/api/query")
async def handle_query(request: QueryRequest):
    try:
        # Calls your existing graph in main.py
        inputs = {"messages": [HumanMessage(content=request.message)]}
        result = agent_graph.invoke(inputs)
        return {
            "answer": result["messages"][-1].content
        }
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Serve the 'static' folder (the React dist)
if os.path.exists("./static"):
    server.mount("/", StaticFiles(directory="./static", html=True), name="static")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(server, host="0.0.0.0", port=port)