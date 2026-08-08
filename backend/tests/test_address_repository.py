import unittest
from unittest.mock import AsyncMock, Mock

from bson import ObjectId
from pymongo.results import InsertOneResult

from app.repository.address_repository import AddressRepository


class AddressRepositoryTests(unittest.IsolatedAsyncioTestCase):
    async def test_create_address_inserts_document_and_returns_object_id(self) -> None:
        inserted_id = ObjectId()
        collection = Mock()
        collection.insert_one = AsyncMock(
            return_value=InsertOneResult(inserted_id, acknowledged=True)
        )
        database = Mock()
        database.get_collection.return_value = collection
        repository = AddressRepository(database)
        address_data = {"receiver_name": "张三"}

        result = await repository.create_address(address_data)

        collection.insert_one.assert_awaited_once_with(address_data)
        self.assertEqual(result, inserted_id)


if __name__ == "__main__":
    unittest.main()
