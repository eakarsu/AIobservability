from fastapi import APIRouter
from app.api.v1 import ingest, query, alerts, projects

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(ingest.router, tags=["Telemetry Ingestion"])
api_router.include_router(query.router, tags=["Metrics & Events"])
api_router.include_router(alerts.router, tags=["Alerts"])
api_router.include_router(projects.router, tags=["Projects"])
