"""Health and readiness routes."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
@router.get("/api/health")
async def health() -> dict[str, str]:
    """Return a no-dependency liveness response."""
    return {"status": "ok", "service": "SaansPlan"}
