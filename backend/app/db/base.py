from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
    # Postgres managed (Render) đóng kết nối nhàn rỗi phía server sau một thời gian —
    # không pre_ping thì request đầu tiên sau lúc rảnh sẽ ăn lỗi "server closed the
    # connection unexpectedly". pre_ping tự phát hiện & mở lại kết nối hỏng trước khi
    # dùng; pool_recycle chủ động tái tạo kết nối cũ trước khi bị server đóng.
    pool_pre_ping=True,
    pool_recycle=300,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass
