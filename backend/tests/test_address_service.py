import unittest
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

from fastapi import HTTPException

from app.amap.models import AmapResolvedLocation
from app.schema.address_schema import (
    AddressCreateRequest,
    AddressCreateResponseData,
    AddressValidData,
)
from app.service.address_service import AddressService


def make_request() -> AddressCreateRequest:
    return AddressCreateRequest.model_validate(
        {
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
        }
    )


def make_resolved_location() -> AmapResolvedLocation:
    return AmapResolvedLocation(
        formatted_address="广东省深圳市南山区高新南一道",
        adcode="440305",
        location="113.934528,22.540503",
        poi_id="B0XXXXXX",
    )


class AddressServiceTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.repository = Mock()
        self.address_validation = Mock()
        self.address_validation.address_validation = AsyncMock()
        self.service = AddressService(self.repository, self.address_validation)
        self.user_id = uuid4()

    async def test_create_address_validates_saves_snapshot_and_returns_response(
        self,
    ) -> None:
        request = make_request()
        resolved_location = make_resolved_location()
        address_id = uuid4()
        self.address_validation.address_validation.return_value = (
            resolved_location,
            True,
        )
        self.repository.create_address.return_value = AddressCreateResponseData(
            address_id=address_id
        )

        response = await self.service.create_address(request, self.user_id)

        validation_data = self.address_validation.address_validation.call_args.args[0]
        self.assertIsInstance(validation_data, AddressValidData)
        self.assertEqual(validation_data.shipping_address, request.shipping_address)
        self.assertEqual(validation_data.detail_address, request.detail_address)
        self.assertEqual(validation_data.location, request.location)
        self.repository.create_address.assert_called_once_with(
            {
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
                "formatted_address": "广东省深圳市南山区高新南一道",
                "adcode": "440305",
            }
        )
        self.assertEqual(response.data.address_id, address_id)
        self.assertEqual(response.code, 200)

    async def test_create_address_rejects_invalid_address_without_saving(
        self,
    ) -> None:
        self.address_validation.address_validation.return_value = (
            make_resolved_location(),
            False,
        )

        with self.assertRaises(HTTPException) as context:
            await self.service.create_address(make_request(), self.user_id)

        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(context.exception.detail, "地址校验失败")
        self.repository.create_address.assert_not_called()


if __name__ == "__main__":
    unittest.main()
