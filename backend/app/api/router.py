from fastapi import APIRouter
from app.api.v1.authoritative import router as authoritative_router
from app.api.v1.query import router as query_router
from app.api.v1.alerts import router as alerts_router
from app.api.v1.ai import router as ai_router
from app.api.v1.prompt_injection_exposure import router as prompt_injection_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(authoritative_router)
api_router.include_router(query_router)
api_router.include_router(alerts_router)
api_router.include_router(ai_router)
api_router.include_router(prompt_injection_router)
