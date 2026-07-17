"""chay_migration(): CSDL rỗng → alembic upgrade head tạo đủ schema; CSDL đã có bảng từ
cơ chế cũ (Base.metadata.create_all() thẳng, trước khi dự án có Alembic) nhưng CHƯA có
alembic_version → phải STAMP (không chạy lại DDL tạo bảng, không mất dữ liệu đã có)."""

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.migrate import chay_migration
from app.models.user import User, VaiTro


def test_db_rong_upgrade_tao_du_schema(tmp_path, monkeypatch):
    import app.db.migrate as migrate_module

    db_path = tmp_path / "empty.db"
    monkeypatch.setattr(migrate_module.settings, "database_url", f"sqlite:///{db_path}")

    chay_migration()

    engine = create_engine(f"sqlite:///{db_path}")
    ten_bang = set(inspect(engine).get_table_names())
    assert "alembic_version" in ten_bang
    for bang in ("users", "sessions", "problems", "lop", "chuyen_de", "turns"):
        assert bang in ten_bang


def test_db_cu_co_san_schema_thi_stamp_khong_mat_du_lieu(tmp_path, monkeypatch):
    import app.db.migrate as migrate_module

    db_path = tmp_path / "old_prod.db"
    url = f"sqlite:///{db_path}"
    monkeypatch.setattr(migrate_module.settings, "database_url", url)

    # Mô phỏng production TRƯỚC khi chuyển Alembic: schema tạo qua create_all() thẳng,
    # đã có dữ liệu thật (KHÔNG có bảng alembic_version).
    engine = create_engine(url)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    db.add(User(
        vai_tro=VaiTro.admin, ho_ten="Quản trị", dang_nhap="admin",
        mat_khau_hash="fake-hash-khong-doi",
    ))
    db.commit()
    db.close()
    engine.dispose()

    chay_migration()

    engine2 = create_engine(url)
    ten_bang = set(inspect(engine2).get_table_names())
    assert "alembic_version" in ten_bang

    Session2 = sessionmaker(bind=engine2)
    db2 = Session2()
    try:
        admin = db2.query(User).filter(User.dang_nhap == "admin").first()
        assert admin is not None
        assert admin.mat_khau_hash == "fake-hash-khong-doi"
        assert db2.query(User).count() == 1
    finally:
        db2.close()


def test_chay_lai_lan_2_khong_loi(tmp_path, monkeypatch):
    """Mô phỏng deploy lại (app khởi động lần 2 trở đi): gọi chay_migration() nhiều lần
    liên tiếp phải idempotent, không lỗi."""
    import app.db.migrate as migrate_module

    db_path = tmp_path / "redeploy.db"
    monkeypatch.setattr(migrate_module.settings, "database_url", f"sqlite:///{db_path}")

    chay_migration()
    chay_migration()

    engine = create_engine(f"sqlite:///{db_path}")
    assert "alembic_version" in set(inspect(engine).get_table_names())
