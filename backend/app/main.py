from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.config import settings
from app.api.router import api_router
from app.api.auth import router as auth_router
from app.core.database import engine

@asynccontextmanager
async def lifespan(_app: FastAPI):
    async with engine.connect() as connection:
        ready = (await connection.execute(text("SELECT to_regclass('observability_events')"))).scalar_one()
        if not ready: raise RuntimeError("Database migration missing; run python scripts/migrate.py")
    yield
    await engine.dispose()

app = FastAPI(title="AI Observability Platform", version="2.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.parsed_cors_origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(api_router)
app.include_router(auth_router, prefix="/api")

@app.get("/health")
async def health():
    try:
        async with engine.connect() as connection: await connection.execute(text("SELECT 1"))
        return {"status": "healthy", "service": "ai-observability"}
    except Exception as exc: raise HTTPException(503, "unready") from exc
