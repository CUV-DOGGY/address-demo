from typing import Annotated
from uuid import UUID
from fastapi import Depends
from app.service.address_service import AddressService
from app.repository.address_repository import AddressRepository

from collections.abc import AsyncIterator
from app.amap.client import AmapClient
from app.service.address_validation import AddressValidation
import httpx


async def get_http_client() -> AsyncIterator[httpx.AsyncClient]:
    async with httpx.AsyncClient(timeout=5.0) as http_client:
        yield http_client


HttpClientDepedency = Annotated[httpx.AsyncClient, Depends(get_http_client)]


def get_amap_client(http_client: HttpClientDepedency) -> AmapClient:
    return AmapClient(http_client)


AmapClientDepdency = Annotated[AmapClient, Depends(get_amap_client)]


def get_address_validation(AmapClient: AmapClientDepdency) -> AddressValidation:
    return AddressValidation(AmapClient)


AddressValidationDedency = Annotated[
    AddressValidation, Depends(get_address_validation)
]


def get_user_id() -> UUID:
    """临时返回固定用户 ID,接入认证后替换。"""

    return UUID("7c2c3dc3-2577-4d85-b6a8-03f3d8c21d83")


def get_address_repository() -> AddressRepository:
    """提供地址数据访问层实例，待数据库接入后替换具体实现。"""

    return AddressRepository()


AddressRepositoryDependency = Annotated[
    AddressRepository, Depends(get_address_repository)
]


def get_address_service(
    repository: AddressRepositoryDependency, addressvalidation: AddressValidationDedency
) -> AddressService:
    """通过依赖注入创建地址服务。"""

    return AddressService(repository, addressvalidation)


AddressServiceDependency = Annotated[AddressService, Depends(get_address_service)]
UserIdDependency = Annotated[UUID, Depends(get_user_id)]
