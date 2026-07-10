"""
Admin service: thống kê tổng, quản lý tài khoản, cấu hình hệ thống.
"""

from sqlalchemy.orm import Session

from app.auth.security import hash_password
from app.config import SO_GOI_Y_MAC_DINH, settings
from app.core.matching.scoring import BANG_BAC_THANG
from app.models.cauhinh import CauHinh
from app.models.flag import Flag, TrangThaiCo
from app.models.lop import Lop
from app.models.problem import Problem, TrangThaiDuyet
from app.models.session import Session as SessionModel
from app.models.session import TrangThaiSession
from app.models.user import TrangThaiUser, User, VaiTro

# Cấu hình mặc định (dùng khi DB chưa có bản ghi).
CAU_HINH_MAC_DINH: dict = {
    "nguong_co_khong_hieu": 3,
    # Số lần phản hồi bị lớp chốt chặn (rò rỉ đáp án) trong 1 phiên → tự gắn cờ cho GV.
    "nguong_co_chot_chan": 3,
    # Ngưỡng nghỉ (giây): khoảng cách giữa 2 lần tương tác vượt mức này coi là "rời đi",
    # chỉ tính tối đa bằng ngưỡng vào thời gian làm bài (chống phồng khi quay lại làm sau).
    "nguong_nghi_giay": 180,
    "llm_temperature": settings.llm_temperature,
    "so_goi_y_mac_dinh": SO_GOI_Y_MAC_DINH,
    "bang_bac_thang": {str(k): v for k, v in BANG_BAC_THANG.items()},
    # LLM cho "AI sinh câu hỏi" — admin chọn nhà cung cấp & nhập khóa API.
    "llm_provider": "gemini",   # gemini | anthropic | openai | stub
    "llm_model": "",            # để trống = dùng model mặc định của nhà cung cấp
    "llm_api_key_gemini": "",
    "llm_api_key_anthropic": "",
    "llm_api_key_openai": "",
    # Bật/tắt chế độ suy luận (thinking) theo từng nhà cung cấp — mặc định TẮT cho
    # nhanh & đỡ tốn token (tránh thinking ăn token gây cắt cụt JSON).
    "llm_thinking_gemini": False,
    "llm_thinking_anthropic": False,
    "llm_thinking_openai": False,
    # Tự động (tái) sinh phân tích năng lực AI theo lịch nền (không cần bấm tay).
    "tu_dong_phan_tich": True,
    "chu_ky_phut_phan_tich": 360,  # quét mỗi N phút (tối thiểu 5)
    # Phanh chi phí LLM: giới hạn lượt gọi LLM THẬT mỗi ngày (0 = không giới hạn).
    # Hội thoại vượt ngưỡng chỉ chuyển sang lời diễn đạt mẫu, KHÔNG chặn HS học.
    "gioi_han_llm_hs_ngay": 30,        # lượt hội thoại / học sinh / ngày
    "gioi_han_llm_he_thong_ngay": 500,  # tổng lượt toàn hệ thống / ngày
    # Trang "sản phẩm đang hoàn thiện" — chặn người ngoài xem trong lúc chưa ra mắt chính
    # thức, nhưng ai có đúng "mã xem trước" (bao_tri_ma) vẫn vào dùng bình thường (kể cả
    # đăng nhập GV/HS/Admin) — xem GET /api/trang-thai-bao-tri (public, không cần đăng nhập).
    "bao_tri_bat": False,
    "bao_tri_ma": "xem-truoc-mt79",
    "bao_tri_noi_dung": "SẢN PHẨM ĐANG HOÀN THIỆN. HÃY QUAY LẠI SAU NGÀY 08/08/2026!",
}

# Các khóa cấu hình là bí mật (KHÔNG trả nguyên văn về giao diện).
CAU_HINH_BI_MAT = {"llm_api_key_gemini", "llm_api_key_anthropic", "llm_api_key_openai"}


