from fastapi import APIRouter, status
from app.schema.address_schema import AddressCreateRequest, AddressCreateResponse
from app.core.depedencies import AddressServiceDependency, UserIdDependency

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
