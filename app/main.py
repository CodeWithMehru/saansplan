"""FastAPI application entry point and security configuration."""

import os

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import MAX_REQUEST_BYTES
from app.limiting import limiter
from app.routers import health, plan

load_dotenv()

app = FastAPI(title="SaansPlan", docs_url=None, redoc_url=None)
app.state.limiter = limiter

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:8000").split(","),
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.middleware("http")
async def security_middleware(request: Request, call_next):
    """Apply body limits and security headers, and hide exception traces."""
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > MAX_REQUEST_BYTES:
        return JSONResponse(status_code=413, content={"detail": "Request body is too large"})
    try:
        response = await call_next(request)
    except Exception:
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
        "connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'"
    )
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(self), camera=(), microphone=()"
    return response


app.include_router(health.router, tags=["health"])
app.include_router(plan.router, tags=["plan"])
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/")
async def index() -> FileResponse:
    """Serve the lightweight application shell."""
    return FileResponse("app/static/index.html")


@app.exception_handler(404)
async def not_found(request: Request, exc) -> JSONResponse:
    """Return a small JSON response for unknown API routes."""
    return JSONResponse(status_code=404, content={"detail": "Not found"})
