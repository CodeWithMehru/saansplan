"""Health and readiness routes."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health() -> dict:
    """Return a no-dependency liveness response."""
    return {"status": "ok", "service": "SaansPlan"}
