"""Kiểu cột dùng chung cho toàn bộ mốc thời gian trong DB."""

from datetime import timezone

from sqlalchemy import DateTime
from sqlalchemy.types import TypeDecorator


class UTCDateTime(TypeDecorator):
    """DateTime lưu dạng "naive" trong DB (tương thích SQLite lẫn Postgres) nhưng LUÔN coi là
    UTC — tự gắn lại tzinfo=UTC khi đọc ra.

    Lý do: toàn bộ code tạo mốc thời gian bằng datetime.now(timezone.utc), nhưng cột DateTime
    trơn (không timezone=True) làm SQLAlchemy/SQLite/Postgres bỏ mất tzinfo khi đọc lại — giá
    trị vẫn ĐÚNG là UTC nhưng Python coi là "naive". Khi serialize sang JSON, .isoformat() của
    datetime naive KHÔNG có hậu tố ('Z'/'+00:00'), khiến frontend (new Date(...)) hiểu nhầm
    thành giờ local trình duyệt thay vì UTC — ở VN (UTC+7) mọi mốc thời gian hiển thị lệch đúng
    7 tiếng. Gắn lại tzinfo=UTC khi đọc giúp FastAPI/Pydantic tự động thêm "+00:00" lúc
    serialize, frontend parse đúng rồi tự quy đổi sang giờ VN qua toLocaleString('vi-VN').
    """

    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if value.tzinfo is not None:
            value = value.astimezone(timezone.utc).replace(tzinfo=None)
        return value

    def process_result_value(self, value, dialect):
        if value is None or value.tzinfo is not None:
            return value
        return value.replace(tzinfo=timezone.utc)
