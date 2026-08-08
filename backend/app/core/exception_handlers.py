import logging
import re
import traceback

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.amap.exceptions import AmapError
from app.service.address_service import AddressProviderError

logger = logging.getLogger(__name__)

PUBLIC_SERVICE_UNAVAILABLE_MESSAGE = "地址服务暂时不可用"
_SENSITIVE_QUERY_PATTERN = re.compile(
    r"([?&](?:key|sig)=)[^&\s]+",
    flags=re.IGNORECASE,
)


def _format_exception(exc: Exception) -> str:
    exception_text = "".join(
        traceback.format_exception(type(exc), exc, exc.__traceback__)
    )
    return _SENSITIVE_QUERY_PATTERN.sub(r"\1<redacted>", exception_text)


async def address_provider_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """在程序边界记录地址供应商异常，并返回统一的安全响应。"""

    logger.error(
        "Address provider failure: method=%s path=%s exception_type=%s\n%s",
        request.method,
        request.url.path,
        type(exc).__name__,
        _format_exception(exc),
    )
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"detail": PUBLIC_SERVICE_UNAVAILABLE_MESSAGE},
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(
        AddressProviderError,
        address_provider_exception_handler,
    )
    app.add_exception_handler(
        AmapError,
        address_provider_exception_handler,
    )
