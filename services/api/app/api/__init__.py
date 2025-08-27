"""
API Routes Package
"""
# Import your routers to make them easily accessible
from .routers.gmail_oauth import router as gmail_oauth_router

# List of all API routers
__all__ = ["gmail_oauth_router"]