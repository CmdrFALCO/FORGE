"""Route package wiring for FORGE API v1 endpoints."""

from fastapi import APIRouter

from forge.api.routes import calculation, system, validation

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(system.router, tags=["System"])
api_router.include_router(validation.router, tags=["Validation"])
api_router.include_router(calculation.router, tags=["Calculation"])

__all__ = ["api_router"]
