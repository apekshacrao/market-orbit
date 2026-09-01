"""API Version 1 endpoints."""
from fastapi import APIRouter
from app.api.v1 import auth, uploads, results

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(uploads.router, prefix="/uploads", tags=["uploads"])
api_router.include_router(results.router, prefix="/results", tags=["results"])
