import unittest
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

from bson import ObjectId
from pymongo.results import InsertOneResult

from app.repository.address_repository import AddressRepository


class AddressRepositoryTests(unittest.IsolatedAsyncioTestCase):
    async def test_sets_default_address_with_cas(self) -> None:
        collection = Mock()
        collection.update_one = AsyncMock(return_value=Mock(modified_count=1))
        database = Mock()
        database.get_collection.return_value = collection
        repository = AddressRepository(database)
        address_id = uuid4()
        user_id = uuid4()
        session = Mock()

        result = await repository.set_address_as_default(
            address_id,
            user_id,
            2,
            session,
        )

        collection.update_one.assert_awaited_once_with(
            {
                "address_id": str(address_id),
                "user_id": str(user_id),
                "status": "active",
                "is_default": False,
                "version": 2,
            },
            {
                "$set": {"is_default": True},
                "$inc": {"version": 1},
                "$currentDate": {"updated_at": True},
            },
            session=session,
        )
        self.assertTrue(result)

    async def test_clears_other_default_addresses_atomically(self) -> None:
        collection = Mock()
        collection.update_many = AsyncMock()
        database = Mock()
        database.get_collection.return_value = collection
        repository = AddressRepository(database)
        session = Mock()
        user_id = uuid4()
        except_address_id = uuid4()

        await repository.clear_other_default_addresses(
            user_id,
            session,
            except_address_id=except_address_id,
        )

        collection.update_many.assert_awaited_once_with(
            {
                "user_id": str(user_id),
                "status": "active",
                "is_default": True,
                "address_id": {"$ne": str(except_address_id)},
            },
            {
                "$set": {"is_default": False},
                "$inc": {"version": 1},
                "$currentDate": {"updated_at": True},
            },
            session=session,
        )

    async def test_create_address_inserts_document_and_returns_object_id(self) -> None:
        inserted_id = ObjectId()
        collection = Mock()
        collection.insert_one = AsyncMock(
            return_value=InsertOneResult(inserted_id, acknowledged=True)
        )
        database = Mock()
        database.get_collection.return_value = collection
        repository = AddressRepository(database)
        address_data = {"user_id": "user-1", "is_default": True}

        result = await repository.create_address(address_data)

        collection.insert_one.assert_awaited_once_with(address_data)
        self.assertEqual(result, inserted_id)


if __name__ == "__main__":
    unittest.main()
