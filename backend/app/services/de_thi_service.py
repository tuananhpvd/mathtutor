"""
Service đề ôn thi THPT (C1).

Cấu trúc đề chuẩn 2025: Phần I = TN4PA (0,25đ/câu) · Phần II = TNDS (bậc thang theo
số ý đúng, tối đa 1đ/câu) · Phần III = TLN (0,5đ/câu). Chấm điểm tái dùng nguyên vẹn
`core/matching.so_khop` (CAS cho TLN, bậc thang cho TNDS) — service này chỉ ghép đề,
quản thời gian và cộng điểm; KHÔNG import LLM.

Trong lúc ĐANG THI tuyệt đối không trả trường đáp án nào (gắt hơn cả phòng học —
không có cả gợi ý); đáp án đúng chỉ xuất hiện trong kết quả SAU KHI NỘP.
"""

import random
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.matching.cas import KetQuaSoKhop
from app.core.matching.matcher import so_khop
from app.models.de_thi import BaiThi, DeThi, DeThiCau, TrangThaiBaiThi
from app.models.lop import Lop
from app.models.problem import Problem, TrangThaiDuyet
from app.models.user import User

PHAN_LOAI = {"I": "TN4PA", "II": "TNDS", "III": "TLN"}
DIEM_CAU = {"I": 0.25, "II": 1.0, "III": 0.5}
GIA_HAN_GIAY = 30  # nhân nhượng trễ mạng khi nộp sát giờ


def _now() -> datetime:
    # Naive UTC — thống nhất với giá trị đọc lại từ cột DateTime (SQLite trả naive).
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _naive(dt: datetime) -> datetime:
    return dt.replace(tzinfo=None) if dt.tzinfo else dt


# ---------- GV: ghép & quản lý đề ----------

def tao_de(db: Session, gv_id: int, ten: str, thoi_gian_phut: int,
           cau_theo_phan: dict[str, list[int]]) -> DeThi:
    """Tạo đề từ danh sách problem_id theo phần {"I": [...], "II": [...], "III": [...]}."""
    ten = (ten or "").strip()
    if not ten:
        raise ValueError("Tên đề không được để trống")
    if not (10 <= int(thoi_gian_phut) <= 180):
        raise ValueError("Thời gian làm bài phải từ 10 đến 180 phút")

    tat_ca_ids: list[int] = []
    for phan in ("I", "II", "III"):
        tat_ca_ids.extend(cau_theo_phan.get(phan) or [])
    if not tat_ca_ids:
        raise ValueError("Đề phải có ít nhất 1 câu")
    if len(set(tat_ca_ids)) != len(tat_ca_ids):
        raise ValueError("Một câu hỏi xuất hiện nhiều lần trong đề")

    problems = {p.id: p for p in db.query(Problem).filter(Problem.id.in_(tat_ca_ids)).all()}
    for phan in ("I", "II", "III"):
        for pid in cau_theo_phan.get(phan) or []:
            p = problems.get(pid)
            if p is None or p.bi_an or p.trang_thai_duyet != TrangThaiDuyet.da_duyet:
                raise ValueError(f"Câu #{pid} không tồn tại hoặc chưa được duyệt")
            if p.loai_cau.value != PHAN_LOAI[phan]:
                raise ValueError(
                    f"Câu #{pid} là {p.loai_cau.value}, không hợp lệ cho Phần {phan} "
                    f"(cần {PHAN_LOAI[phan]})"
                )
            # Nhất quán với quy tắc phòng học: HS chỉ thấy bài của GV chủ nhiệm,
            # nên đề cũng chỉ ghép từ câu của chính GV tạo đề.
            if p.nguoi_tao_id != gv_id:
                raise ValueError(f"Câu #{pid} là câu của giáo viên khác")

    de = DeThi(ten=ten, nguoi_tao_id=gv_id, thoi_gian_phut=int(thoi_gian_phut))
    db.add(de)
    db.flush()
    thu_tu = 0
    for phan in ("I", "II", "III"):
        for pid in cau_theo_phan.get(phan) or []:
            thu_tu += 1
            db.add(DeThiCau(de_thi_id=de.id, problem_id=pid, phan=phan, thu_tu=thu_tu))
    db.commit()
    db.refresh(de)
    return de


def _de_cua_gv(db: Session, gv_id: int, de_id: int) -> DeThi:
    de = db.get(DeThi, de_id)
    if de is None or de.nguoi_tao_id != gv_id:
        raise ValueError("Đề không tồn tại")
    return de


