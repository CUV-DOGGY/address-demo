from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
    )
    # 高德地图配置
    AMAP_API_KEY: str
    AMAP_POI_DETAIL_URL: str
    AMAP_REVERSE_GEOCODE_URL: str

    # MongoDB 配置
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DATABASE: str
    MONGODB_SERVER_SELECTION_TIMEOUT_MS: int = 5000


settings = Settings()
