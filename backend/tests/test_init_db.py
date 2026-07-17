"""init_db(): trên Postgres (production) CSDL rỗng KHÔNG được seed tài khoản mẫu có
mật khẩu công khai trong docs/PROGRESS.md (admin123/gv123/hs123) — chỉ tạo 1 admin với
mật khẩu ngẫu nhiên. Trên SQLite (dev/test) vẫn seed đủ như cũ."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.db.init_db as init_db_module
from app.auth.security import verify_password
from app.db.base import Base
from app.models.danh_muc import ChuyenDe
from app.models.lop import Lop
from app.models.user import User, VaiTro


def _engine_rieng():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return engine, sessionmaker(autocommit=False, autoflush=False, bind=engine)


def test_postgres_rong_chi_tao_1_admin_mat_khau_ngau_nhien(monkeypatch, capsys):
    engine, SessionLocal = _engine_rieng()
    monkeypatch.setattr(init_db_module, "engine", engine)
    monkeypatch.setattr(init_db_module, "SessionLocal", SessionLocal)
    monkeypatch.setattr(
        init_db_module.settings, "database_url",
        "postgresql://user:pass@host/db",
    )

    init_db_module.init_db()

    db = SessionLocal()
    try:
        users = db.query(User).all()
        assert len(users) == 1
        admin = users[0]
        assert admin.dang_nhap == "admin"
        assert admin.vai_tro == VaiTro.admin
        # Không dùng mật khẩu mẫu công khai trong docs/PROGRESS.md
        assert not verify_password("admin123", admin.mat_khau_hash)
        # Mật khẩu ngẫu nhiên được in ra log khởi động đúng 1 lần
        out = capsys.readouterr().out
        assert "admin" in out and "CHỈ HIỂN THỊ 1 LẦN" in out

        # Danh mục chương trình học vẫn seed (không phải thông tin nhạy cảm)
        assert db.query(ChuyenDe).count() > 0
        # Không tạo lớp/HS mẫu trên production
        assert db.query(Lop).count() == 0
    finally:
        db.close()


def test_sqlite_rong_van_seed_du_tai_khoan_mau(monkeypatch):
    engine, SessionLocal = _engine_rieng()
    monkeypatch.setattr(init_db_module, "engine", engine)
    monkeypatch.setattr(init_db_module, "SessionLocal", SessionLocal)
    monkeypatch.setattr(init_db_module.settings, "database_url", "sqlite:///./dev.db")

    init_db_module.init_db()

    db = SessionLocal()
    try:
        dang_nhaps = {u.dang_nhap for u in db.query(User).all()}
        assert {"admin", "gv1", "hs1", "quanly"} <= dang_nhaps
        admin = db.query(User).filter(User.dang_nhap == "admin").first()
        assert verify_password("admin123", admin.mat_khau_hash)
        assert db.query(Lop).filter(Lop.ten == "12A1").count() == 1
    finally:
        db.close()