def dat_phat_hanh(db: Session, gv_id: int, de_id: int, phat_hanh: bool) -> DeThi:
    de = _de_cua_gv(db, gv_id, de_id)
    de.phat_hanh = bool(phat_hanh)
    db.commit()
    db.refresh(de)
    return de


def xoa_de(db: Session, gv_id: int, de_id: int) -> None:
    de = _de_cua_gv(db, gv_id, de_id)
    if db.query(BaiThi).filter(BaiThi.de_thi_id == de.id).first():
        raise ValueError("Đề đã có học sinh làm — chỉ có thể thu hồi, không xóa được")
    db.delete(de)
    db.commit()


def diem_toi_da_cua(de: DeThi) -> float:
    return round(sum(DIEM_CAU[c.phan] for c in de.cau_list), 2)


def ds_de_gv(db: Session, gv_id: int) -> list[dict]:
    des = (db.query(DeThi).filter(DeThi.nguoi_tao_id == gv_id)
           .order_by(DeThi.tao_luc.desc()).all())
    ket = []
    for de in des:
        so_nop = db.query(BaiThi).filter(
            BaiThi.de_thi_id == de.id, BaiThi.trang_thai == TrangThaiBaiThi.da_nop
        ).count()
        ket.append({
            "id": de.id, "ten": de.ten, "thoi_gian_phut": de.thoi_gian_phut,
            "phat_hanh": de.phat_hanh, "so_cau": len(de.cau_list),
            "diem_toi_da": diem_toi_da_cua(de), "so_bai_nop": so_nop,
            "tao_luc": de.tao_luc.isoformat(),
        })
    return ket


def ket_qua_lop(db: Session, gv_id: int, de_id: int) -> list[dict]:
    de = _de_cua_gv(db, gv_id, de_id)
    bais = (
        db.query(BaiThi, User.ho_ten)
        .join(User, User.id == BaiThi.hoc_sinh_id)
        .filter(BaiThi.de_thi_id == de.id, BaiThi.trang_thai == TrangThaiBaiThi.da_nop)
        .order_by(BaiThi.diem.desc())
        .all()
    )
    return [{
        "bai_thi_id": b.id, "hoc_sinh_id": b.hoc_sinh_id, "ho_ten": ho_ten,
        "diem": b.diem, "diem_toi_da": b.diem_toi_da,
        "nop_luc": b.nop_luc.isoformat() if b.nop_luc else None,
    } for b, ho_ten in bais]


# ---------- GV: trộn đề tự động theo ma trận (GĐ2) ----------

TY_LE_KHO_MAC_DINH = {"de": 30, "tb": 40, "kho": 30}


def _phan_bo_theo_kho(so_cau: int, ty_le: dict) -> dict[str, int]:
    """Chia `so_cau` theo tỉ lệ % Dễ/TB/Khó, dồn phần dư làm tròn vào mức có tỉ lệ lớn nhất."""
    tong_ty_le = sum(max(0, int(ty_le.get(k, 0))) for k in ("de", "tb", "kho")) or 1
    ket = {k: int(so_cau * max(0, int(ty_le.get(k, 0))) / tong_ty_le) for k in ("de", "tb", "kho")}
    du = so_cau - sum(ket.values())
    if du > 0:
        k_max = max(("de", "tb", "kho"), key=lambda k: int(ty_le.get(k, 0)))
        ket[k_max] += du
    return ket


def _boc_rai_deu_chuyen_de(ung_vien: list[Problem], can: int) -> list[Problem]:
    """Bốc `can` câu ngẫu nhiên nhưng RẢI ĐỀU theo chuyên đề (round-robin trên các
    danh sách đã xáo trộn của từng chuyên đề) — tránh đề dồn 1 chuyên đề."""
    theo_cd: dict[str, list[Problem]] = {}
    for p in ung_vien:
        theo_cd.setdefault(p.chuyen_de or "", []).append(p)
    for ds in theo_cd.values():
        random.shuffle(ds)
    thu_tu_cd = list(theo_cd)
    random.shuffle(thu_tu_cd)
    ket: list[Problem] = []
    while len(ket) < can and any(theo_cd[cd] for cd in thu_tu_cd):
        for cd in thu_tu_cd:
            if len(ket) >= can:
                break
            if theo_cd[cd]:
                ket.append(theo_cd[cd].pop())
    return ket


