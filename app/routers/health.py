"""Health and readiness routes."""

from fastapi import APIRouter, Depends

from app.core.settings import Settings, get_settings

router = APIRouter()


@router.get("/health")
@router.get("/api/health")
async def health(settings: Settings = Depends(get_settings)) -> dict[str, str]:
    """Return a no-dependency liveness response."""
    return {"status": "ok", "service": "SaansPlan"}
