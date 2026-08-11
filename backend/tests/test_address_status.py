import unittest
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

from app.repository.address_repository import (
    AddressRepository,
    AddressRepositoryDataError,
)
from app.routers.address_routers import get_address_status
from app.service.address_service import (
    AddressDataIntegrityError,
    AddressGetError,
    AddressService,
)


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

    async def test_repository_rejects_invalid_persisted_status(self) -> None:
        collection = Mock()
        collection.find_one = AsyncMock(return_value={"status": "unknown"})
        database = Mock()
        database.get_collection.return_value = collection
        repository = AddressRepository(database)

        with self.assertRaisesRegex(
            AddressRepositoryDataError,
            "地址状态字段异常",
        ):
            await repository.get_address_status(uuid4(), uuid4())

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

        with self.assertRaisesRegex(AddressGetError, "地址不存在"):
            await service.get_address_status(uuid4(), uuid4())

    async def test_service_converts_invalid_status_to_integrity_error(self) -> None:
        repository = Mock()
        repository.get_address_status = AsyncMock(
            side_effect=AddressRepositoryDataError("地址状态字段异常")
        )
        service = AddressService(repository, Mock(), Mock())

        with self.assertRaisesRegex(AddressDataIntegrityError, "地址数据异常"):
            await service.get_address_status(uuid4(), uuid4())

    async def test_router_accepts_address_id_and_returns_status(self) -> None:
        address_id = uuid4()
        user_id = uuid4()
        service = Mock()
        service.get_address_status = AsyncMock(return_value="deleted")

        result = await get_address_status(address_id, user_id, service)

        service.get_address_status.assert_awaited_once_with(address_id, user_id)
        self.assertEqual(result, "deleted")

    async def test_router_propagates_status_error_to_global_handler(self) -> None:
        service = Mock()
        service.get_address_status = AsyncMock(
            side_effect=AddressGetError("地址不存在")
        )

        with self.assertRaisesRegex(AddressGetError, "地址不存在"):
            await get_address_status(uuid4(), uuid4(), service)


if __name__ == "__main__":
    unittest.main()
