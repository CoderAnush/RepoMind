from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

class ChatRequest(BaseModel):
    repository_id: str
    message: str
    session_id: Optional[str] = None  # UUID representing the chat session/thread

class ChatReference(BaseModel):
    file_path: str
    symbol_name: Optional[str] = None
    snippet: str

class ChatMessageResponse(BaseModel):
    id: str
    role: str
    message: str
    references: Optional[List[Dict[str, Any]]] = None
    evidence: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True

class ChatResponse(BaseModel):
    answer: str
    session_id: str
    references: List[ChatReference]
    evidence: Optional[Dict[str, Any]] = None
