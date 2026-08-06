from typing import Annotated, Protocol
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.schema.address_schema import AddressCreateRequest, AddressCreateResponse


class AddressService(Protocol):
    """添加地址接口依赖的服务契约。"""

    async def create_address(self, address: AddressCreateRequest) -> UUID: ...


def get_address_service() -> AddressService:
    """地址服务依赖占位符，待服务层实现后替换。"""

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="地址服务尚未实现",
    )


AddressServiceDependency = Annotated[AddressService, Depends(get_address_service)]

router = APIRouter(prefix="/addresses", tags=["addresses"])


@router.post(
    "/add",
    response_model=AddressCreateResponse,
    status_code=status.HTTP_200_OK,
    summary="添加收货地址",
)
async def create_address(
    request: AddressCreateRequest,
    address_service: AddressServiceDependency,
) -> AddressCreateResponse:
    return await address_service.create_address(request)
