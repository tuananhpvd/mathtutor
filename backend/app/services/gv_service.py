"""Service cho giáo viên: hồ sơ cá nhân, quản lý lớp & học sinh thuộc phạm vi của mình."""

from sqlalchemy.orm import Session

from app.auth.security import hash_password
from app.models.flag import Flag, TrangThaiCo
from app.models.lop import Lop
from app.models.problem import Problem, TrangThaiDuyet
from app.models.progress import Progress
from app.models.session import Session as SessionModel
from app.models.session import TrangThaiSession
from app.models.user import TrangThaiUser, User, VaiTro

# Số lượt hoàn thành tối thiểu của một nhóm (dạng/loại) mới được xếp hạng "tốn nhiều thời
# gian". Dưới ngưỡng, một lượt cá biệt đủ kéo trung bình lên đỉnh bảng — nhiễu thành "tín hiệu".
NGUONG_LUOT_TOI_THIEU = 5


def _hs_dict(u: User) -> dict:
    return {
        "id": u.id, "ho_ten": u.ho_ten, "dang_nhap": u.dang_nhap,
        "trang_thai": u.trang_thai.value, "lop_id": u.lop_id,
    }


def _so_huu_lop(db: Session, gv_id: int, lop_id: int) -> bool:
    lop = db.get(Lop, lop_id)
    return lop is not None and lop.gv_id == gv_id


def _so_huu_hs(db: Session, gv_id: int, hs_id: int) -> bool:
    hs = db.get(User, hs_id)
    if hs is None or hs.vai_tro != VaiTro.hs or hs.lop_id is None:
        return False
    return _so_huu_lop(db, gv_id, hs.lop_id)


# ---------- Tổng quan ----------

def tong_quan_gv(db: Session, gv_id: int, lop_id: int | None = None) -> dict:
    """Thống kê tổng quan cho GV (lớp/HS/câu hỏi/cờ + dạng & loại tốn nhiều thời gian).

    Sĩ số HS / HS bị khóa / cờ theo dõi CỐ Ý gộp MỌI lớp (yêu cầu nghiệp vụ; GV chỉ có 1 lớp
    thì trùng luôn lớp đó). Riêng các thẻ "tốn nhiều thời gian" tính THEO LỚP `lop_id`."""
    lops = db.query(Lop).filter(Lop.gv_id == gv_id).all()
    lop_ids = [lop.id for lop in lops]
    hs = (
        db.query(User).filter(User.vai_tro == VaiTro.hs, User.lop_id.in_(lop_ids)).all()
        if lop_ids else []
    )
    hs_ids = [h.id for h in hs]
    hs_khoa = sum(1 for h in hs if h.trang_thai == TrangThaiUser.khoa)

    # Câu hỏi (ngân hàng dùng chung)
    problems = db.query(Problem).all()
    tong_ch = len(problems)
    ch_duyet = sum(1 for p in problems if p.trang_thai_duyet == TrangThaiDuyet.da_duyet)
    ch_cho = sum(1 for p in problems if p.trang_thai_duyet == TrangThaiDuyet.cho_duyet)

    # Cờ theo dõi — theo phiên của HS thuộc lớp GV
    co = (
        db.query(Flag).join(SessionModel, Flag.session_id == SessionModel.id)
        .filter(SessionModel.hoc_sinh_id.in_(hs_ids)).all()
        if hs_ids else []
    )
    tong_co = len(co)
    co_chua = sum(1 for f in co if f.trang_thai == TrangThaiCo.cho_xu_ly)

    # --- Thẻ "tốn nhiều thời gian": tính THEO LỚP (khác 3 số đếm ở trên vốn cố ý gộp) ---
    lop_ids_tk = [lop_id] if lop_id is not None else lop_ids
    hs_ids_tk = (
        [u.id for u in db.query(User).filter(
            User.vai_tro == VaiTro.hs, User.lop_id.in_(lop_ids_tk)).all()]
        if lop_ids_tk else []
    )
    sess = (
        db.query(SessionModel).filter(
            SessionModel.hoc_sinh_id.in_(hs_ids_tk),
            SessionModel.trang_thai == TrangThaiSession.hoan_thanh,
        ).all()
        if hs_ids_tk else []
    )
    p_cache = {p.id: p for p in problems}
    # TRƯỚC ĐÂY cộng dồn TỔNG thời gian rồi lấy top 3 → dạng nào được GIAO NHIỀU NHẤT luôn
    # đứng đầu, không phải dạng KHÓ NHẤT (một dạng dễ mà 40 HS làm sẽ vượt một dạng khó mà 5 HS
    # làm). Nay dùng THỜI GIAN TRUNG BÌNH MỖI LƯỢT + kèm số lượt để đọc đúng bản chất.
    tg_dang: dict[str, list[int]] = {}
    tg_loai: dict[str, list[int]] = {}
    for s in sess:
        p = p_cache.get(s.problem_id)
        if p is None:
            continue
        t = s.thoi_gian_giay or 0
        ten_dang = f"{p.chuyen_de} › {p.dang.ten}" if p.dang else p.chuyen_de
        tg_dang.setdefault(ten_dang, []).append(t)
        tg_loai.setdefault(p.loai_cau.value, []).append(t)

    def _top(bang: dict[str, list[int]]) -> list[tuple[str, int, int]]:
        """(khóa, thời gian TB mỗi lượt, số lượt) — CHỈ xếp hạng nhóm đủ mẫu, để mẫu nhỏ
        không bị đẩy lên top do một lượt cá biệt kéo trung bình."""
        du_mau = [(k, round(sum(v) / len(v)), len(v))
                  for k, v in bang.items() if len(v) >= NGUONG_LUOT_TOI_THIEU]
        return sorted(du_mau, key=lambda x: x[1], reverse=True)[:3]

    dang_top = _top(tg_dang)
    loai_top = _top(tg_loai)

    return {
        "so_lop": len(lops),
        # 3 số dưới CỐ Ý gộp mọi lớp theo yêu cầu nghiệp vụ (GV 1 lớp thì trùng luôn lớp đó).
        "tong_hoc_sinh": len(hs),
        "hoc_sinh_khoa": hs_khoa,
        "tong_cau_hoi": tong_ch,
        "cau_hoi_da_duyet": ch_duyet,
        "cau_hoi_cho_duyet": ch_cho,
        "tong_co": tong_co,
        "co_da_xu_ly": tong_co - co_chua,
        "co_chua_xu_ly": co_chua,
        # Các thẻ dưới theo LỚP (lop_id) + kèm số lượt để không đọc nhầm.
        "lop_id": lop_id,
        "nguong_luot": NGUONG_LUOT_TOI_THIEU,
        "dang_mat_thoi_gian": [
            {"ten": k, "thoi_gian_tb_giay": tb, "so_luot": n} for k, tb, n in dang_top
        ],
        "loai_mat_thoi_gian": [
            {"loai": k, "thoi_gian_tb_giay": tb, "so_luot": n} for k, tb, n in loai_top
        ],
    }


