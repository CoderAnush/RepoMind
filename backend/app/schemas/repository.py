from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, HttpUrl

class RepositoryBase(BaseModel):
    name: str
    github_url: str
    branch: Optional[str] = "main"

class RepositoryCreate(BaseModel):
    github_url: str
    branch: Optional[str] = "main"

class RepositoryUpdate(BaseModel):
    status: Optional[str] = None
    metadata_info: Optional[Dict[str, Any]] = None

class RepositoryResponse(RepositoryBase):
    id: str
    owner_id: str
    status: str
    metadata_info: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
