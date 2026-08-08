from uuid import UUID

from bson import ObjectId
from pymongo.asynchronous.database import AsyncDatabase


class AddressRepository:
    """地址数据访问层契约骨架。"""

    def __init__(self, database: AsyncDatabase) -> None:
        self._collection = database.get_collection("addresses")

    async def create_address(self, address_data: dict[str, object]) -> ObjectId | None:
        result = await self._collection.insert_one(address_data)

        return result.inserted_id

    async def delete_address(self, address_id: UUID) -> None:
        """按业务 UUID 删除地址记录。"""

        await self._collection.delete_one(
            {"address_id": str(address_id)},
            hint="uniq_address_id",
        )
