import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.v1.auth import get_current_user
from app.models.user import User
from app.models.repository import Repository
from app.models.chat import ChatHistory
from app.schemas.chat import ChatRequest, ChatResponse, ChatMessageResponse
from app.services.rag import RAGService

router = APIRouter()
rag_service = RAGService()

@router.post("", response_model=ChatResponse)
def query_chatbot(
    chat_in: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Submit a conversational query scoped to a specific repository.
    Leverages vector retrieval and generates answers with source references.
    """
    # 1. Validate ownership of repository
    repo = db.query(Repository).filter(
        Repository.id == chat_in.repository_id,
        Repository.owner_id == current_user.id
    ).first()
    
    if not repo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found or access denied."
        )
        
    session_id = chat_in.session_id or str(uuid.uuid4())
    
    # 2. Query RAG pipeline
    try:
        result = rag_service.query_repository(
            repository_id=chat_in.repository_id,
            user_id=current_user.id,
            message=chat_in.message,
            session_id=session_id,
            db=db
        )
        return result
    except Exception as e:
        logger.error(f"[Chat Endpoint] Failed querying chatbot: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal chat service error: {str(e)}"
        )



@router.get("/history/{repository_id}/{session_id}", response_model=List[ChatMessageResponse])
def get_chat_history(
    repository_id: str,
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Fetch the chronological message sequence for a chat session.
    """
    # Verify ownership
    repo = db.query(Repository).filter(
        Repository.id == repository_id,
        Repository.owner_id == current_user.id
    ).first()
    if not repo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found."
        )
        
    messages = db.query(ChatHistory).filter(
        ChatHistory.repository_id == repository_id,
        ChatHistory.session_id == session_id,
        ChatHistory.user_id == current_user.id
    ).order_by(ChatHistory.created_at.asc()).all()
    
    return messages
