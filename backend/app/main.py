from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import allowed_origins

app = FastAPI(
    title="ReguLens AI API",
    description="Regulatory intelligence and change impact assessment API.",
    version="1.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-ReguLens-Request"],
)
app.include_router(router)


@app.get("/", tags=["Root"])
def root() -> dict[str, str]:
    return {"name": "ReguLens AI API", "docs": "/docs", "health": "/api/v1/health"}
