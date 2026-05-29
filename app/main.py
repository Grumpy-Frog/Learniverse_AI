from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.modules.auth.router import router as auth_router
from app.modules.catalog.router import router as catalog_router
from app.modules.simulation.router import router as simulation_router

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/v1/health", tags=["Health"])
def health_check() -> dict[str, str]:
    return {"status": "healthy"}


app.include_router(
    auth_router,
    prefix=settings.api_prefix,
)

app.include_router(
    catalog_router,
    prefix=settings.api_prefix,
)

app.include_router(
    simulation_router,
    prefix=settings.api_prefix,
)