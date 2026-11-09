from pydantic import BaseModel, Field
from typing import List, Optional

class SourceCitation(BaseModel):
    source_file: str
    page_number: int
    category: str
    snippet: str
    score: float

class AskRequest(BaseModel):
    question: str = Field(..., min_length=2, description="Supervisor question from the shop floor")
    category_filter: Optional[str] = Field(default="All", description="All, Safety, Maintenance, or Quality")

class AskResponse(BaseModel):
    question: str
    answer: str
    is_answerable: bool
    safety_warning: Optional[str] = None
    sources: List[SourceCitation] = []
    llm_used: str
    latency_ms: int

