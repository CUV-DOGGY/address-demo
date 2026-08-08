from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.core.depedencies import AddressServiceDependency
from app.schema.address_schema import (
    Address,
    AddressCreateRequest,
    AddressCreateResponse,
    AddressDeleteRequest,
    AddressDeleteResponse,
)
from app.service.address_service import (
    AddressCreateError,
    AddressGetError,
    AddressValidationError,
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
    address_service: AddressServiceDependency,
) -> Address:
    try:
        return await address_service.get_address(address_id)
    except AddressGetError as exc:
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
    address_service: AddressServiceDependency,
) -> AddressCreateResponse:
    try:
        address_create_id = await address_service.create_address(request)
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


@router.delete(
    "/delete",
    response_model=AddressDeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="删除收货地址",
)
async def delete_address(
    request: AddressDeleteRequest,
    address_service: AddressServiceDependency,
) -> AddressDeleteResponse:
    return await address_service.delete_address(request)
