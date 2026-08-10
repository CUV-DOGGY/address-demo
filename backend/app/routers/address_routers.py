from typing import Literal
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

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
from app.service.address_service import (
    AddressCreateError,
    AddressDataIntegrityError,
    AddressDeleteError,
    AddressGetError,
    AddressStatusGetError,
    AddressStateConflictError,
    AddressUpdateError,
    AddressValidationError,
    AddressVersionConflictError,
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
    try:
        return await address_service.get_address(address_id, user_id)
    except AddressGetError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


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
    try:
        return await address_service.get_address_status(address_id, user_id)
    except AddressStatusGetError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


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
    try:
        address_create_id = await address_service.create_address(request, user_id)
    except AddressValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc
    except AddressCreateError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    return AddressCreateResponse(data=address_create_id)


@router.patch(
    "/update",
    response_model=AddressUpdateResponse,
    status_code=status.HTTP_200_OK,
    summary="部分更新收货地址",
)
async def update_address(
    request: AddressUpdateRequest,
    user_id: UserIdDependency,
    address_service: AddressServiceDependency,
) -> AddressUpdateResponse:
    try:
        return await address_service.update_address(request, user_id)
    except AddressGetError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except (AddressStateConflictError, AddressVersionConflictError) as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except (AddressDataIntegrityError, AddressUpdateError) as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@router.delete(
    "/delete",
    response_model=AddressDeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="删除收货地址",
)
async def delete_address(
    request: AddressDeleteRequest,
    user_id: UserIdDependency,
    address_service: AddressServiceDependency,
) -> AddressDeleteResponse:
    try:
        return await address_service.delete_address(request, user_id)
    except AddressGetError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except AddressDataIntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
    except AddressVersionConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except AddressDeleteError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
