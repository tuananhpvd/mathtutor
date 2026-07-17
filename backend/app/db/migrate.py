"""Chạy migration schema qua Alembic — thay cho create_all() + _migrate_them_cot() thủ công cũ.

CSDL production (Postgres) đã tồn tại TRƯỚC khi dự án chuyển sang Alembic; schema của nó đã
khớp đúng migration baseline (nhờ kỷ luật _migrate_them_cot() cũ luôn giữ đồng bộ với models
qua từng đợt ADD COLUMN). Lần đầu chạy Alembic trên một CSDL như vậy: KHÔNG được chạy lại DDL
tạo bảng (đã tồn tại, sẽ lỗi "table already exists") — chỉ "stamp" (đánh dấu đã ở đúng
revision) rồi từ lần sau dùng `upgrade` bình thường như một dự án Alembic thuần từ đầu.
"""

from pathlib import Path

from alembic.config import Config
from sqlalchemy import create_engine, inspect

from alembic import command
from app.config import settings

_ALEMBIC_INI = Path(__file__).resolve().parent.parent.parent / "alembic.ini"


def chay_migration() -> None:
    """Luôn tự lấy DATABASE_URL từ settings — KHÔNG nhận engine rời làm tham số, để tránh
    lệch pha giữa engine dùng để soi bảng và engine Alembic thật sự kết nối (Alembic tự mở
    kết nối riêng theo settings.database_url qua alembic/env.py, không dùng lại app.db.base.
    engine)."""
    cfg = Config(str(_ALEMBIC_INI))
    insp_engine = create_engine(settings.database_url)
    try:
        ten_bang = inspect(insp_engine).get_table_names()
    finally:
        insp_engine.dispose()

    if "users" in ten_bang and "alembic_version" not in ten_bang:
        command.stamp(cfg, "head")
    else:
        command.upgrade(cfg, "head")