def thong_ke(db: Session) -> dict:
    base_cau_hoi = db.query(Problem).filter(Problem.bi_an == False)  # noqa: E712
    return {
        # Người dùng
        "so_nguoi_dung": db.query(User).count(),
        "so_giao_vien": db.query(User).filter(User.vai_tro == VaiTro.gv).count(),
        "so_hoc_sinh": db.query(User).filter(User.vai_tro == VaiTro.hs).count(),
        "so_lop": db.query(Lop).count(),
        # Câu hỏi
        "so_cau_hoi": base_cau_hoi.count(),
        "so_cau_da_duyet": base_cau_hoi.filter(
            Problem.trang_thai_duyet == TrangThaiDuyet.da_duyet
        ).count(),
        "so_cau_cho_duyet": base_cau_hoi.filter(
            Problem.trang_thai_duyet == TrangThaiDuyet.cho_duyet
        ).count(),
        "so_cau_an": db.query(Problem).filter(Problem.bi_an == True).count(),  # noqa: E712
        "cau_theo_loai": {
            loai: base_cau_hoi.filter(Problem.loai_cau == loai).count()
            for loai in ("TN4PA", "TNDS", "TLN")
        },
        "cau_theo_do_kho": {
            dk: base_cau_hoi.filter(Problem.do_kho == dk).count()
            for dk in ("de", "tb", "kho")
        },
        # Phiên học
        "so_phien": db.query(SessionModel).filter(
            SessionModel.bi_an == False  # noqa: E712
        ).count(),
        "so_phien_dang_lam": db.query(SessionModel).filter(
            SessionModel.bi_an == False,  # noqa: E712
            SessionModel.trang_thai == TrangThaiSession.dang_lam,
        ).count(),
        "so_phien_hoan_thanh": db.query(SessionModel).filter(
            SessionModel.bi_an == False,  # noqa: E712
            SessionModel.trang_thai == TrangThaiSession.hoan_thanh,
        ).count(),
        # Cờ
        "so_co_tong": db.query(Flag).count(),
        "so_co_chua_xu_ly": db.query(Flag)
        .filter(Flag.trang_thai == TrangThaiCo.cho_xu_ly)
        .count(),
        # Provider LLM THẬT SỰ đang chạy: ưu tiên cấu hình Admin lưu trong DB (dùng bởi
        # get_llm_client), không phải settings.llm_provider (env) — 2 nơi có thể khác
        # nhau nếu Admin đã đổi trong Cấu hình → AI mà không đổi biến môi trường.
        "llm_provider": lay_cau_hinh(db).get("llm_provider", settings.llm_provider),
    }


def danh_sach_tai_khoan(db: Session) -> list[dict]:
    users = db.query(User).order_by(User.id).all()
    lop_ten = {lop.id: lop.ten for lop in db.query(Lop).all()}
    return [
        {
            "id": u.id,
            "ho_ten": u.ho_ten,
            "dang_nhap": u.dang_nhap,
            "vai_tro": u.vai_tro.value,
            "trang_thai": u.trang_thai.value,
            "lop_id": u.lop_id,
            "lop_ten": lop_ten.get(u.lop_id),
        }
        for u in users
    ]


def danh_sach_lop(db: Session) -> list[dict]:
    """Danh sách lớp kèm tên GV phụ trách (nếu có)."""
    rows = db.query(Lop).order_by(Lop.ten).all()
    gv_ten = {u.id: u.ho_ten for u in db.query(User).filter(User.vai_tro == VaiTro.gv).all()}
    return [
        {"id": lop.id, "ten": lop.ten, "gv_id": lop.gv_id, "gv_ten": gv_ten.get(lop.gv_id)}
        for lop in rows
    ]


