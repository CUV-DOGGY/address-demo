import unittest
from unittest.mock import AsyncMock, Mock, patch

from fastapi import FastAPI

from app.core.lifespan import lifespan


class LifespanTests(unittest.IsolatedAsyncioTestCase):
    async def test_connects_and_closes_mongodb(self) -> None:
        app = FastAPI()
        database = object()
        client = Mock()
        client.admin.command = AsyncMock()
        client.close = AsyncMock()
        client.__getitem__ = Mock(return_value=database)

        with patch("app.core.lifespan.AsyncMongoClient", return_value=client):
            async with lifespan(app):
                client.admin.command.assert_awaited_once_with("ping")
                self.assertIs(app.state.mongo_client, client)
                self.assertIs(app.state.mongo_database, database)

        client.close.assert_awaited_once_with()

    async def test_closes_client_when_startup_ping_fails(self) -> None:
        app = FastAPI()
        client = Mock()
        client.admin.command = AsyncMock(side_effect=RuntimeError("unavailable"))
        client.close = AsyncMock()

        with patch("app.core.lifespan.AsyncMongoClient", return_value=client):
            with self.assertRaisesRegex(RuntimeError, "unavailable"):
                async with lifespan(app):
                    self.fail("lifespan should not start after a failed ping")

        client.close.assert_awaited_once_with()


if __name__ == "__main__":
    unittest.main()
