import unittest
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

from app.main import app
from app.repository.address_repository import AddressRepository
from app.routers.address_routers import delete_address
from app.schema.address_schema import AddressDeleteRequest, AddressDeleteResponse
from app.service.address_service import (
    AddressDataIntegrityError,
    AddressDeleteError,
    AddressGetError,
    AddressService,
    AddressVersionConflictError,
)


class AddressDeleteTests(unittest.IsolatedAsyncioTestCase):
    async def test_router_delegates_to_service(self) -> None:
        address_id = uuid4()
        request = AddressDeleteRequest(address_id=address_id)
        user_id = uuid4()
        expected_response = AddressDeleteResponse()
        service = Mock()
        service.delete_address = AsyncMock(return_value=expected_response)

        response = await delete_address(address_id, user_id, service)

        service.delete_address.assert_awaited_once_with(request, user_id)
        self.assertEqual(response, expected_response)

    def test_delete_route_uses_address_id_path_parameter(self) -> None:
        openapi = app.openapi()

        self.assertNotIn("/addresses/delete", openapi["paths"])
        operation = openapi["paths"]["/addresses/{address_id}"]["delete"]
        self.assertNotIn("requestBody", operation)
        self.assertIn(
            {
                "name": "address_id",
                "in": "path",
                "required": True,
                "schema": {
                    "type": "string",
                    "format": "uuid",
                    "title": "Address Id",
                },
            },
            operation["parameters"],
        )

    async def test_service_gets_status_and_version_before_deleting(self) -> None:
        request = AddressDeleteRequest(address_id=uuid4())
        user_id = uuid4()
        repository = Mock()
        repository.get_address_state = AsyncMock(
            return_value={"status": "active", "version": 1, "is_default": False}
        )
        repository.delete_address = AsyncMock(return_value=True)
        service = AddressService(repository, Mock(), Mock())

        response = await service.delete_address(request, user_id)

        repository.get_address_state.assert_awaited_once_with(
            request.address_id,
            user_id,
        )
        repository.delete_address.assert_awaited_once_with(
            request.address_id,
            user_id,
            1,
            expected_is_default=False,
        )
        self.assertEqual(response, AddressDeleteResponse())

    async def test_repository_soft_deletes_with_atomic_conditions(self) -> None:
        address_id = uuid4()
        user_id = uuid4()
        collection = Mock()
        collection.update_one = AsyncMock(
            return_value=Mock(modified_count=1)
        )
        database = Mock()
        database.get_collection.return_value = collection
        repository = AddressRepository(database)

        result = await repository.delete_address(address_id, user_id, 3, False)

        collection.update_one.assert_awaited_once_with(
            {
                "address_id": str(address_id),
                "user_id": str(user_id),
                "status": "active",
                "version": 3,
                "is_default": False,
            },
            {
                "$set": {"status": "deleted"},
                "$inc": {"version": 1},
                "$currentDate": {
                    "deleted_at": True,
                    "updated_at": True,
                },
            },
        )
        self.assertTrue(result)

    async def test_service_soft_deletes_default_address_without_replacement(self) -> None:
        address_id = uuid4()
        user_id = uuid4()
        repository = Mock()
        repository.get_address_state = AsyncMock(
            return_value={"status": "active", "version": 3, "is_default": True}
        )
        repository.delete_address = AsyncMock(return_value=True)
        repository.find_latest_active_address = AsyncMock()
        repository.set_address_as_default = AsyncMock()
        service = AddressService(repository, Mock(), Mock())

        result = await service.delete_address(
            AddressDeleteRequest(address_id=address_id),
            user_id,
        )

        repository.delete_address.assert_awaited_once_with(
            address_id,
            user_id,
            3,
            expected_is_default=True,
        )
        repository.find_latest_active_address.assert_not_awaited()
        repository.set_address_as_default.assert_not_awaited()
        self.assertEqual(result, AddressDeleteResponse())

    async def test_service_treats_already_deleted_address_as_success(self) -> None:
        request = AddressDeleteRequest(address_id=uuid4())
        user_id = uuid4()
        repository = Mock()
        repository.get_address_state = AsyncMock(
            return_value={"status": "deleted", "version": 2, "is_default": False}
        )
        repository.delete_address = AsyncMock()
        service = AddressService(repository, Mock(), Mock())

        response = await service.delete_address(request, user_id)

        repository.delete_address.assert_not_awaited()
        self.assertEqual(response, AddressDeleteResponse())

    async def test_service_returns_success_when_concurrent_delete_wins(self) -> None:
        request = AddressDeleteRequest(address_id=uuid4())
        user_id = uuid4()
        repository = Mock()
        repository.get_address_state = AsyncMock(
            side_effect=(
                {"status": "active", "version": 1, "is_default": False},
                {"status": "deleted", "version": 2, "is_default": False},
            )
        )
        repository.delete_address = AsyncMock(return_value=False)
        service = AddressService(repository, Mock(), Mock())

        response = await service.delete_address(request, user_id)

        self.assertEqual(repository.get_address_state.await_count, 2)
        self.assertEqual(response, AddressDeleteResponse())

    async def test_service_raises_when_version_changes_concurrently(self) -> None:
        request = AddressDeleteRequest(address_id=uuid4())
        user_id = uuid4()
        repository = Mock()
        repository.get_address_state = AsyncMock(
            side_effect=(
                {"status": "active", "version": 1, "is_default": False},
                {"status": "active", "version": 2, "is_default": False},
            )
        )
        repository.delete_address = AsyncMock(return_value=False)
        service = AddressService(repository, Mock(), Mock())

        with self.assertRaisesRegex(
            AddressVersionConflictError,
            "原地址已被修改",
        ):
            await service.delete_address(request, user_id)

    async def test_service_raises_when_update_fails_without_state_change(self) -> None:
        request = AddressDeleteRequest(address_id=uuid4())
        user_id = uuid4()
        repository = Mock()
        repository.get_address_state = AsyncMock(
            return_value={"status": "active", "version": 1, "is_default": False}
        )
        repository.delete_address = AsyncMock(return_value=False)
        service = AddressService(repository, Mock(), Mock())

        with self.assertRaisesRegex(AddressDeleteError, "地址删除失败"):
            await service.delete_address(request, user_id)

    async def test_router_propagates_delete_errors_to_global_handler(self) -> None:
        address_id = uuid4()
        user_id = uuid4()
        service_errors = (
            AddressGetError("地址不存在或无权操作"),
            AddressDataIntegrityError("地址数据异常"),
            AddressVersionConflictError("原地址已被修改"),
            AddressDeleteError("地址删除失败"),
        )

        for service_error in service_errors:
            with self.subTest(service_error=type(service_error).__name__):
                service = Mock()
                service.delete_address = AsyncMock(side_effect=service_error)

                with self.assertRaises(type(service_error)):
                    await delete_address(address_id, user_id, service)


if __name__ == "__main__":
    unittest.main()
