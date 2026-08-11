import unittest

from pydantic import ValidationError

from app.core.config import Settings


def make_settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "AMAP_API_KEY": "test-key",
        "AMAP_POI_DETAIL_URL": "https://example.com/poi",
        "AMAP_REVERSE_GEOCODE_URL": "https://example.com/regeo",
        "MONGODB_DATABASE": "test-database",
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)


class SettingsTests(unittest.TestCase):
    def test_parses_explicit_cors_origins(self) -> None:
        configured = make_settings(
            FRONTEND_ORIGIN="http://localhost:5173, https://example.com "
        )

        self.assertEqual(
            configured.frontend_origins,
            ["http://localhost:5173", "https://example.com"],
        )

    def test_rejects_wildcard_cors_origin(self) -> None:
        with self.assertRaises(ValidationError):
            make_settings(FRONTEND_ORIGIN="*")

    def test_env_example_contains_only_supported_settings(self) -> None:
        configured = Settings(_env_file=".env.example")

        self.assertEqual(configured.frontend_origins, ["http://localhost:5173"])


if __name__ == "__main__":
    unittest.main()
