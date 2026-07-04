import json
from pathlib import Path

import app.models.cauhinh  # noqa: F401

# Đăng ký tất cả model với metadata
import app.models.cot_moc  # noqa: F401
import app.models.danh_muc  # noqa: F401
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
import app.models.turn  # noqa: F401
import app.models.user  # noqa: F401
import app.models.yeu_cau_tro_giup  # noqa: F401
from app.auth.security import hash_password
from app.db.base import Base, SessionLocal, engine
from app.models.danh_muc import ChuyenDe, Dang
from app.models.lop import Lop
from app.models.problem import Problem
from app.models.solution_step import SolutionStep
from app.models.user import User, VaiTro

SEED_DIR = Path(__file__).parent.parent / "data" / "seed"

# Danh mục mẫu: chuyên đề → dạng
DANH_MUC_SEED = [
    {
        "ten": "Khảo sát hàm số",
        "mo_ta": "Tính đơn điệu, cực trị, tiệm cận, đồ thị hàm số",
        "thu_tu": 1,
        "dang_list": [
            {"ten": "Xét tính đơn điệu", "thu_tu": 1},
            {"ten": "Tìm cực trị", "thu_tu": 2},
            {"ten": "Tìm giá trị lớn nhất / nhỏ nhất", "thu_tu": 3},
            {"ten": "Tiệm cận", "thu_tu": 4},
        ],
    },
    {
        "ten": "Nguyên hàm - Tích phân",
        "mo_ta": "Nguyên hàm, tích phân xác định, ứng dụng",
        "thu_tu": 2,
        "dang_list": [
            {"ten": "Nguyên hàm cơ bản", "thu_tu": 1},
            {"ten": "Tích phân xác định", "thu_tu": 2},
            {"ten": "Ứng dụng tích phân", "thu_tu": 3},
        ],
    },
    {
        "ten": "Xác suất",
        "mo_ta": "Không gian mẫu, biến cố, xác suất cổ điển và có điều kiện",
        "thu_tu": 3,
        "dang_list": [
            {"ten": "Xác suất cổ điển", "thu_tu": 1},
            {"ten": "Xác suất có điều kiện", "thu_tu": 2},
            {"ten": "Biến ngẫu nhiên", "thu_tu": 3},
        ],
    },
    {
        "ten": "Số phức",
        "mo_ta": "Dạng đại số, module, argument, phép tính số phức",
        "thu_tu": 4,
        "dang_list": [
            {"ten": "Dạng đại số và phép tính", "thu_tu": 1},
            {"ten": "Module và argument", "thu_tu": 2},
        ],
    },
    {
        "ten": "Hình học không gian",
        "mo_ta": "Khối đa diện, khối tròn xoay, thể tích, diện tích",
        "thu_tu": 5,
        "dang_list": [
            {"ten": "Khối đa diện", "thu_tu": 1},
            {"ten": "Khối tròn xoay", "thu_tu": 2},
            {"ten": "Thể tích và diện tích", "thu_tu": 3},
        ],
    },
]

# Bản đồ: (tên chuyên đề, tên dạng) → Dang object (điền sau khi seed)
_DANG_MAP: dict[tuple[str, str], int] = {}


def _seed_danh_muc(db, nguoi_tao_id: int | None = None) -> None:
    for cd_data in DANH_MUC_SEED:
        cd = ChuyenDe(
            ten=cd_data["ten"],
            mo_ta=cd_data.get("mo_ta"),
            thu_tu=cd_data["thu_tu"],
            nguoi_tao_id=nguoi_tao_id,
        )
        db.add(cd)
        db.flush()
        for d_data in cd_data.get("dang_list", []):
            dang = Dang(
                chuyen_de_id=cd.id,
                ten=d_data["ten"],
                thu_tu=d_data.get("thu_tu", 0),
                nguoi_tao_id=nguoi_tao_id,
            )
            db.add(dang)
            db.flush()
            _DANG_MAP[(cd_data["ten"], d_data["ten"])] = dang.id


