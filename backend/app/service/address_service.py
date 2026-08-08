from uuid import uuid4

from app.amap.exceptions import (
    AmapAddressFetchError,
    AmapAddressNotFoundError,
    AmapConfigurationError,
    AmapServiceTimeoutError,
    AmapServiceUnavailableError,
)
from app.repository.address_repository import AddressRepository
from app.schema.address_schema import (
    AddressCreateRequest,
    AddressCreateResponseData,
    AddressDeleteRequest,
    AddressDeleteResponse,
    AddressValidData,
)
from app.service.address_validation import (
    AddressValidation,
    AddressLocationError,
    AddressAcodeError,
)


class AddressCreateError(RuntimeError):
    """地址创建失败"""


class AddressValidationError(RuntimeError):
    """地址数据不正确"""


class AddressProviderError(RuntimeError):
    """地址供应商服务异常基类。"""


class AddressFetchError(AddressProviderError):
    """高德地址获取失败"""


class AddressNotFoundError(AddressProviderError):
    """未获取到有效地址"""


class AddressProviderConfigurationError(AddressProviderError):
    """地址服务配置错误"""


class AddressServiceUnavailableError(AddressProviderError):
    """地址服务暂时不可用"""


class AddressServiceTimeoutError(AddressProviderError):
    """高德服务超时"""


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
    ) -> AddressCreateResponseData:
        """校验并创建用户的收货地址。"""

        validation_data = AddressValidData(
            shipping_address=request.shipping_address,
            detail_address=request.detail_address,
            location=request.location,
        )
        try:
            resolved_location = await self._addressvalidation.address_validation(
                validation_data
            )
        except (AddressLocationError, AddressAcodeError) as exc:
            raise AddressValidationError("地址数据不正确") from exc
        except AmapServiceTimeoutError as exc:
            raise AddressServiceTimeoutError("高德服务超时") from exc
        except AmapServiceUnavailableError as exc:
            raise AddressServiceUnavailableError("地址服务暂时不可用") from exc
        except AmapConfigurationError as exc:
            raise AddressProviderConfigurationError("地址服务配置错误") from exc
        except AmapAddressNotFoundError as exc:
            raise AddressNotFoundError("未获取到有效地址") from exc
        except AmapAddressFetchError as exc:
            raise AddressFetchError("高德地址获取失败") from exc

        address_id = uuid4()
        address_data = {
            "address_id": str(address_id),
            "receiver_name": request.receiver_name,
            "phone_number": request.phone_number,
            "shipping_address": request.shipping_address,
            "detail_address": request.detail_address,
            "location": request.location.model_dump(),
            "is_default": request.is_default,
            "formatted_address": resolved_location.formatted_address,
            "adcode": resolved_location.adcode,
        }
        address_create_id = await self._repository.create_address(address_data)
        if address_create_id is None:
            raise AddressCreateError("地址创建失败")

        return AddressCreateResponseData(address_id=address_id)

    async def delete_address(
        self,
        request: AddressDeleteRequest,
    ) -> AddressDeleteResponse:
        """删除地址服务。"""

        await self._repository.delete_address(request.address_id)
        return AddressDeleteResponse()
