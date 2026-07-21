from fastapi import APIRouter
from app.api.v1.authoritative import router as authoritative_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(authoritative_router)