def _migrate_them_cot(engine) -> None:
    """Bổ sung cột mới cho DB cũ mà không mất dữ liệu (SQLite ADD COLUMN)."""
    from sqlalchemy import inspect, text

    insp = inspect(engine)
    ten_bang = insp.get_table_names()
    if "problems" in ten_bang:
        cot = {c["name"] for c in insp.get_columns("problems")}
        if "tao_luc" not in cot:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE problems ADD COLUMN tao_luc DATETIME"))
        if "bi_an" not in cot:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE problems ADD COLUMN bi_an BOOLEAN DEFAULT 0 NOT NULL"))
    if "sessions" in ten_bang:
        cot_s = {c["name"] for c in insp.get_columns("sessions")}
        if "thoi_gian_hoat_dong_giay" not in cot_s:
            with engine.begin() as conn:
                conn.execute(text(
                    "ALTER TABLE sessions ADD COLUMN thoi_gian_hoat_dong_giay INTEGER DEFAULT 0"
                ))
        if "bi_an" not in cot_s:
            with engine.begin() as conn:
                conn.execute(text(
                    "ALTER TABLE sessions ADD COLUMN bi_an BOOLEAN DEFAULT 0 NOT NULL"
                ))
    if "phan_tich_hs" in ten_bang:
        cot_pt = {c["name"] for c in insp.get_columns("phan_tich_hs")}
        if "nguon" not in cot_pt:
            with engine.begin() as conn:
                conn.execute(text(
                    "ALTER TABLE phan_tich_hs ADD COLUMN nguon VARCHAR(16) DEFAULT 'ai'"
                ))
    if "users" in ten_bang:
        cot_u = {c["name"] for c in insp.get_columns("users")}
        if "la_quan_ly" not in cot_u:
            with engine.begin() as conn:
                conn.execute(text(
                    "ALTER TABLE users ADD COLUMN la_quan_ly BOOLEAN DEFAULT 0 NOT NULL"
                ))


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    _migrate_them_cot(engine)
    db = SessionLocal()
    try:
        if db.query(User).count() > 0:
            return  # đã seed rồi

        users_data = json.loads((SEED_DIR / "users.json").read_text(encoding="utf-8"))

        lop_12a1 = Lop(ten="12A1")
        db.add(lop_12a1)
        db.flush()

        for u in users_data:
            user = User(
                vai_tro=VaiTro(u["vai_tro"]),
                ho_ten=u["ho_ten"],
                dang_nhap=u["dang_nhap"],
                mat_khau_hash=hash_password(u["mat_khau"]),
                la_quan_ly=bool(u.get("la_quan_ly", False)),
            )
            if u.get("lop") == "12A1" and u["vai_tro"] == "hs":
                user.lop_id = lop_12a1.id
            db.add(user)

        db.flush()

        gv = db.query(User).filter(User.dang_nhap == "gv1").first()
        gv_id = gv.id if gv else None
        if gv:
            lop_12a1.gv_id = gv.id

        # Seed danh mục chuyên đề → dạng, thuộc sở hữu gv1
        _seed_danh_muc(db, gv_id)

        # Seed bài mẫu — gán dang_id nếu problems.json khai báo "dang"; chủ sở hữu gv1
        if (SEED_DIR / "problems.json").exists():
            problems_data = json.loads((SEED_DIR / "problems.json").read_text(encoding="utf-8"))
            for p_data in problems_data:
                steps_data = p_data.pop("solution_steps", [])
                dang_ten = p_data.pop("dang", None)  # tên dạng (tùy chọn)
                dang_id = _DANG_MAP.get((p_data.get("chuyen_de", ""), dang_ten or ""))
                problem = Problem(
                    dang_id=dang_id, nguoi_tao_id=gv_id, **{k: v for k, v in p_data.items()}
                )
                db.add(problem)
                db.flush()
                for s in steps_data:
                    db.add(SolutionStep(problem_id=problem.id, **s))

        db.commit()
    finally:
        db.close()
