from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.modules.auth.router import router as auth_router
from app.modules.catalog.router import router as catalog_router
from app.modules.simulation.router import router as simulation_router
from app.modules.documents.router import router as documents_router
from app.modules.tutor.router import router as tutor_router


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
)


allowed_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
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