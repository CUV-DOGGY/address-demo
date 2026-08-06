import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def get_allowed_origins() -> list[str]:
    configured_origins = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
    origins = [origin.strip() for origin in configured_origins.split(",") if origin.strip()]
    if "*" in origins:
        raise ValueError("FRONTEND_ORIGIN must contain explicit origins, not '*'")
    return origins


app = FastAPI(title="地图功能demo API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["Accept", "Content-Type"],
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {
        "status": "ok",
        "message": "backend is running",
    }
