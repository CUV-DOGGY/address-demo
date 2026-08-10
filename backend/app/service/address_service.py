from datetime import datetime, timezone
from typing import Literal
from uuid import UUID, uuid4

from app.amap.exceptions import (
    AmapAddressFetchError,
    AmapAddressNotFoundError,
    AmapConfigurationError,
    AmapServiceTimeoutError,
    AmapServiceUnavailableError,
)
from app.repository.address_repository import AddressRepository
from pymongo.asynchronous.database import AsyncDatabase
from app.schema.address_schema import (
    Address,
    AddressCreateRequest,
    AddressCreateResponseData,
    AddressDeleteRequest,
    AddressDeleteResponse,
    AddressUpdateRequest,
    AddressUpdateResponse,
    AddressUpdateResponseData,
    AddressValidData,
)
from app.service.address_validation import (
    AddressValidation,
    AddressLocationError,
    AddressAcodeError,
)


class AddressCreateError(RuntimeError):
    """地址创建失败"""


class AddressGetError(RuntimeError):
    """获取地址信息失败。"""


class AddressStatusGetError(RuntimeError):
    """获取地址状态失败。"""


class AddressDataIntegrityError(RuntimeError):
    """地址持久化数据不符合预期。"""


class AddressVersionConflictError(RuntimeError):
    """地址版本已发生变化。"""


class AddressDeleteError(RuntimeError):
    """地址删除失败。"""


class AddressUpdateError(RuntimeError):
    """地址更新失败。"""


class AddressStateConflictError(RuntimeError):
    """地址当前状态不允许执行操作。"""


