import os
from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
PDF_DIR = DATA_DIR / "pdfs"
FAISS_DIR = DATA_DIR / "faiss_store"

class Settings(BaseSettings):
    EMBEDDING_MODEL: str = "tfidf-vectorizer"
    SIMILARITY_THRESHOLD: float = 0.085
    TOP_K: int = 4

    LLM_PROVIDER: str = "extractive"  # "ollama", "groq", "extractive"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2:3b"

    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.1-8b-instant"

    GEMINI_API_KEY: str = ""

    class Config:
        env_file = os.path.join(BASE_DIR, "backend", ".env")
        extra = "ignore"

settings = Settings()

