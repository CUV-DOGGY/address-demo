from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="forbid",
    )

    # 前端与跨域配置
    FRONTEND_ORIGIN: str = "http://localhost:5173"

    # 高德地图配置
    AMAP_API_KEY: str
    AMAP_POI_DETAIL_URL: str
    AMAP_REVERSE_GEOCODE_URL: str

    # MongoDB 配置
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DATABASE: str
    MONGODB_SERVER_SELECTION_TIMEOUT_MS: int = 5000

    @field_validator("FRONTEND_ORIGIN")
    @classmethod
    def validate_frontend_origin(cls, value: str) -> str:
        origins = [origin.strip() for origin in value.split(",") if origin.strip()]
        if not origins:
            raise ValueError("FRONTEND_ORIGIN must contain at least one origin")
        if "*" in origins:
            raise ValueError("FRONTEND_ORIGIN must contain explicit origins, not '*'")
        return ",".join(origins)

    @property
    def frontend_origins(self) -> list[str]:
        """返回供 CORS 中间件使用的已校验来源列表。"""

        return self.FRONTEND_ORIGIN.split(",")


settings = Settings()
