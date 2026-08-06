from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status

from app.repository.address_repository import (
    AddressRepository,
)
from app.schema.address_schema import AddressCreateRequest, AddressCreateResponse


class AddressService:
    """地址业务服务骨架。"""

    def __init__(self, repository: AddressRepository) -> None:
        self._repository = repository

    async def create_address(
        self,
        request: AddressCreateRequest,
        user_id: UUID,
    ) -> AddressCreateResponse:
        """校验并创建用户的收货地址。"""

        # TODO: 向高德地图发起地址编码请求。
        # TODO: 对比高德返回坐标与 request.coordinate 是否一致，不一致时抛出业务异常。
        # TODO: 生成包含联系人、地址和坐标的完整收货信息快照。
        # TODO: 当 request.is_default 为 True 时，取消该用户的其他默认地址。
        # TODO: 通过 AddressRepository 持久化地址并返回 AddressCreateResponse。
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="添加地址服务尚未实现",
        )