def tron_de(db: Session, gv_id: int, so_cau: dict, chuyen_de_list: list[str] | None = None,
            ty_le_kho: dict | None = None) -> dict:
    """Đề xuất bộ câu hỏi tự động theo ma trận — KHÔNG lưu gì, GV xem/chỉnh rồi mới tạo đề.

    so_cau: {"I": 12, "II": 4, "III": 6}; chuyen_de_list: [] = mọi chuyên đề;
    ty_le_kho: {"de": %, "tb": %, "kho": %} (mặc định 30/40/30).
    Thiếu câu ở mức khó nào → tự lấy bù mức khác + trả cảnh báo rõ; thiếu tổng → lấy
    tối đa + cảnh báo.
    """
    ty_le = ty_le_kho or TY_LE_KHO_MAC_DINH
    q = db.query(Problem).filter(
        Problem.nguoi_tao_id == gv_id,
        Problem.trang_thai_duyet == TrangThaiDuyet.da_duyet,
        Problem.bi_an == False,  # noqa: E712
    )
    if chuyen_de_list:
        q = q.filter(Problem.chuyen_de.in_(chuyen_de_list))
    pool = q.all()

    ket: dict[str, list[int]] = {}
    canh_bao: list[str] = []
    for phan in ("I", "II", "III"):
        can = max(0, int(so_cau.get(phan, 0)))
        ung_vien = [p for p in pool if p.loai_cau.value == PHAN_LOAI[phan]]
        if can == 0:
            ket[phan] = []
            continue
        if len(ung_vien) < can:
            canh_bao.append(
                f"Phần {phan}: chỉ có {len(ung_vien)}/{can} câu {PHAN_LOAI[phan]} "
                f"phù hợp trong ngân hàng"
            )
        chon: list[Problem] = []
        phan_bo = _phan_bo_theo_kho(can, ty_le)
        con_lai = {p.id: p for p in ung_vien}
        for muc in ("de", "tb", "kho"):
            nhom = [p for p in con_lai.values() if p.do_kho.value == muc]
            lay = _boc_rai_deu_chuyen_de(nhom, phan_bo[muc])
            if len(lay) < phan_bo[muc]:
                canh_bao.append(
                    f"Phần {phan}: thiếu câu mức {muc} ({len(lay)}/{phan_bo[muc]}) — đã lấy bù mức khác"
                )
            for p in lay:
                chon.append(p)
                del con_lai[p.id]
        # Lấy bù cho đủ tổng nếu tỉ lệ khó không khớp pool
        if len(chon) < can and con_lai:
            bu = _boc_rai_deu_chuyen_de(list(con_lai.values()), can - len(chon))
            chon.extend(bu)
        ket[phan] = [p.id for p in chon[:can]]
    return {"cau_theo_phan": ket, "canh_bao": canh_bao}

def _gv_chu_nhiem_id(db: Session, hs: User) -> int | None:
    if hs.lop_id is None:
        return None
    lop = db.get(Lop, hs.lop_id)
    return lop.gv_id if lop else None


def ds_de_hs(db: Session, hs: User) -> list[dict]:
    """Đề đã phát hành của GV chủ nhiệm lớp HS, kèm trạng thái bài gần nhất."""
    gv_id = _gv_chu_nhiem_id(db, hs)
    if gv_id is None:
        return []
    des = (
        db.query(DeThi)
        .filter(DeThi.nguoi_tao_id == gv_id, DeThi.phat_hanh == True)  # noqa: E712
        .order_by(DeThi.tao_luc.desc())
        .all()
    )
    ket = []
    for de in des:
        bai = (
            db.query(BaiThi)
            .filter(BaiThi.de_thi_id == de.id, BaiThi.hoc_sinh_id == hs.id)
            .order_by(BaiThi.id.desc())
            .first()
        )
        ket.append({
            "id": de.id, "ten": de.ten, "thoi_gian_phut": de.thoi_gian_phut,
            "so_cau": len(de.cau_list), "diem_toi_da": diem_toi_da_cua(de),
            "bai_gan_nhat": None if bai is None else {
                "bai_thi_id": bai.id, "trang_thai": bai.trang_thai.value,
                "diem": bai.diem, "diem_toi_da": bai.diem_toi_da,
            },
        })
    return ket


def _het_han_luc(bai: BaiThi, de: DeThi) -> datetime:
    return _naive(bai.bat_dau_luc) + timedelta(
        minutes=de.thoi_gian_phut, seconds=GIA_HAN_GIAY
    )