# ---------- Hồ sơ cá nhân ----------

def ho_so(gv: User) -> dict:
    return {
        "id": gv.id, "ho_ten": gv.ho_ten, "dang_nhap": gv.dang_nhap,
        "vai_tro": gv.vai_tro.value, "trang_thai": gv.trang_thai.value,
    }


def cap_nhat_ho_so(db: Session, gv: User, ho_ten: str | None, mat_khau: str | None) -> User:
    if ho_ten:
        gv.ho_ten = ho_ten.strip()
    if mat_khau:
        gv.mat_khau_hash = hash_password(mat_khau)
    db.commit()
    db.refresh(gv)
    return gv


# ---------- Lớp của GV ----------

def lop_cua_gv(db: Session, gv_id: int) -> list[dict]:
    lops = db.query(Lop).filter(Lop.gv_id == gv_id).order_by(Lop.ten).all()
    hs_by_lop: dict = {}
    for hs in db.query(User).filter(User.vai_tro == VaiTro.hs).all():
        hs_by_lop.setdefault(hs.lop_id, []).append(hs)
    return [
        {
            "id": lop.id, "ten": lop.ten,
            "so_hoc_sinh": len(hs_by_lop.get(lop.id, [])),
            "hoc_sinhs": [_hs_dict(h) for h in hs_by_lop.get(lop.id, [])],
        }
        for lop in lops
    ]


def kiem_tra_trung_ten_lop(db: Session, gv_id: int, ten_lops: list[str]) -> dict:
    """Kiểm tra danh sách tên lớp: tên nào đã tồn tại trong lớp của GV này."""
    ten_clean = [t.strip() for t in ten_lops if t.strip()]
    lops = db.query(Lop).filter(Lop.gv_id == gv_id, Lop.ten.in_(ten_clean)).all()
    lop_by_ten = {lop.ten: lop for lop in lops}
    result = {}
    for ten in ten_clean:
        if ten in lop_by_ten:
            lop = lop_by_ten[ten]
            so_hs = db.query(User).filter(
                User.lop_id == lop.id, User.vai_tro == VaiTro.hs
            ).count()
            result[ten] = {"ton_tai": True, "so_hoc_sinh": so_hs}
        else:
            result[ten] = {"ton_tai": False, "so_hoc_sinh": 0}
    return result


