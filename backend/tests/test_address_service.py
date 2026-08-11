import unittest
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

from bson import ObjectId

from app.amap.models import AmapResolvedLocation
from app.schema.address_schema import (
    AddressCreateRequest,
    AddressCreateResponseData,
)
from app.service.address_service import (
    AddressCreateError,
    AddressService,
    AddressValidationError,
)
from app.service.address_validation import AddressAcodeError


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
        self.repository.create_address = AsyncMock()
        self.repository.clear_other_default_addresses = AsyncMock()
        self.database = Mock()
        self.session = Mock()

        @asynccontextmanager
        async def session_context():
            yield self.session

        async def run_in_transaction(operation: object) -> object:
            return await operation(self.session)

        self.database.client.start_session = Mock(return_value=session_context())
        self.session.with_transaction = AsyncMock(side_effect=run_in_transaction)
        self.service = AddressService(
            self.repository,
            self.address_validation,
            self.database,
        )

    async def test_create_address_validates_saves_snapshot_and_returns_response(
        self,
    ) -> None:
        request = make_request()
        resolved_location = make_resolved_location()
        address_id = uuid4()
        user_id = uuid4()
        updated_at = datetime(2026, 8, 9, tzinfo=timezone.utc)
        self.address_validation.address_validation.return_value = resolved_location
        self.repository.create_address.return_value = ObjectId()

        with (
            patch("app.service.address_service.uuid4", return_value=address_id),
            patch("app.service.address_service.datetime") as datetime_mock,
        ):
            datetime_mock.now.return_value = updated_at
            response = await self.service.create_address(request, user_id)

        self.address_validation.address_validation.assert_awaited_once_with(
            request.location
        )
        self.repository.clear_other_default_addresses.assert_awaited_once_with(
            user_id,
            self.session,
        )
        self.repository.create_address.assert_awaited_once_with(
            {
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
                "created_at": updated_at,
                "updated_at": updated_at,
            },
            session=self.session,
        )
        self.assertIsInstance(response, AddressCreateResponseData)
        self.assertEqual(response.address_id, address_id)

    async def test_create_address_rejects_invalid_address_without_saving(
        self,
    ) -> None:
        self.address_validation.address_validation.side_effect = AddressAcodeError(
            "地址的行政编码错误"
        )

        with self.assertRaisesRegex(AddressValidationError, "地址数据不正确"):
            await self.service.create_address(make_request(), uuid4())

        self.repository.create_address.assert_not_called()

    async def test_create_address_raises_when_repository_returns_none(self) -> None:
        self.address_validation.address_validation.return_value = (
            make_resolved_location()
        )
        self.repository.create_address.return_value = None

        with self.assertRaisesRegex(AddressCreateError, "地址创建失败"):
            await self.service.create_address(make_request(), uuid4())


if __name__ == "__main__":
    unittest.main()
