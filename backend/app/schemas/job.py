from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class JobResponse(BaseModel):
    id: str
    repository_id: str
    status: str
    step: str
    error_message: Optional[str] = None
    retries: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
