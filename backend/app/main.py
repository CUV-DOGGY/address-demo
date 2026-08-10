import app.core.logger
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.exception_handlers import register_exception_handlers
from app.core.lifespan import lifespan
from app.routers.address_routers import router as address_router


def get_allowed_origins() -> list[str]:
    return settings.frontend_origins


app = FastAPI(title="地图功能demo API", lifespan=lifespan)
register_exception_handlers(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Accept", "Content-Type"],
)

app.include_router(address_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {
        "status": "ok",
        "message": "backend is running",
    }
