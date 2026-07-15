from contextlib import asynccontextmanager

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models.cauhinh  # noqa: F401

# Import models để metadata nhận biết trước khi create_all
import app.models.cot_moc  # noqa: F401
import app.models.de_thi  # noqa: F401
import app.models.flag  # noqa: F401
import app.models.llm_su_dung  # noqa: F401
import app.models.lop  # noqa: F401
import app.models.muc_tieu  # noqa: F401
import app.models.nhiem_vu  # noqa: F401
import app.models.phan_tich  # noqa: F401
import app.models.problem  # noqa: F401
import app.models.progress  # noqa: F401
import app.models.session  # noqa: F401
import app.models.solution_step  # noqa: F401
import app.models.thong_bao  # noqa: F401
import app.models.tom_tat_ly_thuyet  # noqa: F401
import app.models.turn  # noqa: F401
import app.models.user  # noqa: F401
import app.models.yeu_cau_tro_giup  # noqa: F401
from app.db.base import Base
from app.db.session import get_db
from app.main import app

# StaticPool: mọi kết nối dùng cùng 1 SQLite in-memory connection
engine_test = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)


@asynccontextmanager
async def _noop_lifespan(app):
    yield


@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine_test)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine_test)


@pytest.fixture(autouse=True)
def _xoa_cache_cau_hinh():
    """lay_cau_hinh() cache trong tiến trình (module-level) — mỗi test có DB riêng (bảng
    tạo/xóa lại từ đầu) nhưng cache thì sống chung cả tiến trình pytest, nên PHẢI xóa trước
    mỗi test, nếu không test sau có thể đọc nhầm cấu hình cache lại từ test trước."""
    import app.services.admin_service as admin_service
    admin_service._cau_hinh_cache = None
    yield
    admin_service._cau_hinh_cache = None


@pytest.fixture(scope="function")
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    app.router.lifespan_context = _noop_lifespan  # tắt init_db trong test
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
    app.dependency_overrides.clear()
