import unittest
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

from pydantic import ValidationError

from app.schema.address_schema import AddressUpdateRequest, AddressUpdateResponseData
from app.service.address_service import AddressService


class AddressUpdateSchemaTests(unittest.TestCase):
    def test_accepts_display_address(self) -> None:
        request = AddressUpdateRequest.model_validate(
            {
                "address_id": str(uuid4()),
                "display_address": "  公司前台  ",
            }
        )

        self.assertEqual(request.display_address, "公司前台")

    def test_rejects_shipping_address_alias(self) -> None:
        with self.assertRaises(ValidationError):
            AddressUpdateRequest.model_validate(
                {
                    "address_id": str(uuid4()),
                    "shipping_address": "公司前台",
                }
            )

    def test_response_includes_display_address(self) -> None:
        response_data = AddressUpdateResponseData(
            address_id=uuid4(),
            display_address="公司前台",
        )

        self.assertEqual(response_data.display_address, "公司前台")


class AddressUpdateServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_persists_and_returns_display_address(self) -> None:
        address_id = uuid4()
        user_id = uuid4()
        repository = Mock()
        repository.get_address_state = AsyncMock(
            return_value={"status": "active", "version": 2, "is_default": False}
        )
        repository.update_address = AsyncMock(return_value=True)
        service = AddressService(repository, Mock(), Mock())
        request = AddressUpdateRequest(
            address_id=address_id,
            display_address="公司前台",
        )

        response = await service.update_address(request, user_id)

        repository.update_address.assert_awaited_once_with(
            address_id,
            user_id,
            2,
            False,
            {"display_address": "公司前台"},
        )
        self.assertEqual(response.data.display_address, "公司前台")


if __name__ == "__main__":
    unittest.main()
