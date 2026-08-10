import unittest

import httpx

from app.main import app, get_allowed_origins


class CorsTests(unittest.IsolatedAsyncioTestCase):
    async def test_allows_patch_preflight_for_address_updates(self) -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as client:
            response = await client.options(
                "/addresses/update",
                headers={
                    "Origin": get_allowed_origins()[0],
                    "Access-Control-Request-Method": "PATCH",
                    "Access-Control-Request-Headers": "content-type",
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "PATCH",
            response.headers["access-control-allow-methods"],
        )

    async def test_rejects_unsupported_put_preflight(self) -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as client:
            response = await client.options(
                "/addresses/550e8400-e29b-41d4-a716-446655440000/location",
                headers={
                    "Origin": get_allowed_origins()[0],
                    "Access-Control-Request-Method": "PUT",
                    "Access-Control-Request-Headers": "content-type",
                },
            )

        self.assertEqual(response.status_code, 400)
        self.assertNotIn(
            "PUT",
            response.headers["access-control-allow-methods"],
        )


if __name__ == "__main__":
    unittest.main()
