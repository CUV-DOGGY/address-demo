import unittest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock
from uuid import UUID, uuid4

from app.repository.address_repository import AddressRepository
from app.routers.address_routers import get_address
from app.schema.address_schema import Address, PoiAddressLocation
from app.service.address_service import (
    AddressDataIntegrityError,
    AddressGetError,
    AddressService,
)


def make_address_data(address_id: UUID, user_id: UUID) -> dict[str, object]:
    return {
        "address_id": str(address_id),
        "user_id": str(user_id),
        "receiver_name": "张三",
        "phone_number": "13800138000",
        "display_address": "科技园",
        "detail_address": "某大厦 1001 室",
        "location": {
            "source": "poi",
            "coordinate": "113.934528,22.540503",
            "adcode": "440305",
            "amap_poi_id": "B0XXXXXX",
        },
        "is_default": True,
        "status": "active",
        "version": 1,
        "canonical_address": "广东省深圳市南山区高新南一道",
        "adcode": "440305",
        "deleted_at": None,
        "created_at": datetime(2026, 8, 8, tzinfo=timezone.utc),
        "updated_at": datetime(2026, 8, 9, tzinfo=timezone.utc),
    }


class AddressGetTests(unittest.IsolatedAsyncioTestCase):
    async def test_repository_gets_address_by_string_id_without_mongo_id(self) -> None:
        address_id = uuid4()
        user_id = uuid4()
        address_data = make_address_data(address_id, user_id)
        collection = Mock()
        collection.find_one = AsyncMock(return_value=address_data)
        database = Mock()
        database.get_collection.return_value = collection
        repository = AddressRepository(database)

        result = await repository.get_address(address_id, user_id)

        collection.find_one.assert_awaited_once_with(
            {
                "address_id": str(address_id),
                "user_id": str(user_id),
                "status": "active",
            },
            {"_id": False},
        )
        self.assertEqual(result, address_data)

    async def test_service_returns_address_and_converts_address_id(self) -> None:
        address_id = uuid4()
        user_id = uuid4()
        repository = Mock()
        repository.get_address = AsyncMock(
            return_value=make_address_data(address_id, user_id)
        )
        service = AddressService(repository, Mock(), Mock())

        result = await service.get_address(address_id, user_id)

        repository.get_address.assert_awaited_once_with(address_id, user_id)
        self.assertIsInstance(result, Address)
        self.assertEqual(result.address_id, address_id)
        self.assertIsInstance(result.location, PoiAddressLocation)
        self.assertEqual(result.display_address, "科技园")
        self.assertEqual(
            result.canonical_address,
            "广东省深圳市南山区高新南一道",
        )

    async def test_service_reads_legacy_address_field_names(self) -> None:
        address_id = uuid4()
        user_id = uuid4()
        legacy_address_data = make_address_data(address_id, user_id)
        legacy_address_data["shipping_address"] = legacy_address_data.pop(
            "display_address"
        )
        legacy_address_data["formatted_address"] = legacy_address_data.pop(
            "canonical_address"
        )
        repository = Mock()
        repository.get_address = AsyncMock(return_value=legacy_address_data)
        service = AddressService(repository, Mock(), Mock())

        result = await service.get_address(address_id, user_id)

        self.assertEqual(result.display_address, "科技园")
        self.assertEqual(
            result.canonical_address,
            "广东省深圳市南山区高新南一道",
        )

    async def test_service_raises_when_repository_returns_none(self) -> None:
        address_id = uuid4()
        user_id = uuid4()
        repository = Mock()
        repository.get_address = AsyncMock(return_value=None)
        service = AddressService(repository, Mock(), Mock())

        with self.assertRaisesRegex(AddressGetError, "地址不存在"):
            await service.get_address(address_id, user_id)

    async def test_service_converts_invalid_persisted_address_to_integrity_error(
        self,
    ) -> None:
        address_id = uuid4()
        user_id = uuid4()
        invalid_address = make_address_data(address_id, user_id)
        invalid_address.pop("version")
        repository = Mock()
        repository.get_address = AsyncMock(return_value=invalid_address)
        service = AddressService(repository, Mock(), Mock())

        with self.assertRaisesRegex(AddressDataIntegrityError, "地址数据异常"):
            await service.get_address(address_id, user_id)

    async def test_router_accepts_address_id_and_returns_address(self) -> None:
        address_id = uuid4()
        user_id = uuid4()
        address_data = make_address_data(address_id, user_id)
        expected = Address.model_validate(address_data)
        service = Mock()
        service.get_address = AsyncMock(return_value=expected)

        result = await get_address(address_id, user_id, service)

        service.get_address.assert_awaited_once_with(address_id, user_id)
        self.assertEqual(result, expected)

    async def test_router_propagates_get_error_to_global_handler(self) -> None:
        address_id = uuid4()
        user_id = uuid4()
        service = Mock()
        service.get_address = AsyncMock(
            side_effect=AddressGetError("地址不存在")
        )

        with self.assertRaisesRegex(AddressGetError, "地址不存在"):
            await get_address(address_id, user_id, service)


if __name__ == "__main__":
    unittest.main()
