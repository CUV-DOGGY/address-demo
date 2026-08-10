import unittest
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

from fastapi import HTTPException

from app.repository.address_repository import AddressRepository
from app.routers.address_routers import get_address_status
from app.service.address_service import AddressService, AddressStatusGetError


class AddressStatusTests(unittest.IsolatedAsyncioTestCase):
    async def test_repository_returns_address_status(self) -> None:
        address_id = uuid4()
        user_id = uuid4()
        collection = Mock()
        collection.find_one = AsyncMock(return_value={"status": "active"})
        database = Mock()
        database.get_collection.return_value = collection
        repository = AddressRepository(database)

        result = await repository.get_address_status(address_id, user_id)

        collection.find_one.assert_awaited_once_with(
            {
                "address_id": str(address_id),
                "user_id": str(user_id),
            },
            {"_id": False, "status": True},
        )
        self.assertEqual(result, "active")

    async def test_repository_returns_none_when_address_does_not_exist(self) -> None:
        collection = Mock()
        collection.find_one = AsyncMock(return_value=None)
        database = Mock()
        database.get_collection.return_value = collection
        repository = AddressRepository(database)

        result = await repository.get_address_status(uuid4(), uuid4())

        self.assertIsNone(result)

    async def test_service_returns_active_as_a_valid_status(self) -> None:
        address_id = uuid4()
        user_id = uuid4()
        repository = Mock()
        repository.get_address_status = AsyncMock(return_value="active")
        service = AddressService(repository, Mock(), Mock())

        result = await service.get_address_status(address_id, user_id)

        repository.get_address_status.assert_awaited_once_with(address_id, user_id)
        self.assertEqual(result, "active")

    async def test_service_raises_when_repository_returns_none(self) -> None:
        repository = Mock()
        repository.get_address_status = AsyncMock(return_value=None)
        service = AddressService(repository, Mock(), Mock())

        with self.assertRaisesRegex(AddressStatusGetError, "获取地址状态失败"):
            await service.get_address_status(uuid4(), uuid4())

    async def test_router_accepts_address_id_and_returns_status(self) -> None:
        address_id = uuid4()
        user_id = uuid4()
        service = Mock()
        service.get_address_status = AsyncMock(return_value="deleted")

        result = await get_address_status(address_id, user_id, service)

        service.get_address_status.assert_awaited_once_with(address_id, user_id)
        self.assertEqual(result, "deleted")

    async def test_router_maps_status_error_to_http_500(self) -> None:
        service = Mock()
        service.get_address_status = AsyncMock(
            side_effect=AddressStatusGetError("获取地址状态失败")
        )

        with self.assertRaises(HTTPException) as context:
            await get_address_status(uuid4(), uuid4(), service)

        self.assertEqual(context.exception.status_code, 500)
        self.assertEqual(context.exception.detail, "获取地址状态失败")


if __name__ == "__main__":
    unittest.main()