def gan_lop_tai_khoan(db: Session, user_id: int, lop_id: int | None) -> User:
    """Gán (hoặc bỏ) lớp cho một tài khoản gv/hs."""
    user = db.get(User, user_id)
    if user is None:
        raise ValueError("Không tìm thấy tài khoản")
    if user.vai_tro == VaiTro.admin:
        raise ValueError("Admin không thuộc lớp")
    if lop_id is not None and db.get(Lop, lop_id) is None:
        raise ValueError("Không tìm thấy lớp")
    user.lop_id = lop_id
    db.commit()
    db.refresh(user)
    return user


def sua_tai_khoan(db: Session, user_id: int, du_lieu: dict) -> User:
    """Sửa tài khoản gv/hs. du_lieu (exclude_unset): ho_ten, dang_nhap, mat_khau, vai_tro."""
    user = db.get(User, user_id)
    if user is None:
        raise ValueError("Không tìm thấy tài khoản")
    if user.vai_tro == VaiTro.admin:
        raise ValueError("Không thể sửa tài khoản admin tại đây")

    if "dang_nhap" in du_lieu and du_lieu["dang_nhap"]:
        dn = du_lieu["dang_nhap"].strip()
        if dn != user.dang_nhap and db.query(User).filter(
            User.dang_nhap == dn, User.id != user_id
        ).first():
            raise ValueError("Tên đăng nhập đã tồn tại")
        user.dang_nhap = dn
    if "ho_ten" in du_lieu and du_lieu["ho_ten"]:
        user.ho_ten = du_lieu["ho_ten"].strip()
    if "mat_khau" in du_lieu and du_lieu["mat_khau"]:
        user.mat_khau_hash = hash_password(du_lieu["mat_khau"])
    if "vai_tro" in du_lieu and du_lieu["vai_tro"]:
        if du_lieu["vai_tro"] not in {"gv", "hs"}:
            raise ValueError("Vai trò không hợp lệ")
        moi = VaiTro(du_lieu["vai_tro"])
        if moi != user.vai_tro and user.vai_tro == VaiTro.gv:
            # Đổi GV → vai trò khác: bỏ phụ trách các lớp đang giữ
            for lop in db.query(Lop).filter(Lop.gv_id == user_id).all():
                lop.gv_id = None
        user.vai_tro = moi

    db.commit()
    db.refresh(user)
    return user


def xoa_tai_khoan(db: Session, user_id: int) -> None:
    """Xóa tài khoản. HS có phiên học → chặn (gợi ý Khóa). GV → gỡ phụ trách lớp."""
    from app.models.progress import Progress

    user = db.get(User, user_id)
    if user is None:
        raise ValueError("Không tìm thấy tài khoản")
    if user.vai_tro == VaiTro.admin:
        raise ValueError("Không thể xóa tài khoản admin")

    if user.vai_tro == VaiTro.hs:
        if db.query(SessionModel).filter(SessionModel.hoc_sinh_id == user_id).count() > 0:
            raise ValueError("Học sinh đã có dữ liệu làm bài, không thể xóa — hãy Khóa tài khoản")
        db.query(Progress).filter(Progress.hoc_sinh_id == user_id).delete()
    if user.vai_tro == VaiTro.gv:
        for lop in db.query(Lop).filter(Lop.gv_id == user_id).all():
            lop.gv_id = None

    db.delete(user)
    db.commit()


# ---------- Quản lý lớp ----------

def _hs_dict(u: User) -> dict:
    return {
        "id": u.id, "ho_ten": u.ho_ten, "dang_nhap": u.dang_nhap,
        "trang_thai": u.trang_thai.value, "lop_id": u.lop_id,
    }


def tao_lop(db: Session, ten: str, gv_id: int | None = None) -> Lop:
    if not ten or not ten.strip():
        raise ValueError("Tên lớp không được rỗng")
    if gv_id is not None:
        gv = db.get(User, gv_id)
        if gv is None or gv.vai_tro != VaiTro.gv:
            raise ValueError("Giáo viên phụ trách không hợp lệ")
    lop = Lop(ten=ten.strip(), gv_id=gv_id)
    db.add(lop)
    db.commit()
    db.refresh(lop)
    return lop


