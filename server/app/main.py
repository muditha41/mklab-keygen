"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import admin, auth, licenses
from app.core.config import settings
from app.core.rate_limit import RateLimitMiddleware

app = FastAPI(
    title="SWAPS",
    description="Software & Web Application Protection System — License Verification API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Global rate limit: 100 req/min per IP (then CORS)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    """Health check for load balancers and monitoring."""
    return {"status": "ok", "service": "swaps"}


app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(licenses.router, prefix="/licenses", tags=["licenses"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])
