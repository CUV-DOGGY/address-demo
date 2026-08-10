import unittest
from unittest.mock import AsyncMock
from uuid import uuid4

from fastapi import HTTPException

from app.routers.address_routers import create_address
from app.schema.address_schema import AddressCreateRequest
from app.service.address_service import (
    AddressCreateError,
    AddressFetchError,
    AddressNotFoundError,
    AddressProviderConfigurationError,
    AddressServiceTimeoutError,
    AddressServiceUnavailableError,
    AddressValidationError,
)


def make_request() -> AddressCreateRequest:
    return AddressCreateRequest.model_validate(
        {
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
        }
    )


class AddressRouterExceptionTests(unittest.IsolatedAsyncioTestCase):
    async def test_maps_route_owned_errors_to_http_status_codes(self) -> None:
        cases = (
            (AddressValidationError("地址数据不正确"), 422),
            (AddressCreateError("地址创建失败"), 500),
        )

        for service_error, expected_status in cases:
            with self.subTest(service_error=type(service_error).__name__):
                service = AsyncMock()
                service.create_address.side_effect = service_error

                with self.assertRaises(HTTPException) as context:
                    await create_address(make_request(), uuid4(), service)

                self.assertEqual(context.exception.status_code, expected_status)
                self.assertEqual(context.exception.detail, str(service_error))

    async def test_does_not_catch_address_provider_errors(self) -> None:
        provider_errors = (
            AddressNotFoundError("未获取到有效地址"),
            AddressFetchError("高德地址获取失败"),
            AddressServiceUnavailableError("地址服务暂时不可用"),
            AddressServiceTimeoutError("高德服务超时"),
            AddressProviderConfigurationError("地址服务配置错误"),
        )

        for service_error in provider_errors:
            with self.subTest(service_error=type(service_error).__name__):
                service = AsyncMock()
                service.create_address.side_effect = service_error

                with self.assertRaises(type(service_error)):
                    await create_address(make_request(), uuid4(), service)


if __name__ == "__main__":
    unittest.main()
