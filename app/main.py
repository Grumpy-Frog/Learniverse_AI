from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.modules.auth.router import router as auth_router
from app.modules.catalog.router import router as catalog_router
from app.modules.simulation.router import router as simulation_router
from app.modules.documents.router import router as documents_router
from app.modules.tutor.router import router as tutor_router
from app.modules.rag.router import router as rag_router
from app.modules.diagnostics.router import router as diagnostics_router
from app.modules.remediation.router import router as remediation_router
from app.modules.blog.router import router as blog_router
from app.modules.dashboard.router import router as dashboard_router
from app.modules.custom_tutor.router import router as custom_tutor_router
from app.modules.study_tools.router import router as study_tools_router

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
)

allowed_origins = [
    origin.strip()
    for origin in settings.frontend_origin.split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
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

app.include_router(
    tutor_router,
    prefix=settings.api_prefix,
)

app.include_router(
    documents_router,
    prefix=settings.api_prefix,
)

app.include_router(
    rag_router,
    prefix=settings.api_prefix,
)

app.include_router(
    diagnostics_router,
    prefix=settings.api_prefix,
)

app.include_router(
    remediation_router,
    prefix=settings.api_prefix,
)

app.include_router(
    blog_router,
    prefix=settings.api_prefix,
)

app.include_router(
    dashboard_router,
    prefix=settings.api_prefix,
)

app.include_router(
    custom_tutor_router,
    prefix=settings.api_prefix,
)

app.include_router(
    study_tools_router,
    prefix=settings.api_prefix,
)