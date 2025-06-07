from fastapi import APIRouter

from app.api.v1.endpoints import health, scrape, leads, analytics, export, websocket
from app.api import jobs

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(scrape.router, prefix="/scrape", tags=["scraping"])
api_router.include_router(leads.router, prefix="/leads", tags=["leads"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(export.router, prefix="/export", tags=["export"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["background-jobs"])
api_router.include_router(websocket.router, tags=["websocket"])
