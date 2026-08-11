import unittest
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import httpx

from app.amap.client import AmapClient
from app.amap.exceptions import (
    AmapAddressFetchError,
    AmapAddressNotFoundError,
    AmapConfigurationError,
    AmapServiceTimeoutError,
    AmapServiceUnavailableError,
)
from app.schema.address_schema import AddressCreateRequest
from app.service.address_service import (
    AddressFetchError,
    AddressNotFoundError,
    AddressProviderConfigurationError,
    AddressService,
    AddressServiceTimeoutError,
    AddressServiceUnavailableError,
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


class AmapClientExceptionTests(unittest.IsolatedAsyncioTestCase):
    async def test_converts_http_timeout(self) -> None:
        http_client = Mock()
        http_client.get = AsyncMock(side_effect=httpx.ReadTimeout("timed out"))
        client = AmapClient(http_client)

        with self.assertRaises(AmapServiceTimeoutError):
            await client.get_poi_detail("B0XXXXXX")

    async def test_rejects_unknown_failed_amap_response(self) -> None:
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "status": "0",
            "info": "UNKNOWN_ERROR",
            "infocode": "20003",
        }
        http_client = Mock()
        http_client.get = AsyncMock(return_value=response)
        client = AmapClient(http_client)

        with self.assertRaises(AmapAddressFetchError):
            await client.get_poi_detail("B0XXXXXX")

    async def test_converts_invalid_key_to_configuration_error(self) -> None:
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "status": "0",
            "info": "INVALID_USER_KEY",
            "infocode": "10001",
        }
        http_client = Mock()
        http_client.get = AsyncMock(return_value=response)
        client = AmapClient(http_client)

        with self.assertRaises(AmapConfigurationError):
            await client.get_poi_detail("B0XXXXXX")

    async def test_converts_quota_error_to_unavailable_error(self) -> None:
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "status": "0",
            "info": "USER_DAILY_QUERY_OVER_LIMIT",
            "infocode": "10044",
        }
        http_client = Mock()
        http_client.get = AsyncMock(return_value=response)
        client = AmapClient(http_client)

        with self.assertRaises(AmapServiceUnavailableError):
            await client.get_poi_detail("B0XXXXXX")

    async def test_converts_http_rate_limit_to_unavailable_error(self) -> None:
        request = httpx.Request("GET", "https://restapi.amap.com/test")
        response = httpx.Response(429, request=request)
        http_client = Mock()
        http_client.get = AsyncMock(return_value=response)
        client = AmapClient(http_client)

        with self.assertRaises(AmapServiceUnavailableError):
            await client.get_poi_detail("B0XXXXXX")

    async def test_converts_empty_poi_result_to_not_found_error(self) -> None:
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {"status": "1", "pois": []}
        http_client = Mock()
        http_client.get = AsyncMock(return_value=response)
        client = AmapClient(http_client)

        with self.assertRaises(AmapAddressNotFoundError):
            await client.get_poi_detail("B0XXXXXX")


class AddressServiceAmapExceptionTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.repository = Mock()
        self.validation = Mock()
        self.validation.address_validation = AsyncMock()
        self.service = AddressService(self.repository, self.validation, Mock())

    async def test_converts_amap_address_fetch_error(self) -> None:
        self.validation.address_validation.side_effect = AmapAddressFetchError()

        with self.assertRaisesRegex(AddressFetchError, "高德地址获取失败"):
            await self.service.create_address(make_request(), uuid4())

        self.repository.create_address.assert_not_called()

    async def test_converts_amap_timeout_error(self) -> None:
        self.validation.address_validation.side_effect = AmapServiceTimeoutError()

        with self.assertRaisesRegex(AddressServiceTimeoutError, "高德服务超时"):
            await self.service.create_address(make_request(), uuid4())

        self.repository.create_address.assert_not_called()

    async def test_converts_amap_not_found_error(self) -> None:
        self.validation.address_validation.side_effect = AmapAddressNotFoundError()

        with self.assertRaisesRegex(AddressNotFoundError, "未获取到有效地址"):
            await self.service.create_address(make_request(), uuid4())

        self.repository.create_address.assert_not_called()

    async def test_converts_amap_configuration_error(self) -> None:
        self.validation.address_validation.side_effect = AmapConfigurationError()

        with self.assertRaisesRegex(
            AddressProviderConfigurationError, "地址服务配置错误"
        ):
            await self.service.create_address(make_request(), uuid4())

        self.repository.create_address.assert_not_called()

    async def test_converts_amap_unavailable_error(self) -> None:
        self.validation.address_validation.side_effect = AmapServiceUnavailableError()

        with self.assertRaisesRegex(
            AddressServiceUnavailableError, "地址服务暂时不可用"
        ):
            await self.service.create_address(make_request(), uuid4())

        self.repository.create_address.assert_not_called()


if __name__ == "__main__":
    unittest.main()
