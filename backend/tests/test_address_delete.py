import unittest
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

from app.repository.address_repository import AddressRepository
from app.routers.address_routers import delete_address
from app.schema.address_schema import AddressDeleteRequest, AddressDeleteResponse
from app.service.address_service import AddressService


class AddressDeleteTests(unittest.IsolatedAsyncioTestCase):
    async def test_router_delegates_to_service(self) -> None:
        request = AddressDeleteRequest(address_id=uuid4())
        expected_response = AddressDeleteResponse()
        service = Mock()
        service.delete_address = AsyncMock(return_value=expected_response)

        response = await delete_address(request, service)

        service.delete_address.assert_awaited_once_with(request)
        self.assertEqual(response, expected_response)

    async def test_service_delegates_to_repository_without_business_rules(self) -> None:
        request = AddressDeleteRequest(address_id=uuid4())
        repository = Mock()
        repository.delete_address = AsyncMock()
        service = AddressService(repository, Mock())

        response = await service.delete_address(request)

        repository.delete_address.assert_awaited_once_with(request.address_id)
        self.assertEqual(response, AddressDeleteResponse())

    async def test_repository_deletes_by_string_address_id(self) -> None:
        address_id = uuid4()
        collection = Mock()
        collection.delete_one = AsyncMock()
        database = Mock()
        database.get_collection.return_value = collection
        repository = AddressRepository(database)

        await repository.delete_address(address_id)

        collection.delete_one.assert_awaited_once_with(
            {"address_id": str(address_id)},
            hint="uniq_address_id",
        )


if __name__ == "__main__":
    unittest.main()
