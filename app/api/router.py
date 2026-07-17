from fastapi import APIRouter

from app.api.routes import analytics, health, leads, root, webhook

api_router = APIRouter()
api_router.include_router(root.router)
api_router.include_router(health.router)
api_router.include_router(webhook.router)
api_router.include_router(analytics.router)
api_router.include_router(leads.router)