def tao_lop_gv(db: Session, gv_id: int, ten: str) -> Lop:
    if not ten or not ten.strip():
        raise ValueError("Tên lớp không được rỗng")
    lop = Lop(ten=ten.strip(), gv_id=gv_id)
    db.add(lop)
    db.commit()
    db.refresh(lop)
    return lop


def sua_lop_gv(db: Session, gv_id: int, lop_id: int, ten: str) -> Lop:
    if not _so_huu_lop(db, gv_id, lop_id):
        raise ValueError("Không có quyền với lớp này")
    if not ten or not ten.strip():
        raise ValueError("Tên lớp không được rỗng")
    lop = db.get(Lop, lop_id)
    lop.ten = ten.strip()
    db.commit()
    db.refresh(lop)
    return lop


def kiem_tra_trung_dang_nhap(db: Session, dang_nhaps: list[str]) -> list[str]:
    """Trả về các dang_nhap đã tồn tại trong hệ thống."""
    rows = db.query(User.dang_nhap).filter(User.dang_nhap.in_(dang_nhaps)).all()
    return [r[0] for r in rows]


def import_hs_batch(db: Session, gv_id: int, lop_id: int,
                    hoc_sinhs: list[dict]) -> dict:
    """Tạo hàng loạt HS vào lớp. Bỏ qua dang_nhap đã tồn tại."""
    if not _so_huu_lop(db, gv_id, lop_id):
        raise ValueError("Không có quyền với lớp này")
    da_tao, bo_qua = [], []
    for hs in hoc_sinhs:
        if db.query(User).filter(User.dang_nhap == hs["dang_nhap"]).first():
            bo_qua.append(hs["dang_nhap"])
            continue
        u = User(
            vai_tro=VaiTro.hs,
            ho_ten=hs["ho_ten"].strip(),
            dang_nhap=hs["dang_nhap"].strip(),
            mat_khau_hash=hash_password(hs["mat_khau"]),
            lop_id=lop_id,
        )
        db.add(u)
        da_tao.append(hs["ho_ten"])
    db.commit()
    return {"da_tao": da_tao, "bo_qua": bo_qua}


def import_hs_batch_admin(db: Session, lop_id: int, hoc_sinhs: list[dict]) -> dict:
    """Admin: tạo hàng loạt HS vào lớp, không kiểm tra quyền sở hữu GV."""
    lop = db.get(Lop, lop_id)
    if not lop:
        raise ValueError("Lớp không tồn tại")
    da_tao, bo_qua = [], []
    for hs in hoc_sinhs:
        if db.query(User).filter(User.dang_nhap == hs["dang_nhap"]).first():
            bo_qua.append(hs["dang_nhap"])
            continue
        u = User(
            vai_tro=VaiTro.hs,
            ho_ten=hs["ho_ten"].strip(),
            dang_nhap=hs["dang_nhap"].strip(),
            mat_khau_hash=hash_password(hs["mat_khau"]),
            lop_id=lop_id,
        )
        db.add(u)
        da_tao.append(hs["ho_ten"])
    db.commit()
    return {"da_tao": da_tao, "bo_qua": bo_qua}


def xoa_lop_gv(db: Session, gv_id: int, lop_id: int) -> None:
    if not _so_huu_lop(db, gv_id, lop_id):
        raise ValueError("Không có quyền với lớp này")
    for hs in db.query(User).filter(User.lop_id == lop_id).all():
        hs.lop_id = None
    db.delete(db.get(Lop, lop_id))
    db.commit()


# ---------- Học sinh của GV ----------

def danh_sach_hs_gv(db: Session, gv_id: int) -> list[dict]:
    lop_ids = [lop.id for lop in db.query(Lop).filter(Lop.gv_id == gv_id).all()]
    if not lop_ids:
        return []
    lop_ten = {lop.id: lop.ten for lop in db.query(Lop).filter(Lop.id.in_(lop_ids)).all()}
    hss = (
        db.query(User)
        .filter(User.vai_tro == VaiTro.hs, User.lop_id.in_(lop_ids))
        .order_by(User.ho_ten)
        .all()
    )
    return [{**_hs_dict(h), "lop_ten": lop_ten.get(h.lop_id)} for h in hss]


def tao_hs_gv(db: Session, gv_id: int, ho_ten: str, dang_nhap: str,
              mat_khau: str, lop_id: int) -> User:
    if not _so_huu_lop(db, gv_id, lop_id):
        raise ValueError("Phải chọn một lớp bạn phụ trách")
    if db.query(User).filter(User.dang_nhap == dang_nhap).first():
        raise ValueError("Tên đăng nhập đã tồn tại")
    hs = User(
        vai_tro=VaiTro.hs, ho_ten=ho_ten.strip(), dang_nhap=dang_nhap.strip(),
        mat_khau_hash=hash_password(mat_khau), lop_id=lop_id,
    )
    db.add(hs)
    db.commit()
    db.refresh(hs)
    return hs