class _AddressDefaultTransactionAborted(Exception):
    """中止默认地址切换事务。"""


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
        self,
        repository: AddressRepository,
        addressvalidation: AddressValidation,
        database: AsyncDatabase,
    ) -> None:
        self._repository = repository
        self._addressvalidation = addressvalidation
        self._database = database

    async def create_address(
        self,
        request: AddressCreateRequest,
        user_id: UUID,
    ) -> AddressCreateResponseData:
        """校验并创建用户的收货地址。"""

        validation_data = AddressValidData(
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
        now = datetime.now(timezone.utc)
        address_data = {
            "address_id": str(address_id),
            "user_id": str(user_id),
            "receiver_name": request.receiver_name,
            "phone_number": request.phone_number,
            "display_address": request.display_address,
            "detail_address": request.detail_address,
            "location": request.location.model_dump(),
            "is_default": request.is_default,
            "status": "active",
            "version": 1,
            "canonical_address": resolved_location.formatted_address,
            "deleted_at": None,
            "created_at": now,
            "updated_at": now,
        }
        if request.is_default:
            address_create_id = await self._create_default_address(
                address_data,
                user_id,
            )
        else:
            address_create_id = await self._repository.create_address(address_data)
        if address_create_id is None:
            raise AddressCreateError("地址创建失败")

        return AddressCreateResponseData(address_id=address_id)

    async def get_address(self, address_id: UUID, user_id: UUID) -> Address:
        """获取一条有效地址信息。"""

        address_data = await self._repository.get_address(address_id, user_id)
        if address_data is None:
            raise AddressGetError("地址不存在")
        return Address.model_validate(address_data)

    async def get_address_status(
        self,
        address_id: UUID,
        user_id: UUID,
    ) -> Literal["active", "deleted"]:
        """获取一条地址的状态。"""

        address_status = await self._repository.get_address_status(address_id, user_id)
        if address_status is None:
            raise AddressStatusGetError("获取地址状态失败")

        return address_status

    async def get_address_status_and_version_and_is_default(
        self,
        address_id: UUID,
        user_id: UUID,
    ) -> tuple[str, int, bool]:
        """获取删除业务所需的地址状态和版本号。"""

        address_data = await self._repository.get_address_state(address_id, user_id)
        if address_data is None:
            raise AddressGetError("地址不存在")

        address_status = address_data.get("status")
        address_version = address_data.get("version")
        is_default = address_data.get("is_default")
        if (
            address_status not in {"active", "deleted"}
            or not isinstance(address_version, int)
            or isinstance(address_version, bool)
            or not isinstance(is_default, bool)
        ):
            raise AddressDataIntegrityError("地址数据异常")

        return address_status, address_version, is_default

    async def delete_address(
        self,
        request: AddressDeleteRequest,
        user_id: UUID,
    ) -> AddressDeleteResponse:
        """删除地址服务。"""

        (
            address_status,
            address_version,
            is_default,
        ) = await self.get_address_status_and_version_and_is_default(
            request.address_id, user_id
        )
        if address_status == "deleted":
            return AddressDeleteResponse()

        delete_succeeded = await self._repository.delete_address(
            request.address_id,
            user_id,
            address_version,
            expected_is_default=is_default,
        )
        if not delete_succeeded:
            (
                current_status,
                current_version,
                _,
            ) = await self.get_address_status_and_version(request.address_id, user_id)
            if current_status == "deleted":
                return AddressDeleteResponse()
            if current_version != address_version:
                raise AddressVersionConflictError("原地址已被修改")
            raise AddressDeleteError("地址删除失败")
        return AddressDeleteResponse()

    async def clear_other_default_addresses(
        self,
        user_id: UUID,
        except_address_id: UUID | None = None,
    ) -> None:
        """清除默认地址。"""
        return await self._repository.clear_other_default_addresses(
            user_id,
            except_address_id=except_address_id,
        )

    async def _create_default_address(
        self,
        address_data: dict[str, object],
        user_id: UUID,
    ) -> object | None:
        """在事务中取消旧默认地址并创建新的默认地址。"""

        async def operation(session: object) -> object:
            await self._repository.clear_other_default_addresses(user_id, session)
            created_address_id = await self._repository.create_address(
                address_data,
                session=session,
            )
            if created_address_id is None:
                raise _AddressDefaultTransactionAborted
            return created_address_id

        try:
            async with self._database.client.start_session() as session:
                return await session.with_transaction(operation)
        except _AddressDefaultTransactionAborted:
            return None

    async def _set_default_address(
        self,
        address_id: UUID,
        user_id: UUID,
        update_data: dict[str, object],
    ) -> bool:
        """在事务中取消旧默认地址并原子地设定新的默认地址。"""

        (
            _,
            address_version,
            _,
        ) = await self.get_address_status_and_version_and_is_default(
            address_id,
            user_id,
        )

        async def operation(session: object) -> bool:
            await self._repository.clear_other_default_addresses(
                user_id,
                session,
                except_address_id=address_id,
            )
            is_set = await self._repository.set_address_as_default(
                address_id,
                user_id,
                address_version,
                session,
            )
            if not is_set:
                raise _AddressDefaultTransactionAborted
            return True

        try:
            async with self._database.client.start_session() as session:
                return await session.with_transaction(operation)
        except _AddressDefaultTransactionAborted:
            return False

    async def update_address(
        self,
        request: AddressUpdateRequest,
        user_id: UUID,
    ) -> AddressUpdateResponse:
        """部分更新 active 地址，并通过版本号避免并发覆盖。"""

        (
            address_status,
            address_version,
            is_default,
        ) = await self.get_address_status_and_version(request.address_id, user_id)
        if address_status == "deleted":
            raise AddressStateConflictError("地址已被删除")

        update_data = request.model_dump(
            exclude={"address_id"},
            exclude_none=True,
        )
        if request.is_default is True and not is_default:
            update_succeeded = await self._set_default_address(
                request.address_id,
                user_id,
                address_version,
                {
                    field: value
                    for field, value in update_data.items()
                    if field != "is_default"
                },
            )
        else:
            update_succeeded = await self._repository.update_address(
                request.address_id,
                user_id,
                address_version,
                is_default,
                update_data,
            )
        if update_succeeded:
            return AddressUpdateResponse(
                data=AddressUpdateResponseData(
                    address_id=request.address_id,
                    version=address_version + 1,
                )
            )

        (
            current_status,
            current_version,
            _,
        ) = await self.get_address_status_and_version(request.address_id, user_id)
        if current_status == "deleted":
            raise AddressStateConflictError("地址已被删除")
        if current_version != address_version:
            raise AddressVersionConflictError("原地址已被修改")
        raise AddressUpdateError("地址更新失败")
