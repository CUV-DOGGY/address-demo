import unittest
from unittest.mock import AsyncMock
from uuid import uuid4

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
    async def test_propagates_application_errors_to_global_handler(self) -> None:
        cases = (
            AddressValidationError("地址数据不正确"),
            AddressCreateError("地址创建失败"),
            AddressNotFoundError("未获取到有效地址"),
            AddressFetchError("高德地址获取失败"),
            AddressServiceUnavailableError("地址服务暂时不可用"),
            AddressServiceTimeoutError("高德服务超时"),
            AddressProviderConfigurationError("地址服务配置错误"),
        )

        for service_error in cases:
            with self.subTest(service_error=type(service_error).__name__):
                service = AsyncMock()
                service.create_address.side_effect = service_error

                with self.assertRaises(type(service_error)):
                    await create_address(make_request(), uuid4(), service)


if __name__ == "__main__":
    unittest.main()
