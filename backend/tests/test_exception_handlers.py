import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.amap.exceptions import AmapAddressFetchError
from app.core.exception_handlers import register_exception_handlers
from app.service.address_service import (
    AddressCreateError,
    AddressDataIntegrityError,
    AddressDeleteError,
    AddressFetchError,
    AddressGetError,
    AddressNotFoundError,
    AddressProviderConfigurationError,
    AddressServiceTimeoutError,
    AddressServiceUnavailableError,
    AddressStateConflictError,
    AddressUpdateError,
    AddressValidationError,
    AddressVersionConflictError,
)


def make_app_raising(exception: Exception) -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/raise-error")
    async def raise_error() -> None:
        raise exception

    return app


class ApplicationExceptionHandlerTests(unittest.TestCase):
    def test_maps_application_errors_to_safe_http_responses(self) -> None:
        cases = (
            (AddressGetError("internal"), 404, "address_not_found", "地址不存在"),
            (
                AddressValidationError("internal"),
                422,
                "address_validation_failed",
                "地址数据不正确",
            ),
            (
                AddressNotFoundError("internal"),
                422,
                "address_provider_location_not_found",
                "未获取到有效地址",
            ),
            (
                AddressStateConflictError("internal"),
                409,
                "address_state_conflict",
                "地址状态冲突",
            ),
            (
                AddressVersionConflictError("internal"),
                409,
                "address_version_conflict",
                "原地址已被修改",
            ),
            (
                AddressFetchError("internal"),
                502,
                "address_provider_bad_response",
                "地址服务响应异常",
            ),
            (
                AddressServiceUnavailableError("internal"),
                503,
                "address_provider_unavailable",
                "地址服务暂时不可用",
            ),
            (
                AddressServiceTimeoutError("internal"),
                504,
                "address_provider_timeout",
                "地址服务超时",
            ),
            (
                AddressProviderConfigurationError("internal"),
                500,
                "address_provider_configuration_error",
                "地址服务配置错误",
            ),
            (
                AddressCreateError("internal"),
                500,
                "address_create_failed",
                "地址创建失败",
            ),
            (
                AddressDataIntegrityError("internal"),
                500,
                "address_data_integrity_error",
                "地址数据异常",
            ),
            (
                AddressUpdateError("internal"),
                500,
                "address_update_failed",
                "地址更新失败",
            ),
            (
                AddressDeleteError("internal"),
                500,
                "address_delete_failed",
                "地址删除失败",
            ),
        )

        for error, expected_status, expected_code, expected_detail in cases:
            with self.subTest(error=type(error).__name__):
                client = TestClient(
                    make_app_raising(error),
                    raise_server_exceptions=False,
                )

                if expected_status >= 500:
                    with self.assertLogs(
                        "app.core.exception_handlers",
                        level="ERROR",
                    ):
                        response = client.get("/raise-error")
                else:
                    response = client.get("/raise-error")

                self.assertEqual(response.status_code, expected_status)
                self.assertEqual(
                    response.json(),
                    {"code": expected_code, "detail": expected_detail},
                )
                self.assertNotIn("internal", response.text)

    def test_unhandled_amap_error_returns_safe_502(self) -> None:
        client = TestClient(
            make_app_raising(AmapAddressFetchError("internal-amap")),
            raise_server_exceptions=False,
        )

        with self.assertLogs("app.core.exception_handlers", level="ERROR") as logs:
            response = client.get("/raise-error")

        self.assertEqual(response.status_code, 502)
        self.assertEqual(
            response.json(),
            {
                "code": "address_provider_error",
                "detail": "地址服务响应异常",
            },
        )
        self.assertNotIn("internal-amap", response.text)
        self.assertIn("internal-amap", "\n".join(logs.output))

    def test_redacts_amap_credentials_from_terminal_log(self) -> None:
        error = AddressFetchError(
            "request failed: https://restapi.amap.com/test"
            "?key=secret-key&sig=secret-signature"
        )
        client = TestClient(
            make_app_raising(error),
            raise_server_exceptions=False,
        )

        with self.assertLogs("app.core.exception_handlers", level="ERROR") as logs:
            response = client.get("/raise-error")

        log_output = "\n".join(logs.output)
        self.assertEqual(response.status_code, 502)
        self.assertNotIn("secret-key", log_output)
        self.assertNotIn("secret-signature", log_output)
        self.assertIn("key=<redacted>", log_output)
        self.assertIn("sig=<redacted>", log_output)


if __name__ == "__main__":
    unittest.main()
