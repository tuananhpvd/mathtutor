"""Fail-fast: JWT_SECRET mặc định/mẫu KHÔNG được chạy chung với DATABASE_URL PostgreSQL
(dấu hiệu production) — tránh vô tình deploy với secret ai đọc mã nguồn cũng biết."""

import pytest

from app.config import kiem_tra_an_toan_khoi_dong, settings


@pytest.fixture(autouse=True)
def _khoi_phuc_settings():
    database_url_goc = settings.database_url
    jwt_secret_goc = settings.jwt_secret
    yield
    settings.database_url = database_url_goc
    settings.jwt_secret = jwt_secret_goc


def test_chan_postgres_voi_secret_mac_dinh():
    settings.database_url = "postgresql://user:pw@host/db"
    settings.jwt_secret = "dev-secret-change-in-prod"
    with pytest.raises(RuntimeError, match="JWT_SECRET"):
        kiem_tra_an_toan_khoi_dong()


def test_chan_postgres_voi_secret_mau_trong_env_example():
    settings.database_url = "postgresql://user:pw@host/db"
    settings.jwt_secret = "change-me-in-production"
    with pytest.raises(RuntimeError, match="JWT_SECRET"):
        kiem_tra_an_toan_khoi_dong()


def test_cho_phep_postgres_voi_secret_rieng():
    settings.database_url = "postgresql://user:pw@host/db"
    settings.jwt_secret = "mot-chuoi-bi-mat-ngau-nhien-that-dai-khong-doan-duoc"
    kiem_tra_an_toan_khoi_dong()  # không raise


def test_cho_phep_sqlite_du_secret_mac_dinh():
    """Dev/test dùng SQLite — secret mặc định vẫn được phép (không phải production)."""
    settings.database_url = "sqlite:///./dev.db"
    settings.jwt_secret = "dev-secret-change-in-prod"
    kiem_tra_an_toan_khoi_dong()  # không raise
