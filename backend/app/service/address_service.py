from uuid import UUID

from fastapi import HTTPException, status

from app.repository.address_repository import AddressRepository
from app.schema.address_schema import (
    AddressCreateRequest,
    AddressCreateResponse,
    AddressValidData,
)
from app.service.address_validation import AddressValidation


class AddressService:
    """地址业务服务骨架。"""

    def __init__(
        self, repository: AddressRepository, addressvalidation: AddressValidation
    ) -> None:
        self._repository = repository
        self._addressvalidation = addressvalidation

    async def create_address(
        self,
        request: AddressCreateRequest,
        user_id: UUID,
    ) -> AddressCreateResponse:
        """校验并创建用户的收货地址。"""

        validation_data = AddressValidData(
            shipping_address=request.shipping_address,
            detail_address=request.detail_address,
            location=request.location,
        )
        resolved_location, validation_status = (
            await self._addressvalidation.address_validation(validation_data)
        )
        if not validation_status:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="地址校验失败",
            )

        address_data = {
            "receiver_name": request.receiver_name,
            "phone_number": request.phone_number,
            "shipping_address": request.shipping_address,
            "detail_address": request.detail_address,
            "location": request.location.model_dump(),
            "is_default": request.is_default,
            "formatted_address": resolved_location.formatted_address,
            "adcode": resolved_location.adcode,
        }
        response_data = self._repository.create_address(address_data)
        return AddressCreateResponse(data=response_data)
