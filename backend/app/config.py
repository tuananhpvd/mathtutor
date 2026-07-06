from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "sqlite:///./dev.db"
    jwt_secret: str = "dev-secret-change-in-prod"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480

    llm_provider: str = "stub"
    llm_api_key: str = ""
    llm_model: str = ""
    llm_temperature: float = 0.2

    cors_extra_origins: str = ""


settings = Settings()

# Bảng số gợi ý mặc định theo độ khó (Phương án C, DATA_MODEL mục 12).
# Đây là GIÁ TRỊ KHỞI TẠO khi tạo bài/AI sinh; GV chỉnh tự do (khuyến nghị 1–5).
SO_GOI_Y_MAC_DINH: dict[str, int] = {"de": 2, "tb": 3, "kho": 4}
