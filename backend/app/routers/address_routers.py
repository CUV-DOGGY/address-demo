from fastapi import APIRouter, HTTPException, status

from app.core.depedencies import AddressServiceDependency
from app.schema.address_schema import (
    AddressCreateRequest,
    AddressCreateResponse,
    AddressDeleteRequest,
    AddressDeleteResponse,
)
from app.service.address_service import (
    AddressCreateError,
    AddressValidationError,
)

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
