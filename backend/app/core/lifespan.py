import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pymongo import AsyncMongoClient

from app.core.config import settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """管理应用级 MongoDB 客户端的启动与关闭。"""

    client = AsyncMongoClient(
        settings.MONGODB_URI,
        serverSelectionTimeoutMS=settings.MONGODB_SERVER_SELECTION_TIMEOUT_MS,
    )

    try:
        await client.admin.command("ping")
        app.state.mongo_client = client
        app.state.mongo_database = client[settings.MONGODB_DATABASE]
        await app.state.mongo_database.get_collection("addresses").create_index(
            "address_id",
            unique=True,
            name="uniq_address_id",
        )
        logger.info("MongoDB connected: database=%s", settings.MONGODB_DATABASE)

        yield
    finally:
        await client.close()
        logger.info("MongoDB connection closed")
