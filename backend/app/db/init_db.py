import json
import secrets
from pathlib import Path

import app.models.cauhinh  # noqa: F401

# Đăng ký tất cả model với metadata
import app.models.cot_moc  # noqa: F401
import app.models.danh_muc  # noqa: F401
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
from app.auth.security import hash_password
from app.config import settings
from app.db.base import SessionLocal
from app.db.migrate import chay_migration
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


def _seed_admin_ngau_nhien(db) -> None:
    """CSDL production (Postgres) rỗng: KHÔNG seed tài khoản mẫu users.json — mật khẩu
    của chúng (admin123/gv123/hs123) nằm công khai trong docs/PROGRESS.md trên GitHub.
    Thay vào đó tạo đúng 1 admin với mật khẩu NGẪU NHIÊN, chỉ in ra log khởi động MỘT
    LẦN; admin tự đăng nhập, đổi mật khẩu qua "Tài khoản cá nhân", rồi tự tạo GV/HS qua
    Quản lý tài khoản. Áp dụng khi Postgres bị tạo lại/khôi phục về rỗng, hoặc ai đó
    deploy repo này lần đầu."""
    mat_khau = secrets.token_urlsafe(12)
    db.add(User(
        vai_tro=VaiTro.admin,
        ho_ten="Quản trị",
        dang_nhap="admin",
        mat_khau_hash=hash_password(mat_khau),
    ))
    print(
        "=" * 60 + "\n"
        "CSDL production rỗng — đã tạo tài khoản admin đầu tiên:\n"
        "  Tên đăng nhập: admin\n"
        f"  Mật khẩu (CHỈ HIỂN THỊ 1 LẦN, hãy đổi ngay sau khi đăng nhập): {mat_khau}\n"
        + "=" * 60
    )


def init_db() -> None:
    chay_migration()
    db = SessionLocal()
    try:
        if db.query(User).count() > 0:
            return  # đã seed rồi

        if "postgres" in settings.database_url.lower():
            _seed_admin_ngau_nhien(db)
            _seed_danh_muc(db, None)
            db.commit()
            return

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
                problem = Problem(dang_id=dang_id, nguoi_tao_id=gv_id, **p_data)
                db.add(problem)
                db.flush()
                for s in steps_data:
                    db.add(SolutionStep(problem_id=problem.id, **s))

        db.commit()
    finally:
        db.close()
