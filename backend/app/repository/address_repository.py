from typing import Literal
from uuid import UUID

from bson import ObjectId
from pymongo.asynchronous.database import AsyncDatabase


class AddressRepositoryDataError(RuntimeError):
    """地址持久化数据不符合仓储层契约。"""


class AddressRepository:
    """地址数据访问层契约骨架。"""

    def __init__(self, database: AsyncDatabase) -> None:
        self._collection = database.get_collection("addresses")

    async def create_address(
        self,
        address_data: dict[str, object],
        session: object | None = None,
    ) -> ObjectId | None:
        """原子插入一条地址记录。"""

        kwargs = {"session": session} if session is not None else {}
        result = await self._collection.insert_one(address_data, **kwargs)
        return result.inserted_id

    async def get_address(
        self,
        address_id: UUID,
        user_id: UUID,
    ) -> dict[str, object] | None:
        """按业务 UUID 获取地址，并移除 MongoDB 内部主键。"""

        return await self._collection.find_one(
            {
                "address_id": str(address_id),
                "user_id": str(user_id),
                "status": "active",
            },
            {"_id": False},
        )

    async def get_address_state(
        self,
        address_id: UUID,
        user_id: UUID,
    ) -> dict[str, object] | None:
        """获取删除流程所需的地址状态和版本，包含已删除地址。"""

        return await self._collection.find_one(
            {
                "address_id": str(address_id),
                "user_id": str(user_id),
            },
            {"_id": False, "status": True, "version": True, "is_default": True},
        )

    async def get_address_status(
        self,
        address_id: UUID,
        user_id: UUID,
    ) -> Literal["active", "deleted"] | None:
        """按业务 UUID 获取地址状态。"""

        address_status = await self._collection.find_one(
            {
                "address_id": str(address_id),
                "user_id": str(user_id),
            },
            {"_id": False, "status": True},
        )
        if address_status is None:
            return None

        status = address_status.get("status")
        if status in {"active", "deleted"}:
            return status
        raise AddressRepositoryDataError("地址状态字段异常")

    async def update_address(
        self,
        address_id: UUID,
        user_id: UUID,
        expected_version: int,
        expected_is_default: bool,
        update_data: dict[str, object],
        session: object | None = None,
    ) -> bool:
        """按版本原子部分更新一条 active 地址。"""

        kwargs = {"session": session} if session is not None else {}
        result = await self._collection.update_one(
            self._active_address_filter(
                address_id,
                user_id,
                expected_version,
                expected_is_default,
            ),
            self._address_update_document(update_data),
            **kwargs,
        )
        return result.modified_count == 1

    async def delete_address(
        self,
        address_id: UUID,
        user_id: UUID,
        expected_version: int,
        expected_is_default: bool,
        session: object | None = None,
    ) -> bool:
        """按地址状态和版本原子软删除单个地址。"""

        kwargs = {"session": session} if session is not None else {}
        result = await self._collection.update_one(
            self._active_address_filter(
                address_id,
                user_id,
                expected_version,
                expected_is_default,
            ),
            {
                "$set": {"status": "deleted"},
                "$inc": {"version": 1},
                "$currentDate": {
                    "deleted_at": True,
                    "updated_at": True,
                },
            },
            **kwargs,
        )
        return result.modified_count == 1

    async def set_address_as_default(
        self,
        address_id: UUID,
        user_id: UUID,
        expected_version: int,
        session: object,
    ) -> bool:
        """在事务中按版本将 active 地址设为默认地址。"""

        result = await self._collection.update_one(
            {
                "address_id": str(address_id),
                "user_id": str(user_id),
                "status": "active",
                "is_default": False,
                "version": expected_version,
            },
            {
                "$set": {"is_default": True},
                "$inc": {"version": 1},
                "$currentDate": {"updated_at": True},
            },
            session=session,
        )
        return result.modified_count == 1

    @staticmethod
    def _active_address_filter(
        address_id: UUID,
        user_id: UUID,
        expected_version: int,
        expected_is_default: bool,
    ) -> dict[str, object]:
        return {
            "address_id": str(address_id),
            "user_id": str(user_id),
            "status": "active",
            "version": expected_version,
            "is_default": expected_is_default,
        }

    @staticmethod
    def _address_update_document(update_data: dict[str, object]) -> dict[str, object]:
        return {
            "$set": update_data,
            "$inc": {"version": 1},
            "$currentDate": {"updated_at": True},
        }

    async def clear_other_default_addresses(
        self,
        user_id: UUID,
        session: object | None = None,
        except_address_id: UUID | None = None,
    ) -> None:
        """取消同一用户其他 active 默认地址，可选用已有事务。"""
        filters: dict[str, object] = {
            "user_id": str(user_id),
            "status": "active",
            "is_default": True,
        }
        if except_address_id is not None:
            filters["address_id"] = {"$ne": str(except_address_id)}

        update_document = {
            "$set": {"is_default": False},
            "$inc": {"version": 1},
            "$currentDate": {"updated_at": True},
        }
        if session is None:
            await self._collection.update_many(filters, update_document)
            return

        await self._collection.update_many(
            filters,
            update_document,
            session=session,
        )
