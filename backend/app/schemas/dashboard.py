from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from typing import Optional

class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None

class ProjectResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    created_at: datetime
    is_active: bool

    class Config:
        from_attributes = True

class ApiKeyCreate(BaseModel):
    pass

class ApiKeyResponse(BaseModel):
    id: UUID
    key_prefix: str
    is_active: bool
    created_at: datetime
    raw_key: Optional[str] = None

    class Config:
        from_attributes = True
