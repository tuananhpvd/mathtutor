"""
Phân tích năng lực học sinh (TẤT ĐỊNH — không gọi LLM).

Tính "hồ sơ năng lực" theo chuyên đề / dạng / loại câu từ lịch sử làm bài, rồi
đưa ra đề xuất theo LUẬT. Đây là Bước 1+2; lớp LLM diễn giải sẽ thêm ở bước sau.
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.phan_tich import PhanTich
from app.models.problem import Problem
from app.models.session import Session as SessionModel
from app.models.session import TrangThaiSession

# Tái sinh phân tích AI khi có thêm ngần này bài, hoặc đã quá ngần này ngày.
TAI_SINH_SAU_BAI = 5
TAI_SINH_SAU_NGAY = 7

# Số bài hoàn thành tối thiểu để coi là "đủ dữ liệu" cho phân tích đáng tin.
NGUONG_DU_LIEU = 8
# Mỗi nhóm cần tối thiểu bấy nhiêu bài hoàn thành mới xếp mạnh/yếu.
NGUONG_NHOM = 2

NHAN_LOAI = {"TN4PA": "Trắc nghiệm ABCD", "TNDS": "Đúng/Sai 4 ý", "TLN": "Trả lời ngắn"}


def _diem_thanh_thao(ty_le_hoan_thanh: float, diem_tb: float, goi_y_tb: float) -> int:
    """Điểm thành thạo 0–100 (minh bạch): chủ yếu theo điểm + tỉ lệ hoàn thành,
    trừ điểm nếu phụ thuộc nhiều vào gợi ý."""
    diem = 0.6 * diem_tb + 0.4 * ty_le_hoan_thanh
    phat = min(0.2, max(0.0, goi_y_tb) * 0.05)
    return round(max(0.0, min(1.0, diem - phat)) * 100)


def _phan_loai(mastery: int | None) -> str:
    if mastery is None:
        return "chua_du_lieu"
    if mastery >= 75:
        return "manh"
    if mastery >= 50:
        return "kha"
    return "can_cai_thien"


def _gom() -> dict:
    return {"so_phien": 0, "so_hoan_thanh": 0, "_diem": [], "_goi_y": [], "_tg": []}


def _ket_nhom(ten: str, g: dict, extra: dict | None = None) -> dict:
    htc = g["so_hoan_thanh"]
    ty_le = (htc / g["so_phien"]) if g["so_phien"] else 0.0
    diem_tb = (sum(g["_diem"]) / len(g["_diem"])) if g["_diem"] else 0.0
    goi_y_tb = (sum(g["_goi_y"]) / len(g["_goi_y"])) if g["_goi_y"] else 0.0
    tg_tb = round(sum(g["_tg"]) / len(g["_tg"])) if g["_tg"] else None
    mastery = _diem_thanh_thao(ty_le, diem_tb, goi_y_tb) if htc >= 1 else None
    row = {
        "ten": ten,
        "so_phien": g["so_phien"],
        "so_hoan_thanh": htc,
        "ty_le_hoan_thanh": round(ty_le * 100),
        "diem_thanh_thao": mastery,
        "goi_y_tb": round(goi_y_tb, 1),
        "thoi_gian_tb_giay": tg_tb,
        "nhan": _phan_loai(mastery),
    }
    if extra:
        row.update(extra)
    return row


def ho_so_nang_luc(db: Session, hoc_sinh_id: int) -> dict:
    """Hồ sơ năng lực + đề xuất theo luật cho 1 học sinh."""
    sessions = (
        db.query(SessionModel).filter(
            SessionModel.hoc_sinh_id == hoc_sinh_id,
            SessionModel.bi_an == False,  # noqa: E712
        ).all()
    )
    p_ids = {s.problem_id for s in sessions}
    problems = (
        {p.id: p for p in db.query(Problem).filter(Problem.id.in_(p_ids)).all()}
        if p_ids else {}
    )

    theo_cd: dict[str, dict] = {}
    theo_dang: dict[str, dict] = {}
    theo_loai: dict[str, dict] = {}
    dang_meta: dict[str, dict] = {}  # key dạng → {dang_id, chuyen_de}

    for s in sessions:
        p = problems.get(s.problem_id)
        if p is None:
            continue
        cd = p.chuyen_de or "(Chưa phân loại)"
        dang = f"{cd} › {p.dang.ten}" if p.dang else f"{cd} › (Chưa phân dạng)"
        dang_meta.setdefault(dang, {"dang_id": p.dang_id, "chuyen_de": p.chuyen_de})
        loai = p.loai_cau.value
        xong = s.trang_thai == TrangThaiSession.hoan_thanh

        for key, store in ((cd, theo_cd), (dang, theo_dang), (loai, theo_loai)):
            g = store.setdefault(key, _gom())
            g["so_phien"] += 1
            if xong:
                g["so_hoan_thanh"] += 1
                g["_diem"].append(s.diem if s.diem is not None else 1.0)
                g["_goi_y"].append(s.cap_goi_y_hien_tai or 0)
                if s.thoi_gian_giay is not None:
                    g["_tg"].append(s.thoi_gian_giay)

    ds_cd = sorted((_ket_nhom(k, v) for k, v in theo_cd.items()),
                   key=lambda r: (r["diem_thanh_thao"] is None, r["diem_thanh_thao"] or 0))
    ds_dang = sorted((_ket_nhom(k, v, dang_meta.get(k)) for k, v in theo_dang.items()),
                     key=lambda r: (r["diem_thanh_thao"] is None, r["diem_thanh_thao"] or 0))
    ds_loai = sorted(
        (_ket_nhom(NHAN_LOAI.get(k, k), v, {"loai": k}) for k, v in theo_loai.items()),
        key=lambda r: (r["diem_thanh_thao"] is None, r["diem_thanh_thao"] or 0),
    )

    tong_hoan_thanh = sum(1 for s in sessions if s.trang_thai == TrangThaiSession.hoan_thanh)
    du_lieu_du = tong_hoan_thanh >= NGUONG_DU_LIEU
    do_tin_cay = "cao" if tong_hoan_thanh >= NGUONG_DU_LIEU else (
        "trung_binh" if tong_hoan_thanh >= NGUONG_NHOM else "thap"
    )

    # Mạnh/yếu lấy ở cấp DẠNG (hành động rõ nhất), chỉ xét nhóm đủ bài.
    co_du = [r for r in ds_dang if r["so_hoan_thanh"] >= NGUONG_NHOM and r["nhan"] != "chua_du_lieu"]
    diem_yeu = [r for r in co_du if r["nhan"] == "can_cai_thien"][:3]
    diem_manh = [r for r in sorted(co_du, key=lambda r: -(r["diem_thanh_thao"] or 0))
                 if r["nhan"] == "manh"][:3]

    xu_huong = _xu_huong(sessions)

    de_xuat_hs, de_xuat_gv = _de_xuat_theo_luat(
        tong_hoan_thanh, diem_manh, diem_yeu, ds_loai, xu_huong
    )

    return {
        "tong_hoan_thanh": tong_hoan_thanh,
        "du_lieu_du": du_lieu_du,
        "do_tin_cay": do_tin_cay,
        "xu_huong": xu_huong,
        "diem_manh": diem_manh,
        "diem_yeu": diem_yeu,
        "theo_chuyen_de": ds_cd,
        "theo_dang": ds_dang,
        "theo_loai_cau": ds_loai,
        "de_xuat_hs": de_xuat_hs,
        "de_xuat_gv": de_xuat_gv,
    }


CAC_DO_KHO = ("de", "tb", "kho")


def ban_do_nang_luc(db: Session, hoc_sinh_ids: list[int]) -> dict:
    """C3 — Bản đồ năng lực (heatmap): ô = (chuyên đề × độ khó), giá trị = điểm
    thành thạo 0–100 (cùng công thức `_diem_thanh_thao` với hồ sơ năng lực).

    Nhận danh sách HS: 1 phần tử = bản đồ cá nhân; nhiều = bản đồ gộp cả lớp
    (dồn chung phiên của mọi HS vào từng ô rồi tính, không lấy trung bình của
    trung bình). Ô không có phiên hoàn thành → diem_thanh_thao = None
    ("chưa đủ dữ liệu" — khác với ô yếu).
    """
    if not hoc_sinh_ids:
        return {"cot": list(CAC_DO_KHO), "hang": []}
    sessions = (
        db.query(SessionModel).filter(
            SessionModel.hoc_sinh_id.in_(hoc_sinh_ids),
            SessionModel.bi_an == False,  # noqa: E712
        ).all()
    )
    p_ids = {s.problem_id for s in sessions}
    problems = (
        {p.id: p for p in db.query(Problem).filter(Problem.id.in_(p_ids)).all()}
        if p_ids else {}
    )

    o_gom: dict[tuple[str, str], dict] = {}
    for s in sessions:
        p = problems.get(s.problem_id)
        if p is None:
            continue
        cd = p.chuyen_de or "(Chưa phân loại)"
        khoa = (cd, p.do_kho.value)
        g = o_gom.setdefault(khoa, _gom())
        g["so_phien"] += 1
        if s.trang_thai == TrangThaiSession.hoan_thanh:
            g["so_hoan_thanh"] += 1
            g["_diem"].append(s.diem if s.diem is not None else 1.0)
            g["_goi_y"].append(s.cap_goi_y_hien_tai or 0)

    hang = []
    for cd in sorted({k[0] for k in o_gom}):
        o_theo_dk = {}
        for dk in CAC_DO_KHO:
            g = o_gom.get((cd, dk))
            if g is None:
                o_theo_dk[dk] = None
                continue
            ket = _ket_nhom(cd, g)
            o_theo_dk[dk] = {
                "so_phien": ket["so_phien"],
                "so_hoan_thanh": ket["so_hoan_thanh"],
                "diem_thanh_thao": ket["diem_thanh_thao"],
                "nhan": ket["nhan"],
            }
        hang.append({"chuyen_de": cd, "o": o_theo_dk})
    return {"cot": list(CAC_DO_KHO), "hang": hang}


def tong_hop_lop_gv(db: Session, gv_id: int) -> dict:
    """Tổng hợp điểm yếu chung của lớp + danh sách HS cần chú ý (cho GV)."""
    from app.models.lop import Lop
    from app.models.user import User, VaiTro

    lop_ids = [lop.id for lop in db.query(Lop).filter(Lop.gv_id == gv_id).all()]
    hs_list = (
        db.query(User).filter(User.vai_tro == VaiTro.hs, User.lop_id.in_(lop_ids)).all()
        if lop_ids else []
    )

    dang_tally: dict[str, dict] = {}  # ten dạng → {so_hs, _mastery[]}
    hs_can_chu_y: list[dict] = []
    so_co_dl = 0

    for hs in hs_list:
        ho_so = ho_so_nang_luc(db, hs.id)
        if ho_so["tong_hoan_thanh"] <= 0:
            continue
        so_co_dl += 1
        yeu = ho_so["diem_yeu"]
        for r in yeu:
            t = dang_tally.setdefault(r["ten"], {"ten": r["ten"], "so_hs": 0, "_m": []})
            t["so_hs"] += 1
            if r["diem_thanh_thao"] is not None:
                t["_m"].append(r["diem_thanh_thao"])
        if yeu or ho_so["xu_huong"] == "giam":
            hs_can_chu_y.append({
                "hoc_sinh_id": hs.id,
                "ho_ten": hs.ho_ten,
                "so_diem_yeu": len(yeu),
                "diem_yeu_ten": [r["ten"] for r in yeu],
                "xu_huong": ho_so["xu_huong"],
            })

    dang_yeu_chung = sorted(
        ({"ten": v["ten"], "so_hs": v["so_hs"],
          "mastery_tb": round(sum(v["_m"]) / len(v["_m"])) if v["_m"] else None}
         for v in dang_tally.values()),
        key=lambda x: (-x["so_hs"], x["mastery_tb"] if x["mastery_tb"] is not None else 999),
    )[:3]
    hs_can_chu_y.sort(key=lambda x: (-x["so_diem_yeu"], x["ho_ten"]))

    return {
        "so_hoc_sinh": len(hs_list),
        "so_hoc_sinh_co_du_lieu": so_co_dl,
        "dang_yeu_chung": dang_yeu_chung,
        "hoc_sinh_can_chu_y": hs_can_chu_y[:10],
    }


def _xu_huong(sessions) -> str:
    """Xu hướng tiến bộ dựa trên điểm các bài hoàn thành theo thời gian.

    Chia đôi (cũ/mới) theo thời điểm hoàn thành, so điểm trung bình.
    Trả: 'tien_bo' | 'giam' | 'on_dinh' | 'chua_du'.
    """
    xong = sorted(
        [s for s in sessions if s.trang_thai == TrangThaiSession.hoan_thanh and s.diem is not None],
        key=lambda s: s.cap_nhat_luc,
    )
    if len(xong) < 4:
        return "chua_du"
    nua = len(xong) // 2
    cu = [s.diem for s in xong[:nua]]
    moi = [s.diem for s in xong[nua:]]
    chenh = (sum(moi) / len(moi)) - (sum(cu) / len(cu))
    if chenh > 0.07:
        return "tien_bo"
    if chenh < -0.07:
        return "giam"
    return "on_dinh"


def _nen_cap_nhat(ho_so: dict, ban_cache: PhanTich | None) -> bool:
    """Có nên (tái) sinh phân tích không: có dữ liệu + (chưa có / bản tạm theo luật /
    thêm bài / quá hạn). Bản theo luật luôn nên thử nâng cấp lên bản AI."""
    if ho_so["tong_hoan_thanh"] <= 0:
        return False
    if ban_cache is None:
        return True
    if (ban_cache.nguon or "ai") == "luat":
        return True
    if ho_so["tong_hoan_thanh"] - (ban_cache.so_bai_luc_tao or 0) >= TAI_SINH_SAU_BAI:
        return True
    tao = ban_cache.tao_luc
    if tao is not None and tao.tzinfo is None:
        tao = tao.replace(tzinfo=timezone.utc)
    return bool(tao and datetime.now(timezone.utc) - tao > timedelta(days=TAI_SINH_SAU_NGAY))


def _phan_tich_theo_luat(ho_so: dict) -> dict | None:
    """Bản phân tích dự phòng TẤT ĐỊNH từ đề xuất theo luật (khi LLM không khả dụng:
    hết quota, lỗi mạng...). Đảm bảo nút luôn cho ra nội dung."""
    if ho_so.get("tong_hoan_thanh", 0) <= 0:
        return None
    hs = " ".join(ho_so.get("de_xuat_hs") or []).strip()
    gv = " ".join(ho_so.get("de_xuat_gv") or []).strip()
    if not hs and not gv:
        return None
    return {"cho_hoc_sinh": hs, "cho_giao_vien": gv}


def _ai_dict(ban: PhanTich | None) -> dict | None:
    if ban is None:
        return None
    return {
        "cho_hoc_sinh": ban.noi_dung_hs,
        "cho_giao_vien": ban.noi_dung_gv,
        "so_bai_luc_tao": ban.so_bai_luc_tao,
        "nguon": ban.nguon or "ai",
        "tao_luc": ban.tao_luc.isoformat() if ban.tao_luc else None,
    }


def lay_phan_tich(db: Session, hoc_sinh_id: int) -> dict:
    """Hồ sơ năng lực + bản phân tích đã cache (KHÔNG gọi LLM)."""
    from app.services.admin_service import lay_cau_hinh

    ho_so = ho_so_nang_luc(db, hoc_sinh_id)
    ban = db.query(PhanTich).filter(PhanTich.hoc_sinh_id == hoc_sinh_id).first()

    # Cache lỗi thời: được tạo từ nhiều bài hơn số bài hiện tại (sessions bị ẩn sau reset).
    if ban is not None and (ban.so_bai_luc_tao or 0) > ho_so["tong_hoan_thanh"]:
        db.delete(ban)
        db.commit()
        ban = None

    ho_so["ai"] = _ai_dict(ban)
    ho_so["nen_cap_nhat"] = _nen_cap_nhat(ho_so, ban)
    ho_so["tu_dong_phan_tich"] = bool(lay_cau_hinh(db).get("tu_dong_phan_tich", True))
    return ho_so


def _luu_ban(db, ban, hoc_sinh_id, ket, tong_ht, nguon) -> PhanTich:
    if ban is None:
        ban = PhanTich(hoc_sinh_id=hoc_sinh_id)
        db.add(ban)
    ban.noi_dung_hs = ket.get("cho_hoc_sinh") or ""
    ban.noi_dung_gv = ket.get("cho_giao_vien") or ""
    ban.so_bai_luc_tao = tong_ht
    ban.nguon = nguon
    ban.tao_luc = datetime.now(timezone.utc)
    db.commit()
    db.refresh(ban)
    return ban


def cap_nhat_phan_tich(db: Session, hoc_sinh_id: int, llm) -> dict:
    """(Tái) sinh phân tích từ hồ sơ năng lực rồi lưu cache. Ưu tiên LLM diễn giải;
    nếu LLM không khả dụng (hết quota/lỗi) → ghi bản dự phòng theo luật để nút LUÔN
    cho ra nội dung, và đánh dấu nguồn 'luat' để lần sau tự nâng cấp lên 'ai'."""
    ho_so = ho_so_nang_luc(db, hoc_sinh_id)
    ban = db.query(PhanTich).filter(PhanTich.hoc_sinh_id == hoc_sinh_id).first()
    tong_ht = ho_so["tong_hoan_thanh"]

    ket_ai = llm.phan_tich(ho_so) if tong_ht > 0 else None
    if ket_ai:
        ban = _luu_ban(db, ban, hoc_sinh_id, ket_ai, tong_ht, "ai")
        ai_kha_dung = True
    else:
        # LLM không cho kết quả → dùng bản theo luật (nếu chưa từng có bản 'ai').
        ket_luat = _phan_tich_theo_luat(ho_so)
        if ket_luat and (ban is None or (ban.nguon or "ai") == "luat"):
            ban = _luu_ban(db, ban, hoc_sinh_id, ket_luat, tong_ht, "luat")
        ai_kha_dung = False

    ho_so["ai"] = _ai_dict(ban)
    ho_so["nen_cap_nhat"] = _nen_cap_nhat(ho_so, ban)
    # Báo cho giao diện: lần này có tạo được bản AI mới không (False = đang dùng bản theo luật).
    ho_so["ai_kha_dung"] = ai_kha_dung
    return ho_so


def tai_sinh_neu_can(db: Session, hoc_sinh_id: int, llm) -> bool:
    """(Tái) sinh phân tích AI cho 1 HS NẾU đến hạn (thêm bài / quá ngày / chưa có).
    Trả True nếu thực sự tạo được bản AI mới."""
    ho_so = ho_so_nang_luc(db, hoc_sinh_id)
    ban = db.query(PhanTich).filter(PhanTich.hoc_sinh_id == hoc_sinh_id).first()
    if not _nen_cap_nhat(ho_so, ban):
        return False
    ket = cap_nhat_phan_tich(db, hoc_sinh_id, llm)
    return bool(ket.get("ai_kha_dung"))


def quet_tai_sinh(db: Session, llm) -> dict:
    """Quét toàn bộ học sinh, tái sinh phân tích AI cho ai đến hạn. Lỗi 1 HS không
    chặn các HS khác. Dùng cho lịch chạy nền."""
    from app.models.user import User, VaiTro

    hs_ids = [u.id for u in db.query(User).filter(User.vai_tro == VaiTro.hs).all()]
    da_cap_nhat = 0
    loi = 0
    for hid in hs_ids:
        try:
            if tai_sinh_neu_can(db, hid, llm):
                da_cap_nhat += 1
        except Exception:
            db.rollback()
            loi += 1
    return {"da_quet": len(hs_ids), "da_cap_nhat": da_cap_nhat, "loi": loi}


_XU_HUONG_HS = {
    "tien_bo": "Gần đây em đang TIẾN BỘ — cố gắng duy trì nhé! 🚀",
    "giam": "Gần đây kết quả hơi đi xuống — em đừng nản, ôn lại phần còn lúng túng nhé.",
}
_XU_HUONG_GV = {
    "tien_bo": "Xu hướng: đang tiến bộ.",
    "giam": "Xu hướng: kết quả gần đây đi xuống — nên quan tâm thêm.",
    "on_dinh": "Xu hướng: ổn định.",
}


def _de_xuat_theo_luat(tong_ht, diem_manh, diem_yeu, ds_loai,
                       xu_huong="chua_du") -> tuple[list[str], list[str]]:
    """Sinh câu đề xuất bằng LUẬT (tiếng Việt). Lớp LLM sẽ thay/bổ sung ở bước sau."""
    hs: list[str] = []
    gv: list[str] = []

    if tong_ht == 0:
        return (["Em hãy bắt đầu luyện một vài bài để hệ thống đưa ra nhận xét nhé."],
                ["Học sinh chưa hoàn thành bài nào — chưa đủ dữ liệu phân tích."])

    if xu_huong in _XU_HUONG_HS:
        hs.append(_XU_HUONG_HS[xu_huong])
    if xu_huong in _XU_HUONG_GV:
        gv.append(_XU_HUONG_GV[xu_huong])

    if tong_ht < NGUONG_DU_LIEU:
        hs.append(f"Em đã hoàn thành {tong_ht} bài. Luyện thêm để nhận xét chính xác hơn nhé.")
        gv.append(f"Mới {tong_ht} bài hoàn thành — số liệu còn ít, nhận định mang tính tham khảo.")

    for r in diem_manh:
        hs.append(f"Em làm tốt dạng «{r['ten']}» (thành thạo {r['diem_thanh_thao']}%). Giữ phong độ nhé!")
    if diem_manh:
        gv.append("Điểm mạnh: " + "; ".join(
            f"{r['ten']} ({r['diem_thanh_thao']}%)" for r in diem_manh))

    for r in diem_yeu:
        ly_do = []
        if r["goi_y_tb"] >= 1:
            ly_do.append("còn phụ thuộc gợi ý")
        if r["ty_le_hoan_thanh"] < 60:
            ly_do.append("tỉ lệ hoàn thành thấp")
        duoi = (" — " + ", ".join(ly_do)) if ly_do else ""
        hs.append(f"Nên luyện thêm dạng «{r['ten']}» (mới {r['diem_thanh_thao']}%){duoi}.")
    if diem_yeu:
        gv.append("Cần cải thiện: " + "; ".join(
            f"{r['ten']} ({r['diem_thanh_thao']}%)" for r in diem_yeu))
        gv.append("Đề xuất: giao thêm bài các dạng trên và theo sát trong giờ luyện.")

    # Loại câu yếu nhất (nếu có dữ liệu)
    loai_du = [r for r in ds_loai if r["nhan"] != "chua_du_lieu"]
    if loai_du:
        yeu_loai = loai_du[0]  # đã sắp tăng dần theo thành thạo
        if yeu_loai["nhan"] == "can_cai_thien":
            hs.append(f"Với câu «{yeu_loai['ten']}», em nên làm chậm và chắc từng bước hơn.")
            gv.append(f"Loại câu yếu nhất: {yeu_loai['ten']} ({yeu_loai['diem_thanh_thao']}%).")

    if not diem_yeu and tong_ht >= NGUONG_DU_LIEU:
        hs.append("Năng lực khá đồng đều — em có thể thử các bài mức khó hơn để nâng cao.")
        gv.append("Năng lực đồng đều; có thể nâng độ khó để thử thách học sinh.")

    return hs, gv
