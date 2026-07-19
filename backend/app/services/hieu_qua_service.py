"""
C2 — Số liệu chứng minh hiệu quả phương pháp Socratic (tất định, KHÔNG dùng LLM).

Nguồn dữ liệu: Session hoàn thành + Turn (mức gợi ý từng lượt) — đều đã được ghi
từ trước, nên số liệu tính ngược được cho toàn bộ dữ liệu cũ, không cần HS/GV làm
gì thêm.

Chỉ số cốt lõi:
1. Phân bố mức gợi ý khi hoàn thành bài (mức 0 = tự làm không cần gợi ý) — "linh hồn"
   của phương pháp gợi mở: HS tự tìm ra đáp án chứ không bị mớm lời giải.
2. Xu hướng phụ thuộc gợi ý: mức gợi ý trung bình ở các bài ĐẦU so với các bài GẦN
   NHẤT của từng HS — giảm dần = tiến bộ thật sự.
3. Chuỗi tuần: số bài hoàn thành / điểm TB / mức gợi ý TB theo tuần — đường tiến bộ.

Lưu ý trình bày trung thực: với cỡ mẫu lớp học, đây là THỐNG KÊ MÔ TẢ, không phải
kiểm định thống kê — báo cáo dự thi nên ghi đúng như vậy.
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.lop import Lop
from app.models.session import Session as SessionModel
from app.models.session import TrangThaiSession
from app.models.turn import Turn
from app.models.user import User

CUA_SO_XU_HUONG = 5  # số bài đầu / gần nhất để so sánh mức gợi ý


def _phien_hoan_thanh(db: Session, hoc_sinh_ids: list[int]) -> list[SessionModel]:
    """Phiên hoàn thành của nhóm HS, cũ → mới (thứ tự cần cho xu hướng)."""
    if not hoc_sinh_ids:
        return []
    return (
        db.query(SessionModel)
        .filter(
            SessionModel.hoc_sinh_id.in_(hoc_sinh_ids),
            SessionModel.trang_thai == TrangThaiSession.hoan_thanh,
            SessionModel.bi_an == False,  # noqa: E712
        )
        .order_by(SessionModel.cap_nhat_luc.asc())
        .all()
    )


def _muc_goi_y_theo_phien(db: Session, session_ids: list[int]) -> dict[int, int]:
    """Mức gợi ý CAO NHẤT từng phiên (max Turn.cap_goi_y) — 1 query GROUP BY."""
    if not session_ids:
        return {}
    rows = (
        db.query(Turn.session_id, func.max(Turn.cap_goi_y))
        .filter(Turn.session_id.in_(session_ids))
        .group_by(Turn.session_id)
        .all()
    )
    return {sid: int(muc or 0) for sid, muc in rows}


def _phan_bo(muc_list: list[int]) -> dict:
    """Đếm phân bố mức gợi ý: 0 / 1 / 2 / 3+ và tỉ lệ tự làm."""
    tong = len(muc_list)
    dem = {"muc_0": 0, "muc_1": 0, "muc_2": 0, "muc_3_plus": 0}
    for m in muc_list:
        if m <= 0:
            dem["muc_0"] += 1
        elif m == 1:
            dem["muc_1"] += 1
        elif m == 2:
            dem["muc_2"] += 1
        else:
            dem["muc_3_plus"] += 1
    return {
        **dem,
        "tong": tong,
        "ty_le_tu_lam": round(dem["muc_0"] * 100 / tong) if tong else None,
        # "thoát mớm": tự làm hoặc chỉ cần gợi ý định hướng mức 1
        "ty_le_muc_toi_da_1": round((dem["muc_0"] + dem["muc_1"]) * 100 / tong) if tong else None,
    }


def _xu_huong_tu_muc(muc_theo_thu_tu: list[int], cua_so: int = CUA_SO_XU_HUONG) -> dict:
    """So mức gợi ý TB của `cua_so` bài đầu với `cua_so` bài gần nhất (cần ≥ 2*cua_so bài
    thì 2 cửa sổ mới không giẫm nhau; ít hơn → chưa đủ dữ liệu)."""
    if len(muc_theo_thu_tu) < cua_so * 2:
        return {"du_du_lieu": False, "dau": None, "gan_nhat": None, "xu_huong": None}
    dau = sum(muc_theo_thu_tu[:cua_so]) / cua_so
    gan = sum(muc_theo_thu_tu[-cua_so:]) / cua_so
    if gan < dau - 0.2:
        xu_huong = "giam"      # giảm phụ thuộc gợi ý = tiến bộ
    elif gan > dau + 0.2:
        xu_huong = "tang"
    else:
        xu_huong = "on_dinh"
    return {"du_du_lieu": True, "dau": round(dau, 1), "gan_nhat": round(gan, 1),
            "xu_huong": xu_huong}


def _tuan_iso(dt: datetime) -> str:
    y, w, _ = dt.isocalendar()
    return f"{y}-T{w:02d}"


def _chuoi_tuan(sessions: list[SessionModel], muc_map: dict[int, int],
                so_tuan: int = 8) -> list[dict]:
    """Chuỗi `so_tuan` tuần gần nhất (kể cả tuần trống): bài / tự làm / điểm TB / gợi ý TB.

    `so_tu_lam` (bài hoàn thành KHÔNG cần gợi ý — mức 0) cùng đơn vị với `so_bai` để FE vẽ
    đường + cột chung MỘT trục tung (combo chart 1 thang đo, không dual-axis)."""
    gom: dict[str, dict] = {}
    for s in sessions:
        khoa = _tuan_iso(s.cap_nhat_luc)
        g = gom.setdefault(khoa, {"so_bai": 0, "so_tu_lam": 0, "_diem": [], "_goi_y": []})
        g["so_bai"] += 1
        if muc_map.get(s.id, 0) == 0:
            g["so_tu_lam"] += 1
        if s.diem is not None:
            g["_diem"].append(s.diem)
        g["_goi_y"].append(muc_map.get(s.id, 0))

    ket = []
    hom_nay = datetime.now(timezone.utc)
    for i in range(so_tuan - 1, -1, -1):
        khoa = _tuan_iso(hom_nay - timedelta(weeks=i))
        g = gom.get(khoa)
        ket.append({
            "tuan": khoa,
            "so_bai": g["so_bai"] if g else 0,
            "so_tu_lam": g["so_tu_lam"] if g else 0,
            "diem_tb": round(sum(g["_diem"]) / len(g["_diem"]), 1) if g and g["_diem"] else None,
            "goi_y_tb": round(sum(g["_goi_y"]) / len(g["_goi_y"]), 1) if g else None,
        })
    return ket


def _moc_bat_dau(db: Session, hoc_sinh_id: int) -> datetime | None:
    """Mốc "Tuần 1" của HS = 0h (UTC) ngày bắt đầu phiên luyện tập ĐẦU TIÊN — dùng phiên
    đầu thay vì "đăng nhập đầu" vì users không lưu mốc đăng nhập, và phiên đầu đúng ngược
    về quá khứ cho mọi HS đang học. Không tính phiên đã ẩn (đặt lại lịch sử → đồng hồ tuần
    cũng tính lại). Chưa có phiên nào → None."""
    dau = (
        db.query(func.min(SessionModel.bat_dau_luc))
        .filter(SessionModel.hoc_sinh_id == hoc_sinh_id, SessionModel.bi_an == False)  # noqa: E712
        .scalar()
    )
    if dau is None:
        return None
    if dau.tzinfo is None:
        dau = dau.replace(tzinfo=timezone.utc)
    return dau.replace(hour=0, minute=0, second=0, microsecond=0)


def _chuoi_tuan_theo_moc(sessions: list[SessionModel], muc_map: dict[int, int],
                         moc: datetime, so_tuan: int = 8) -> list[dict]:
    """Chuỗi tuần TƯƠNG ĐỐI theo mốc riêng từng HS: "Tuần 1" = 7 ngày đầu kể từ `moc`
    (KHÔNG theo tuần lịch của năm). Trả tối đa `so_tuan` tuần gần nhất, HS mới học 3 tuần
    → chỉ 3 phần tử — biểu đồ per-HS tự co lại, nhãn tuần cho biết em đã học bao lâu."""
    def _utc(dt):
        return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt

    def _tuan_cua(dt) -> int:
        return max(1, int((_utc(dt) - moc).days // 7) + 1)

    gom: dict[int, dict] = {}
    for s in sessions:
        k = _tuan_cua(s.cap_nhat_luc)
        g = gom.setdefault(k, {"so_bai": 0, "so_tu_lam": 0, "_diem": [], "_goi_y": []})
        g["so_bai"] += 1
        if muc_map.get(s.id, 0) == 0:
            g["so_tu_lam"] += 1
        if s.diem is not None:
            g["_diem"].append(s.diem)
        g["_goi_y"].append(muc_map.get(s.id, 0))

    tuan_nay = _tuan_cua(datetime.now(timezone.utc))
    ket = []
    for k in range(max(1, tuan_nay - so_tuan + 1), tuan_nay + 1):
        g = gom.get(k)
        ket.append({
            "tuan_so": k,
            "so_bai": g["so_bai"] if g else 0,
            "so_tu_lam": g["so_tu_lam"] if g else 0,
            "diem_tb": round(sum(g["_diem"]) / len(g["_diem"]), 1) if g and g["_diem"] else None,
            "goi_y_tb": round(sum(g["_goi_y"]) / len(g["_goi_y"]), 1) if g else None,
        })
    return ket


def _hoc_sinh_cua_gv(db: Session, gv_id: int,
                     lop_id: int | None = None) -> tuple[list[User], dict[int, str]]:
    """lop_id có giá trị → CHỈ lớp đó; None → mọi lớp. Khác các thống kê còn lại, ở đây view
    gộp ĐƯỢC GIỮ như một tùy chọn hợp lệ: hiệu quả phương pháp Socratic là thuộc tính của CÁCH
    DẠY chứ không của lớp, gộp cho mẫu lớn hơn nên tín hiệu ổn định hơn."""
    q = db.query(Lop).filter(Lop.gv_id == gv_id)
    if lop_id is not None:
        q = q.filter(Lop.id == lop_id)
    lops = q.all()
    lop_ten = {lop.id: lop.ten for lop in lops}
    if not lop_ten:
        return [], {}
    hs = db.query(User).filter(User.lop_id.in_(list(lop_ten))).order_by(User.ho_ten).all()
    return hs, lop_ten


def hieu_qua_hs(db: Session, hoc_sinh_id: int, so_tuan: int = 8) -> dict:
    """Hiệu quả phương pháp cho MỘT học sinh: phân bố + xu hướng + chuỗi tuần.

    Chuỗi tuần per-HS tính theo mốc RIÊNG của em đó (`tuan_so` từ 1, xem _chuoi_tuan_theo_moc);
    chuỗi tuần CẢ LỚP (hieu_qua_lop) vẫn theo tuần lịch — mỗi em một "Tuần 1" khác nhau,
    không gộp chung trục tương đối được."""
    sessions = _phien_hoan_thanh(db, [hoc_sinh_id])
    muc_map = _muc_goi_y_theo_phien(db, [s.id for s in sessions])
    muc_thu_tu = [muc_map.get(s.id, 0) for s in sessions]
    moc = _moc_bat_dau(db, hoc_sinh_id)
    return {
        "hoc_sinh_id": hoc_sinh_id,
        "phan_bo_goi_y": _phan_bo(muc_thu_tu),
        "xu_huong_goi_y": _xu_huong_tu_muc(muc_thu_tu),
        "theo_tuan": _chuoi_tuan_theo_moc(sessions, muc_map, moc, so_tuan) if moc else [],
    }


def hieu_qua_lop(db: Session, gv_id: int, lop_id: int | None = None) -> dict:
    """Hiệu quả phương pháp cấp lớp cho GV: phân bố chung + bảng từng HS."""
    hoc_sinhs, lop_ten = _hoc_sinh_cua_gv(db, gv_id, lop_id)
    hs_ids = [h.id for h in hoc_sinhs]
    sessions = _phien_hoan_thanh(db, hs_ids)
    muc_map = _muc_goi_y_theo_phien(db, [s.id for s in sessions])

    theo_hs: dict[int, list[int]] = {h.id: [] for h in hoc_sinhs}
    for s in sessions:  # đã sắp cũ → mới
        theo_hs[s.hoc_sinh_id].append(muc_map.get(s.id, 0))

    bang_hs = []
    for h in hoc_sinhs:
        muc_list = theo_hs[h.id]
        pb = _phan_bo(muc_list)
        bang_hs.append({
            "hoc_sinh_id": h.id,
            "ho_ten": h.ho_ten,
            "lop_ten": lop_ten.get(h.lop_id),
            "so_bai": pb["tong"],
            "ty_le_tu_lam": pb["ty_le_tu_lam"],
            "xu_huong_goi_y": _xu_huong_tu_muc(muc_list),
        })

    return {
        "phan_bo_goi_y": _phan_bo([muc_map.get(s.id, 0) for s in sessions]),
        "so_hoc_sinh": len(hoc_sinhs),
        "hoc_sinhs": bang_hs,
        "theo_tuan": _chuoi_tuan(sessions, muc_map),
    }


def csv_hieu_qua_lop(db: Session, gv_id: int, lop_id: int | None = None) -> str:
    """Xuất CSV bảng hiệu quả từng HS — đưa thẳng vào báo cáo/phụ lục dự thi.
    Theo đúng phạm vi đang xem (lop_id) để file xuất ra không lệch với màn hình."""
    ket = hieu_qua_lop(db, gv_id, lop_id)
    dong = ["Họ tên,Lớp,Số bài hoàn thành,% tự làm không cần gợi ý,"
            "Gợi ý TB 5 bài đầu,Gợi ý TB 5 bài gần nhất,Xu hướng"]
    nhan_xu_huong = {"giam": "Giảm (tiến bộ)", "tang": "Tăng", "on_dinh": "Ổn định"}
    for r in ket["hoc_sinhs"]:
        xh = r["xu_huong_goi_y"]
        dong.append(",".join([
            f'"{r["ho_ten"]}"',
            f'"{r["lop_ten"] or ""}"',
            str(r["so_bai"]),
            "" if r["ty_le_tu_lam"] is None else str(r["ty_le_tu_lam"]),
            "" if xh["dau"] is None else str(xh["dau"]),
            "" if xh["gan_nhat"] is None else str(xh["gan_nhat"]),
            nhan_xu_huong.get(xh["xu_huong"], "Chưa đủ dữ liệu"),
        ]))
    return "\n".join(dong)