def sua_lop(db: Session, lop_id: int, du_lieu: dict) -> Lop:
    """Sửa lớp. du_lieu (exclude_unset): ten, gv_id (None = bỏ phụ trách)."""
    lop = db.get(Lop, lop_id)
    if lop is None:
        raise ValueError("Không tìm thấy lớp")
    if "ten" in du_lieu and du_lieu["ten"]:
        lop.ten = du_lieu["ten"].strip()
    if "gv_id" in du_lieu:
        gv_id = du_lieu["gv_id"]
        if gv_id is not None:
            gv = db.get(User, gv_id)
            if gv is None or gv.vai_tro != VaiTro.gv:
                raise ValueError("Giáo viên phụ trách không hợp lệ")
        lop.gv_id = gv_id
    db.commit()
    db.refresh(lop)
    return lop


def xoa_lop(db: Session, lop_id: int) -> None:
    """Xóa lớp: gỡ học sinh khỏi lớp (lop_id = None) rồi xóa."""
    lop = db.get(Lop, lop_id)
    if lop is None:
        raise ValueError("Không tìm thấy lớp")
    for hs in db.query(User).filter(User.lop_id == lop_id).all():
        hs.lop_id = None
    db.delete(lop)
    db.commit()


def danh_sach_lop_chi_tiet(db: Session) -> list[dict]:
    """Danh sách lớp kèm GV phụ trách + danh sách học sinh."""
    lops = db.query(Lop).order_by(Lop.ten).all()
    gv_ten = {u.id: u.ho_ten for u in db.query(User).filter(User.vai_tro == VaiTro.gv).all()}
    hs_by_lop: dict = {}
    for hs in db.query(User).filter(User.vai_tro == VaiTro.hs).all():
        hs_by_lop.setdefault(hs.lop_id, []).append(hs)
    return [
        {
            "id": lop.id, "ten": lop.ten, "gv_id": lop.gv_id,
            "gv_ten": gv_ten.get(lop.gv_id),
            "so_hoc_sinh": len(hs_by_lop.get(lop.id, [])),
            "hoc_sinhs": [_hs_dict(h) for h in hs_by_lop.get(lop.id, [])],
        }
        for lop in lops
    ]


def danh_sach_giao_vien(db: Session) -> list[dict]:
    """Danh sách GV kèm lớp phụ trách + học sinh các lớp đó."""
    gvs = db.query(User).filter(User.vai_tro == VaiTro.gv).order_by(User.ho_ten).all()
    lops = db.query(Lop).all()
    hs_by_lop: dict = {}
    for hs in db.query(User).filter(User.vai_tro == VaiTro.hs).all():
        hs_by_lop.setdefault(hs.lop_id, []).append(hs)
    lops_by_gv: dict = {}
    for lop in lops:
        lops_by_gv.setdefault(lop.gv_id, []).append(lop)
    return [
        {
            "id": gv.id, "ho_ten": gv.ho_ten, "dang_nhap": gv.dang_nhap,
            "trang_thai": gv.trang_thai.value,
            "lops": [
                {"id": lop.id, "ten": lop.ten,
                 "hoc_sinhs": [_hs_dict(h) for h in hs_by_lop.get(lop.id, [])]}
                for lop in lops_by_gv.get(gv.id, [])
            ],
        }
        for gv in gvs
    ]


def danh_sach_hoc_sinh(db: Session) -> list[dict]:
    """Danh sách HS kèm lớp + GV phụ trách lớp."""
    hss = db.query(User).filter(User.vai_tro == VaiTro.hs).order_by(User.ho_ten).all()
    lop_map = {lop.id: lop for lop in db.query(Lop).all()}
    gv_ten = {u.id: u.ho_ten for u in db.query(User).filter(User.vai_tro == VaiTro.gv).all()}
    out = []
    for hs in hss:
        lop = lop_map.get(hs.lop_id)
        out.append({
            "id": hs.id, "ho_ten": hs.ho_ten, "dang_nhap": hs.dang_nhap,
            "trang_thai": hs.trang_thai.value,
            "lop_id": hs.lop_id, "lop_ten": lop.ten if lop else None,
            "gv_ten": gv_ten.get(lop.gv_id) if lop else None,
        })
    return out


