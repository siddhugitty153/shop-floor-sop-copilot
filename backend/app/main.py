import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.schemas import AskRequest, AskResponse
from app.retriever import retriever
from app.llm_service import generate_grounded_answer
from app.config import settings

app = FastAPI(
    title="BiztelAI Shop-Floor SOP Copilot",
    description="Grounded RAG Copilot for Manufacturing Supervisors",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {
        "status": "online",
        "indexed_chunks": len(retriever.metadata),
        "similarity_threshold": settings.SIMILARITY_THRESHOLD,
        "configured_llm": settings.LLM_PROVIDER
    }

@app.get("/documents")
def list_documents():
    docs = {}
    for item in retriever.metadata:
        fname = item["source_file"]
        if fname not in docs:
            docs[fname] = {"source_file": fname, "category": item["category"], "chunks": 0, "max_page": 0}
        docs[fname]["chunks"] += 1
        docs[fname]["max_page"] = max(docs[fname]["max_page"], item["page_number"])
    return {"documents": list(docs.values())}

@app.post("/ask", response_model=AskResponse)
def ask_sop_copilot(req: AskRequest):
    start_ts = time.perf_counter()
    sources = retriever.retrieve(req.question, req.category_filter or "All")

    result = generate_grounded_answer(req.question, sources)
    elapsed_ms = int((time.perf_counter() - start_ts) * 1000)

    # If LLM determined the retrieved chunks didn't actually answer the question, clear sources
    final_sources = sources if result["is_answerable"] else []

    return AskResponse(
        question=req.question,
        answer=result["answer"],
        is_answerable=result["is_answerable"],
        safety_warning=result["safety_warning"],
        sources=final_sources,
        llm_used=result["llm_used"],
        latency_ms=elapsed_ms
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