def sua_hs_gv(db: Session, gv_id: int, hs_id: int, du_lieu: dict) -> User:
    if not _so_huu_hs(db, gv_id, hs_id):
        raise ValueError("Không có quyền với học sinh này")
    hs = db.get(User, hs_id)
    if "dang_nhap" in du_lieu and du_lieu["dang_nhap"]:
        dn = du_lieu["dang_nhap"].strip()
        if dn != hs.dang_nhap and db.query(User).filter(
            User.dang_nhap == dn, User.id != hs_id
        ).first():
            raise ValueError("Tên đăng nhập đã tồn tại")
        hs.dang_nhap = dn
    if "ho_ten" in du_lieu and du_lieu["ho_ten"]:
        hs.ho_ten = du_lieu["ho_ten"].strip()
    if "mat_khau" in du_lieu and du_lieu["mat_khau"]:
        hs.mat_khau_hash = hash_password(du_lieu["mat_khau"])
    db.commit()
    db.refresh(hs)
    return hs


def gan_lop_hs_gv(db: Session, gv_id: int, hs_id: int, lop_id: int) -> User:
    if not _so_huu_hs(db, gv_id, hs_id):
        raise ValueError("Không có quyền với học sinh này")
    if not _so_huu_lop(db, gv_id, lop_id):
        raise ValueError("Chỉ được gán vào lớp bạn phụ trách")
    hs = db.get(User, hs_id)
    hs.lop_id = lop_id
    db.commit()
    db.refresh(hs)
    return hs


def khoa_hs_gv(db: Session, gv_id: int, hs_id: int, trang_thai: str) -> User:
    if not _so_huu_hs(db, gv_id, hs_id):
        raise ValueError("Không có quyền với học sinh này")
    hs = db.get(User, hs_id)
    hs.trang_thai = TrangThaiUser(trang_thai)
    db.commit()
    db.refresh(hs)
    return hs


def xoa_hs_gv(db: Session, gv_id: int, hs_id: int) -> None:
    if not _so_huu_hs(db, gv_id, hs_id):
        raise ValueError("Không có quyền với học sinh này")
    if db.query(SessionModel).filter(SessionModel.hoc_sinh_id == hs_id).count() > 0:
        raise ValueError("Học sinh đã có dữ liệu làm bài, không thể xóa — hãy Khóa tài khoản")
    db.query(Progress).filter(Progress.hoc_sinh_id == hs_id).delete()
    db.delete(db.get(User, hs_id))
    db.commit()


# ---------- Nhận xét gửi học sinh (đồng hành GV→HS) ----------


def nhap_nhan_xet(db: Session, gv_id: int, hs_id: int) -> str:
    """Trả về một bản nháp nhận xét cho HS, dựa trên phân tích năng lực sẵn có
    (không gọi LLM mới — tái dùng bản đã cache/luật để tiết kiệm quota)."""
    if not _so_huu_hs(db, gv_id, hs_id):
        raise ValueError("Không có quyền với học sinh này")
    from app.services.phan_tich_service import lay_phan_tich

    ho_so = lay_phan_tich(db, hs_id)
    ai = ho_so.get("ai") or {}
    draft = (ai.get("cho_hoc_sinh") or "").strip()
    if not draft:
        draft = " ".join(ho_so.get("de_xuat_hs") or []).strip()
    if not draft:
        draft = "Em đang cố gắng tốt. Hãy tiếp tục luyện tập đều đặn nhé!"
    return draft


def gui_nhan_xet(db: Session, gv_id: int, hs_id: int, noi_dung: str) -> dict:
    """GV gửi nhận xét cho HS → tạo thông báo cho HS."""
    if not _so_huu_hs(db, gv_id, hs_id):
        raise ValueError("Không có quyền với học sinh này")
    noi_dung = (noi_dung or "").strip()
    if not noi_dung:
        raise ValueError("Nội dung nhận xét không được để trống")

    from app.models.thong_bao import LoaiThongBao
    from app.services import thong_bao_service

    tb = thong_bao_service.tao(
        db,
        nguoi_nhan_id=hs_id,
        noi_dung=noi_dung,
        loai=LoaiThongBao.nhan_xet,
        nguoi_gui_id=gv_id,
        tieu_de="Nhận xét của thầy/cô",
    )
    return {"id": tb.id, "tao_luc": tb.tao_luc.isoformat() if tb.tao_luc else None}
