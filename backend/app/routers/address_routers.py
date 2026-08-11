from typing import Literal
from uuid import UUID

from fastapi import APIRouter, status

from app.core.depedencies import AddressServiceDependency, UserIdDependency
from app.schema.address_schema import (
    Address,
    AddressCreateRequest,
    AddressCreateResponse,
    AddressDeleteRequest,
    AddressDeleteResponse,
    AddressUpdateRequest,
    AddressUpdateResponse,
)


router = APIRouter(prefix="/addresses", tags=["addresses"])


@router.get(
    "/get",
    response_model=Address,
    status_code=status.HTTP_200_OK,
    summary="获取收货地址",
)
async def get_address(
    address_id: UUID,
    user_id: UserIdDependency,
    address_service: AddressServiceDependency,
) -> Address:
    return await address_service.get_address(address_id, user_id)


@router.get(
    "/status",
    response_model=Literal["active", "deleted"],
    status_code=status.HTTP_200_OK,
    summary="获取收货地址状态",
)
async def get_address_status(
    address_id: UUID,
    user_id: UserIdDependency,
    address_service: AddressServiceDependency,
) -> Literal["active", "deleted"]:
    return await address_service.get_address_status(address_id, user_id)


@router.post(
    "/add",
    response_model=AddressCreateResponse,
    status_code=status.HTTP_200_OK,
    summary="添加收货地址",
)
async def create_address(
    request: AddressCreateRequest,
    user_id: UserIdDependency,
    address_service: AddressServiceDependency,
) -> AddressCreateResponse:
    address_create_id = await address_service.create_address(request, user_id)
    return AddressCreateResponse(data=address_create_id)


@router.patch(
    "/update",
    response_model=AddressUpdateResponse,
    response_model_exclude_none=True,
    status_code=status.HTTP_200_OK,
    summary="部分更新收货地址",
)
async def update_address(
    request: AddressUpdateRequest,
    user_id: UserIdDependency,
    address_service: AddressServiceDependency,
) -> AddressUpdateResponse:
    return await address_service.update_address(request, user_id)


@router.delete(
    "/{address_id}",
    response_model=AddressDeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="删除收货地址",
)
async def delete_address(
    address_id: UUID,
    user_id: UserIdDependency,
    address_service: AddressServiceDependency,
) -> AddressDeleteResponse:
    request = AddressDeleteRequest(address_id=address_id)
    return await address_service.delete_address(request, user_id)
