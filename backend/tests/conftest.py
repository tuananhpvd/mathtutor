from contextlib import asynccontextmanager

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Import models để metadata nhận biết trước khi create_all
import app.models.cot_moc  # noqa: F401
import app.models.cauhinh  # noqa: F401
import app.models.flag  # noqa: F401
import app.models.lop  # noqa: F401
import app.models.muc_tieu  # noqa: F401
import app.models.nhiem_vu  # noqa: F401
import app.models.phan_tich  # noqa: F401
import app.models.problem  # noqa: F401
import app.models.progress  # noqa: F401
import app.models.session  # noqa: F401
import app.models.solution_step  # noqa: F401
import app.models.thong_bao  # noqa: F401
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
