from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
import uuid
from app.core.database import get_db
from app.core.security import hash_api_key
from app.models.projects import Project, ApiKey
from app.schemas.dashboard import ProjectCreate, ProjectResponse, ApiKeyResponse

router = APIRouter()

@router.post("/projects", response_model=ProjectResponse, status_code=201)
async def create_project(
    project: ProjectCreate,
    db: AsyncSession = Depends(get_db),
):
    db_project = Project(
        id=uuid.uuid4(),
        name=project.name,
        description=project.description,
    )
    db.add(db_project)
    await db.commit()
    await db.refresh(db_project)
    return db_project

@router.get("/projects", response_model=list[ProjectResponse])
async def list_projects(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).where(Project.is_active == True))
    return result.scalars().all()

@router.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).where(Project.id == UUID(project_id)))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@router.post("/projects/{project_id}/api-keys", response_model=ApiKeyResponse, status_code=201)
async def create_api_key(
    project_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Project).where(Project.id == UUID(project_id)))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Project not found")

    raw_key = ApiKey.generate_key()
    api_key = ApiKey(
        id=uuid.uuid4(),
        project_id=UUID(project_id),
        key_hash=hash_api_key(raw_key),
        key_prefix=raw_key[:12],
    )
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)

    response = ApiKeyResponse(
        id=api_key.id,
        key_prefix=api_key.key_prefix,
        is_active=api_key.is_active,
        created_at=api_key.created_at,
        raw_key=raw_key,
    )
    return response
