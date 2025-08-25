from fastapi import APIRouter
from . import health, jobs, gmail_oauth

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
api_router.include_router(gmail_oauth.router, prefix="/api", tags=["gmail"])  # NEW
