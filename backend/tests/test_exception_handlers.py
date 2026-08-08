import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.amap.exceptions import AmapAddressFetchError
from app.core.exception_handlers import (
    PUBLIC_SERVICE_UNAVAILABLE_MESSAGE,
    register_exception_handlers,
)
from app.service.address_service import (
    AddressFetchError,
    AddressNotFoundError,
    AddressProviderConfigurationError,
    AddressServiceTimeoutError,
    AddressServiceUnavailableError,
)


class AddressProviderExceptionHandlerTests(unittest.TestCase):
    def test_returns_safe_503_and_logs_internal_exception(self) -> None:
        exception_types = (
            AddressFetchError,
            AddressNotFoundError,
            AddressProviderConfigurationError,
            AddressServiceTimeoutError,
            AddressServiceUnavailableError,
            AmapAddressFetchError,
        )

        for exception_type in exception_types:
            with self.subTest(exception_type=exception_type.__name__):
                internal_message = f"internal-{exception_type.__name__}"
                app = FastAPI()
                register_exception_handlers(app)

                @app.get("/raise-provider-error")
                async def raise_provider_error() -> None:
                    raise exception_type(internal_message)

                client = TestClient(app, raise_server_exceptions=False)
                with self.assertLogs(
                    "app.core.exception_handlers", level="ERROR"
                ) as logs:
                    response = client.get("/raise-provider-error")

                self.assertEqual(response.status_code, 503)
                self.assertEqual(
                    response.json(),
                    {"detail": PUBLIC_SERVICE_UNAVAILABLE_MESSAGE},
                )
                self.assertNotIn(internal_message, response.text)
                self.assertIn(internal_message, "\n".join(logs.output))

    def test_redacts_amap_credentials_from_terminal_log(self) -> None:
        app = FastAPI()
        register_exception_handlers(app)

        @app.get("/raise-provider-error")
        async def raise_provider_error() -> None:
            raise AddressFetchError(
                "request failed: https://restapi.amap.com/test?key=secret-key&sig=secret-signature"
            )

        client = TestClient(app, raise_server_exceptions=False)
        with self.assertLogs("app.core.exception_handlers", level="ERROR") as logs:
            response = client.get("/raise-provider-error")

        log_output = "\n".join(logs.output)
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("secret-key", log_output)
        self.assertNotIn("secret-signature", log_output)
        self.assertIn("key=<redacted>", log_output)
        self.assertIn("sig=<redacted>", log_output)


if __name__ == "__main__":
    unittest.main()
