import uuid
import secrets
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base

class Project(Base):
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(256), nullable=False, unique=True)
    description = Column(String(1024))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    tenant_id = Column(String(128), nullable=True, index=True)
    retention_days = Column(Integer, nullable=False, default=30)

    api_keys = relationship("ApiKey", back_populates="project")

class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    key_hash = Column(String(128), nullable=False)
    key_prefix = Column(String(12), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    role = Column(String(32), nullable=False, default="viewer")

    project = relationship("Project", back_populates="api_keys")

    @staticmethod
    def generate_key():
        key = f"aio_{secrets.token_urlsafe(32)}"
        return key