def tao_tai_khoan(
    db: Session, ho_ten: str, dang_nhap: str, mat_khau: str, vai_tro: str, lop_id: int | None
) -> User:
    if vai_tro not in {"gv", "hs"}:
        raise ValueError("Chỉ tạo được tài khoản gv hoặc hs")
    if db.query(User).filter(User.dang_nhap == dang_nhap).first():
        raise ValueError("Tên đăng nhập đã tồn tại")
    user = User(
        ho_ten=ho_ten,
        dang_nhap=dang_nhap,
        mat_khau_hash=hash_password(mat_khau),
        vai_tro=VaiTro(vai_tro),
        lop_id=lop_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def doi_trang_thai_tai_khoan(db: Session, user_id: int, trang_thai: str) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise ValueError("Không tìm thấy tài khoản")
    if user.vai_tro == VaiTro.admin:
        raise ValueError("Không thể khóa tài khoản admin")
    user.trang_thai = TrangThaiUser(trang_thai)
    db.commit()
    db.refresh(user)
    return user


def lay_cau_hinh(db: Session) -> dict:
    """Cấu hình ĐẦY ĐỦ (gồm khóa API nguyên văn) — chỉ dùng nội bộ phía server."""
    ket_qua = dict(CAU_HINH_MAC_DINH)
    for row in db.query(CauHinh).all():
        ket_qua[row.khoa] = row.gia_tri.get("v", row.gia_tri)
    return ket_qua


def lay_cau_hinh_an_toan(db: Session) -> dict:
    """Cấu hình cho giao diện admin: thay khóa API bằng cờ '<khoa>_da_dat' (bool)."""
    cau_hinh = lay_cau_hinh(db)
    ket_qua = {}
    for k, v in cau_hinh.items():
        if k in CAU_HINH_BI_MAT:
            ket_qua[f"{k}_da_dat"] = bool(str(v).strip())
        else:
            ket_qua[k] = v
    return ket_qua


def import_tai_khoan_batch(db: Session, tai_khoans: list[dict]) -> dict:
    """Tạo hàng loạt tài khoản GV/HS. Bỏ qua dang_nhap đã tồn tại."""
    da_tao, bo_qua = [], []
    for tk in tai_khoans:
        if db.query(User).filter(User.dang_nhap == tk["dang_nhap"]).first():
            bo_qua.append(tk["dang_nhap"])
            continue
        u = User(
            vai_tro=VaiTro(tk["vai_tro"]),
            ho_ten=tk["ho_ten"].strip(),
            dang_nhap=tk["dang_nhap"].strip(),
            mat_khau_hash=hash_password(tk["mat_khau"]),
            lop_id=None,
        )
        db.add(u)
        da_tao.append(tk["ho_ten"])
    db.commit()
    return {"da_tao": da_tao, "bo_qua": bo_qua}


def dat_cau_hinh(db: Session, khoa: str, gia_tri) -> dict:
    if khoa not in CAU_HINH_MAC_DINH:
        raise ValueError(f"Khóa cấu hình không hợp lệ: {khoa}")
    # Khóa API rỗng = giữ nguyên giá trị cũ (tránh xóa nhầm khi lưu form).
    if khoa in CAU_HINH_BI_MAT and not str(gia_tri or "").strip():
        return lay_cau_hinh_an_toan(db)
    row = db.get(CauHinh, khoa)
    if row is None:
        row = CauHinh(khoa=khoa, gia_tri={"v": gia_tri})
        db.add(row)
    else:
        row.gia_tri = {"v": gia_tri}
    db.commit()
    return lay_cau_hinh(db)
