"""Centralized API router aggregation for all endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from app.routers import ask, geocode, health, plan

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(plan.router, tags=["plan"])
api_router.include_router(geocode.router, tags=["geocode"])
api_router.include_router(ask.router, tags=["ask"])

__all__ = ["api_router"]
