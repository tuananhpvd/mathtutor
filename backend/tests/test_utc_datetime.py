"""Test kiểu cột UTCDateTime — khóa hành vi tránh tái phát lỗi lệch múi giờ 7 tiếng ở VN.

Bối cảnh: cột DateTime trơn (không timezone=True) làm SQLAlchemy/SQLite/Postgres bỏ mất
tzinfo khi đọc lại — giá trị vẫn đúng UTC nhưng Python coi là "naive", serialize JSON không
có hậu tố ('Z'/'+00:00'), khiến frontend (new Date(...)) hiểu nhầm thành giờ local trình
duyệt. Ở VN (UTC+7), mọi mốc thời gian hiển thị lệch đúng 7 tiếng. Xác nhận bằng gọi API thật
trước khi sửa: tao_luc trả về "2026-07-07T16:25:54.955810" (không hậu tố).
"""

from datetime import datetime, timezone

from sqlalchemy import Column, Integer, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.db.types import UTCDateTime

_Base = declarative_base()


class _MocThoiGian(_Base):
    __tablename__ = "_moc_thoi_gian_test"
    id = Column(Integer, primary_key=True)
    ts = Column(UTCDateTime)


def _db():
    engine = create_engine("sqlite:///:memory:")
    _Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def test_doc_lai_co_tzinfo_utc():
    db = _db()
    now_utc = datetime.now(timezone.utc)
    db.add(_MocThoiGian(id=1, ts=now_utc))
    db.commit()
    db.expire_all()

    row = db.get(_MocThoiGian, 1)
    assert row.ts.tzinfo is not None
    assert row.ts.utcoffset().total_seconds() == 0


def test_isoformat_co_hau_to_utc():
    db = _db()
    db.add(_MocThoiGian(id=1, ts=datetime.now(timezone.utc)))
    db.commit()
    db.expire_all()

    row = db.get(_MocThoiGian, 1)
    # Đây là điều frontend cần: chuỗi ISO PHẢI có hậu tố UTC để new Date() parse đúng,
    # không bị hiểu nhầm thành giờ local trình duyệt.
    assert row.ts.isoformat().endswith("+00:00")


def test_gia_tri_khong_doi_qua_round_trip():
    db = _db()
    now_utc = datetime.now(timezone.utc)
    db.add(_MocThoiGian(id=1, ts=now_utc))
    db.commit()
    db.expire_all()

    row = db.get(_MocThoiGian, 1)
    assert row.ts == now_utc


def test_gia_tri_none_giu_nguyen_none():
    db = _db()
    db.add(_MocThoiGian(id=1, ts=None))
    db.commit()
    db.expire_all()

    row = db.get(_MocThoiGian, 1)
    assert row.ts is None
