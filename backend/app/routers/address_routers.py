from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.schema.address_schema import AddressCreateRequest, AddressCreateResponse
from app.service.address_service import AddressService, get_address_service
from app.repository.address_repository import AddressRepository


def get_user_id() -> UUID:
    """临时返回固定用户 ID，接入认证后替换。"""

    return UUID("7c2c3dc3-2577-4d85-b6a8-03f3d8c21d83")


def get_address_service(
    repository: AddressRepositoryDependency,
) -> AddressService:
    """通过依赖注入创建地址服务。"""

    return AddressService(repository)


def get_address_repository() -> AddressRepository:
    """提供地址数据访问层实例，待数据库接入后替换具体实现。"""

    return AddressRepository()


AddressRepositoryDependency = Annotated[
    AddressRepository, Depends(get_address_repository)
]
AddressServiceDependency = Annotated[AddressService, Depends(get_address_service)]
UserIdDependency = Annotated[UUID, Depends(get_user_id)]


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
    user_id: UserIdDependency,
) -> AddressCreateResponse:
    return await address_service.create_address(request, user_id)
