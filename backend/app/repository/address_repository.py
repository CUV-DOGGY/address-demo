import uuid

from app.schema.address_schema import AddressCreateResponseData


class AddressRepository:
    """地址数据访问层契约骨架。"""

    def create_address(
        self, addressdata: dict[str, object]
    ) -> AddressCreateResponseData:
        return AddressCreateResponseData(address_id=uuid.uuid4())
