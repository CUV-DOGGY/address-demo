from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )
    # 高德地图配置
    AMAP_API_KEY: str
    AMAP_POI_DETAIL_URL: str
    AMAP_REVERSE_GEOCODE_URL: str


settings = Settings()
