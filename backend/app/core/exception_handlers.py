import logging
import re
import traceback

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.amap.exceptions import AmapError
from app.core.exceptions import ApplicationError

logger = logging.getLogger(__name__)

PUBLIC_UPSTREAM_ERROR_MESSAGE = "地址服务响应异常"
_SENSITIVE_QUERY_PATTERN = re.compile(
    r"([?&](?:key|sig)=)[^&\s]+",
    flags=re.IGNORECASE,
)


def _format_exception(exc: Exception) -> str:
    exception_text = "".join(
        traceback.format_exception(type(exc), exc, exc.__traceback__)
    )
    return _SENSITIVE_QUERY_PATTERN.sub(r"\1<redacted>", exception_text)


async def application_exception_handler(
    request: Request,
    exc: ApplicationError,
) -> JSONResponse:
    """统一记录应用异常，并返回稳定、安全的 HTTP 响应。"""

    if exc.status_code >= status.HTTP_500_INTERNAL_SERVER_ERROR:
        logger.error(
            "Application failure: method=%s path=%s error_code=%s "
            "exception_type=%s\n%s",
            request.method,
            request.url.path,
            exc.error_code,
            type(exc).__name__,
            _format_exception(exc),
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.error_code,
            "detail": exc.public_message,
        },
    )


async def unhandled_amap_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """兜底处理未被 Service 翻译的高德异常。"""

    logger.error(
        "Unhandled Amap failure: method=%s path=%s exception_type=%s\n%s",
        request.method,
        request.url.path,
        type(exc).__name__,
        _format_exception(exc),
    )
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={
            "code": "address_provider_error",
            "detail": PUBLIC_UPSTREAM_ERROR_MESSAGE,
        },
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(
        ApplicationError,
        application_exception_handler,
    )
    app.add_exception_handler(
        AmapError,
        unhandled_amap_exception_handler,
    )
