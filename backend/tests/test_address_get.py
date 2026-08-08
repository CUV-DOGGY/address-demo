import unittest
from unittest.mock import AsyncMock, Mock
from uuid import UUID, uuid4

from fastapi import HTTPException

from app.repository.address_repository import AddressRepository
from app.routers.address_routers import get_address
from app.schema.address_schema import Address, PoiAddressLocation
from app.service.address_service import AddressGetError, AddressService


def make_address_data(address_id: UUID) -> dict[str, object]:
    return {
        "address_id": str(address_id),
        "receiver_name": "张三",
        "phone_number": "13800138000",
        "shipping_address": "广东省深圳市南山区科技园",
        "detail_address": "某大厦 1001 室",
        "location": {
            "source": "poi",
            "coordinate": "113.934528,22.540503",
            "adcode": "440305",
            "amap_poi_id": "B0XXXXXX",
        },
        "is_default": True,
        "is_delete": False,
        "formatted_address": "广东省深圳市南山区高新南一道",
        "adcode": "440305",
    }


class AddressGetTests(unittest.IsolatedAsyncioTestCase):
    async def test_repository_gets_address_by_string_id_without_mongo_id(self) -> None:
        address_id = uuid4()
        address_data = make_address_data(address_id)
        collection = Mock()
        collection.find_one = AsyncMock(return_value=address_data)
        database = Mock()
        database.get_collection.return_value = collection
        repository = AddressRepository(database)

        result = await repository.get_address(address_id)

        collection.find_one.assert_awaited_once_with(
            {"address_id": str(address_id)},
            {"_id": False},
        )
        self.assertEqual(result, address_data)

    async def test_service_returns_address_and_converts_address_id(self) -> None:
        address_id = uuid4()
        repository = Mock()
        repository.get_address = AsyncMock(return_value=make_address_data(address_id))
        service = AddressService(repository, Mock())

        result = await service.get_address(address_id)

        repository.get_address.assert_awaited_once_with(address_id)
        self.assertIsInstance(result, Address)
        self.assertEqual(result.address_id, address_id)
        self.assertIsInstance(result.location, PoiAddressLocation)

    async def test_service_raises_when_repository_returns_none(self) -> None:
        address_id = uuid4()
        repository = Mock()
        repository.get_address = AsyncMock(return_value=None)
        service = AddressService(repository, Mock())

        with self.assertRaisesRegex(AddressGetError, "获取地址信息失败"):
            await service.get_address(address_id)

    async def test_router_accepts_address_id_and_returns_address(self) -> None:
        address_id = uuid4()
        expected = Address.model_validate(make_address_data(address_id))
        service = Mock()
        service.get_address = AsyncMock(return_value=expected)

        result = await get_address(address_id, service)

        service.get_address.assert_awaited_once_with(address_id)
        self.assertEqual(result, expected)

    async def test_router_maps_get_error_to_http_500(self) -> None:
        address_id = uuid4()
        service = Mock()
        service.get_address = AsyncMock(
            side_effect=AddressGetError("获取地址信息失败")
        )

        with self.assertRaises(HTTPException) as context:
            await get_address(address_id, service)

        self.assertEqual(context.exception.status_code, 500)
        self.assertEqual(context.exception.detail, "获取地址信息失败")


if __name__ == "__main__":
    unittest.main()
