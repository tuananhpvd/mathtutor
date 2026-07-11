from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "sqlite:///./dev.db"
    # >= 32 ký tự để tránh InsecureKeyLengthWarning của PyJWT (khuyến nghị RFC 7518 §3.2
    # cho HS256) — vẫn chỉ là giá trị MẪU cho dev/test, production luôn phải tự đặt riêng
    # (xem kiem_tra_an_toan_khoi_dong() bên dưới).
    jwt_secret: str = "dev-secret-change-in-prod-please-set-a-real-one"
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

# Các giá trị JWT_SECRET mặc định/mẫu — ai đọc được mã nguồn (repo công khai hoặc
# .env.example) cũng biết, nên tự ký được JWT giả mạo bất kỳ vai trò nào nếu production
# vô tình chạy với 1 trong các giá trị này.
# Giữ CẢ giá trị mẫu cũ (ngắn, trước khi tăng độ dài cho đủ khuyến nghị PyJWT) lẫn mới —
# phòng trường hợp production cũ còn copy nguyên .env.example bản trước đây.
_JWT_SECRET_KHONG_AN_TOAN = {
    "dev-secret-change-in-prod",
    "dev-secret-change-in-prod-please-set-a-real-one",
    "change-me-in-production",
    "change-me-in-production-please-set-a-real-one",
}


def kiem_tra_an_toan_khoi_dong() -> None:
    """Fail-fast khi khởi động: chặn app chạy với JWT_SECRET mặc định TRÊN MỘT CSDL
    trông như production (PostgreSQL) — tránh vô tình deploy với secret công khai."""
    la_postgres = "postgres" in settings.database_url.lower()
    if la_postgres and settings.jwt_secret in _JWT_SECRET_KHONG_AN_TOAN:
        raise RuntimeError(
            "JWT_SECRET đang là giá trị mặc định/mẫu trong khi DATABASE_URL là "
            "PostgreSQL (trông như production) — PHẢI đặt biến môi trường JWT_SECRET "
            "riêng, dài, ngẫu nhiên, bí mật trước khi khởi động. Xem backend/.env.example."
        )