def bat_dau_thi(db: Session, hs: User, de_id: int) -> BaiThi:
    """Bắt đầu thi (hoặc TIẾP TỤC bài đang thi còn giờ). Hết giờ → tự nộp bài cũ, mở bài mới."""
    de = db.get(DeThi, de_id)
    if de is None or not de.phat_hanh or de.nguoi_tao_id != _gv_chu_nhiem_id(db, hs):
        raise ValueError("Đề không tồn tại hoặc chưa phát hành")
    if not de.cau_list:
        raise ValueError("Đề chưa có câu hỏi")

    bai_dang = (
        db.query(BaiThi)
        .filter(BaiThi.de_thi_id == de.id, BaiThi.hoc_sinh_id == hs.id,
                BaiThi.trang_thai == TrangThaiBaiThi.dang_thi)
        .first()
    )
    if bai_dang is not None:
        if _now() <= _het_han_luc(bai_dang, de):
            return bai_dang  # làm tiếp
        _cham_va_nop(db, bai_dang, de)  # hết giờ → chốt bài cũ

    bai = BaiThi(de_thi_id=de.id, hoc_sinh_id=hs.id)
    db.add(bai)
    db.commit()
    db.refresh(bai)
    return bai


def _bai_cua_hs(db: Session, hs_id: int, bai_id: int) -> tuple[BaiThi, DeThi]:
    bai = db.get(BaiThi, bai_id)
    if bai is None or bai.hoc_sinh_id != hs_id:
        raise ValueError("Bài thi không tồn tại")
    de = db.get(DeThi, bai.de_thi_id)
    if de is None:
        raise ValueError("Đề không còn tồn tại")
    return bai, de


def luu_bai_lam(db: Session, hs_id: int, bai_id: int, bai_lam: dict) -> BaiThi:
    """Autosave khi đang thi. Hết giờ → tự chấm nộp (đáp án lưu TRƯỚC hạn vẫn được tính)."""
    bai, de = _bai_cua_hs(db, hs_id, bai_id)
    if bai.trang_thai == TrangThaiBaiThi.da_nop:
        raise ValueError("Bài đã nộp, không sửa được nữa")
    if _now() > _het_han_luc(bai, de):
        _cham_va_nop(db, bai, de)
        return bai
    hop_le = {str(c.id) for c in de.cau_list}
    bai.bai_lam = {k: v for k, v in (bai_lam or {}).items() if k in hop_le}
    db.commit()
    return bai


def nop_bai(db: Session, hs_id: int, bai_id: int, bai_lam: dict | None = None) -> BaiThi:
    bai, de = _bai_cua_hs(db, hs_id, bai_id)
    if bai.trang_thai == TrangThaiBaiThi.da_nop:
        return bai
    if bai_lam is not None and _now() <= _het_han_luc(bai, de):
        hop_le = {str(c.id) for c in de.cau_list}
        bai.bai_lam = {k: v for k, v in bai_lam.items() if k in hop_le}
    _cham_va_nop(db, bai, de)
    return bai


def _cham_va_nop(db: Session, bai: BaiThi, de: DeThi) -> None:
    """Chấm toàn bộ đề bằng core/matching rồi chốt bài."""
    problems = {
        p.id: p for p in db.query(Problem).filter(
            Problem.id.in_([c.problem_id for c in de.cau_list])
        ).all()
    }
    chi_tiet = []
    tong = 0.0
    for c in de.cau_list:
        p = problems.get(c.problem_id)
        nhap = (bai.bai_lam or {}).get(str(c.id))
        diem_cau = 0.0
        dung = False
        if p is not None and nhap not in (None, "", {}):
            try:
                km = so_khop(p.loai_cau.value, nhap, p.meta or {},
                             p.che_do_so_khop.value)
                dung = km.ket_qua == KetQuaSoKhop.DUNG
                if c.phan == "II":
                    diem_cau = round((km.diem or 0.0) * DIEM_CAU["II"], 2)
                else:
                    diem_cau = DIEM_CAU[c.phan] if dung else 0.0
            except (ValueError, TypeError, AttributeError, KeyError):
                dung = False  # nhập không hợp lệ → 0 điểm, không sập buổi thi
        tong += diem_cau
        chi_tiet.append({
            "de_thi_cau_id": c.id, "problem_id": c.problem_id, "phan": c.phan,
            "thu_tu": c.thu_tu, "da_tra_loi": nhap not in (None, "", {}),
            "dung": dung, "diem": diem_cau, "diem_toi_da": DIEM_CAU[c.phan],
        })
    bai.chi_tiet = chi_tiet
    bai.diem = round(tong, 2)
    bai.diem_toi_da = diem_toi_da_cua(de)
    bai.trang_thai = TrangThaiBaiThi.da_nop
    bai.nop_luc = _now()
    db.commit()
