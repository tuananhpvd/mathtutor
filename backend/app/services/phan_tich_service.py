"""
Phân tích năng lực học sinh (TẤT ĐỊNH — không gọi LLM).

Tính "hồ sơ năng lực" theo chuyên đề / dạng / loại câu từ lịch sử làm bài, rồi
đưa ra đề xuất theo LUẬT. Đây là Bước 1+2; lớp LLM diễn giải sẽ thêm ở bước sau.
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.phan_tich import PhanTich
from app.models.problem import Problem
from app.models.session import Session as SessionModel
from app.models.session import TrangThaiSession
from app.models.yeu_cau_tro_giup import YeuCauTroGiup

# Tái sinh phân tích AI khi có thêm ngần này bài, hoặc đã quá ngần này ngày.
TAI_SINH_SAU_BAI = 5
TAI_SINH_SAU_NGAY = 7

# Số bài hoàn thành tối thiểu để coi là "đủ dữ liệu" cho phân tích đáng tin.
NGUONG_DU_LIEU = 8
# Mỗi nhóm cần tối thiểu bấy nhiêu bài hoàn thành mới xếp mạnh/yếu.
NGUONG_NHOM = 2

# Số HS CÓ DỮ LIỆU tối thiểu trong một LỚP để tổng hợp cấp lớp được coi là đáng tin. Dưới
# ngưỡng này, FE phải hiện "chưa đủ dữ liệu" thay vì vẽ xếp hạng — thống kê tách theo lớp làm
# mẫu số nhỏ đi nhiều, rất dễ biến nhiễu thành "tín hiệu".
NGUONG_MAU_TOI_THIEU = 5

NHAN_LOAI = {"TN4PA": "Trắc nghiệm ABCD", "TNDS": "Đúng/Sai 4 ý", "TLN": "Trả lời ngắn"}

# Nhãn hiển thị TIẾNG VIỆT duy nhất cho từng mức "nhan" — nguồn CHUẨN cho mọi màn (Phân tích
# năng lực, Báo cáo phụ huynh...). FE không tự đặt nhãn riêng nữa để tránh lệch nhau
# (từng có nơi ghi "Mạnh", nơi ghi "Tốt" cho cùng nhãn "manh").
NHAN_HIEN_THI = {
    "manh": "Vững",
    "kha": "Ổn",
    "can_cai_thien": "Cần luyện thêm",
    "chua_du_lieu": "Chưa đủ dữ liệu",
}


def _diem_thanh_thao(ty_le_hoan_thanh: float, diem_chat_luong_tb: float, het_goi_y_tb: float) -> int:
    """Điểm thành thạo 0–100.

    `diem_chat_luong_tb`: trung bình tín hiệu CHẤT LƯỢNG làm bài của các phiên hoàn thành (lấy
    qua `_diem_xu_huong` — ưu tiên diem_qua_trinh, trừ dần theo số lần sai/không hiểu; phiên cũ
    chưa có thì fallback diem). Dùng tín hiệu này thay vì `diem` thô vì diem TN4PA/TLN hoàn
    thành LUÔN = 1.0 (chỉ TNDS có bậc thang) — nếu tính thẳng vào công thức thì gần như ai làm
    xong cũng được coi là thành thạo, bất kể loay hoay bao nhiêu.

    `ty_le_hoan_thanh`: trọng số PHỤ — hoàn thành bài là điều kiện cần nhưng không đủ để nói
    "thành thạo", nên chỉ chiếm 0.25 (trước đây 0.4).

    `het_goi_y_tb`: trung bình số lần CẠN gợi ý (so_lan_het_goi_y — không reset trong phiên,
    khác cap_goi_y_hien_tai vốn reset mỗi khi trả lời đúng) của các phiên hoàn thành. Phạt thêm
    nếu học sinh liên tục phải dùng hết bậc gợi ý cao nhất mới ra được bài.
    """
    diem = 0.75 * diem_chat_luong_tb + 0.25 * ty_le_hoan_thanh
    phat = min(0.15, max(0.0, het_goi_y_tb) * 0.3)
    return round(max(0.0, min(1.0, diem - phat)) * 100)


# Tỉ lệ hoàn thành dưới ngưỡng này thì KHÔNG được xếp "manh" dù điểm chất lượng cao — tránh
# 1-2 bài làm tốt che mất việc bỏ dở phần lớn bài đã bắt đầu (vd hoàn thành 2/7 = 29% nhưng
# 2 bài đó làm rất tốt vẫn không nên gắn "Vững"). Dùng CHUNG ngưỡng với câu ly_do ("hay bỏ dở
# giữa chừng") để nhãn và lời giải thích luôn khớp nhau.
NGUONG_TY_LE_KHOA_MANH = 0.6


def _phan_loai(mastery: int | None, ty_le_hoan_thanh: float = 1.0) -> str:
    if mastery is None:
        return "chua_du_lieu"
    if mastery >= 75:
        return "manh" if ty_le_hoan_thanh >= NGUONG_TY_LE_KHOA_MANH else "kha"
    if mastery >= 50:
        return "kha"
    return "can_cai_thien"


def _ly_do_diem(mastery: int | None, so_phien: int, ty_le: float, het_goi_y_tb: float) -> str:
    """Câu giải thích ngắn VÌ SAO ra mức điểm này — để nhìn vào là hiểu ngay, không phải đoán."""
    if mastery is None:
        if so_phien > 0:
            return "Đã bắt đầu nhưng chưa hoàn thành bài nào ở đây."
        return "Chưa có bài nào."
    kho_khan = []
    if het_goi_y_tb >= 1:
        kho_khan.append("còn cần nhiều gợi ý")
    if ty_le < 0.6:
        kho_khan.append("hay bỏ dở giữa chừng")
    if kho_khan:
        return "Còn " + " và ".join(kho_khan) + "."
    if mastery >= 75:
        return "Làm bài tốt, ít cần trợ giúp."
    return "Hoàn thành ổn, thỉnh thoảng vẫn cần gợi ý."


def _gom() -> dict:
    return {"so_phien": 0, "so_hoan_thanh": 0, "_diem": [], "_goi_y": [], "_het_goi_y_ct": [],
            "_tg": [], "het_goi_y": 0, "xem_ly_thuyet": 0, "nho_thay_co": 0}


def _ket_nhom(ten: str, g: dict, extra: dict | None = None) -> dict:
    htc = g["so_hoan_thanh"]
    ty_le = (htc / g["so_phien"]) if g["so_phien"] else 0.0
    diem_chat_luong_tb = (sum(g["_diem"]) / len(g["_diem"])) if g["_diem"] else 0.0
    goi_y_tb = (sum(g["_goi_y"]) / len(g["_goi_y"])) if g["_goi_y"] else 0.0
    het_goi_y_tb = (
        (sum(g["_het_goi_y_ct"]) / len(g["_het_goi_y_ct"])) if g["_het_goi_y_ct"] else 0.0
    )
    tg_tb = round(sum(g["_tg"]) / len(g["_tg"])) if g["_tg"] else None
    mastery = _diem_thanh_thao(ty_le, diem_chat_luong_tb, het_goi_y_tb) if htc >= 1 else None
    nhan = _phan_loai(mastery, ty_le)
    row = {
        "ten": ten,
        "so_phien": g["so_phien"],
        "so_hoan_thanh": htc,
        "ty_le_hoan_thanh": round(ty_le * 100),
        "diem_thanh_thao": mastery,
        "goi_y_tb": round(goi_y_tb, 1),
        "het_goi_y_tb": round(het_goi_y_tb, 1),
        "thoi_gian_tb_giay": tg_tb,
        "nhan": nhan,
        "nhan_hien_thi": NHAN_HIEN_THI[nhan],
        "ly_do": _ly_do_diem(mastery, g["so_phien"], ty_le, het_goi_y_tb),
        # Cột chẩn đoán — hiện cho GV thấy hành trình vật lộn: cạn gợi ý / tự xem lại lý
        # thuyết / nhờ thầy cô ở dạng này bao nhiêu lần (tính trên MỌI phiên, kể cả chưa
        # xong). Riêng "cạn gợi ý" của các phiên ĐÃ XONG cũng là một phần của công thức điểm
        # thành thạo ở trên (qua het_goi_y_tb) — không còn tách biệt hoàn toàn như trước.
        "so_lan_het_goi_y": g["het_goi_y"],
        "so_lan_xem_ly_thuyet": g["xem_ly_thuyet"],
        "so_lan_nho_thay_co": g["nho_thay_co"],
    }
    if extra:
        row.update(extra)
    return row


def ho_so_nang_luc(
    db: Session,
    hoc_sinh_id: int,
    tu_ngay: datetime | None = None,
    den_ngay: datetime | None = None,
) -> dict:
    """Hồ sơ năng lực + đề xuất theo luật cho 1 học sinh.

    tu_ngay/den_ngay (tùy chọn): chỉ tính các phiên BẮT ĐẦU trong khoảng — dùng cho
    báo cáo theo mốc thời gian. Không truyền → tính toàn bộ (hành vi cũ, các caller
    khác không đổi)."""
    q = db.query(SessionModel).filter(
        SessionModel.hoc_sinh_id == hoc_sinh_id,
        SessionModel.bi_an == False,  # noqa: E712
    )
    if tu_ngay is not None:
        q = q.filter(SessionModel.bat_dau_luc >= tu_ngay)
    if den_ngay is not None:
        q = q.filter(SessionModel.bat_dau_luc <= den_ngay)
    sessions = q.all()
    p_ids = {s.problem_id for s in sessions}
    problems = (
        {p.id: p for p in db.query(Problem).filter(Problem.id.in_(p_ids)).all()}
        if p_ids else {}
    )

    theo_cd: dict[str, dict] = {}
    theo_dang: dict[str, dict] = {}
    theo_loai: dict[str, dict] = {}
    dang_meta: dict[str, dict] = {}  # key dạng → {dang_id, chuyen_de}
    dang_phien: dict[str, list] = {}  # key dạng → các phiên (để tính xu hướng riêng từng dạng)

    # Số lần "Nhờ thầy/cô" theo từng phiên (1 query gộp) — để đếm chẩn đoán theo dạng.
    nho_rows = (
        db.query(YeuCauTroGiup.session_id, func.count(YeuCauTroGiup.id))
        .filter(YeuCauTroGiup.hoc_sinh_id == hoc_sinh_id)
        .group_by(YeuCauTroGiup.session_id)
        .all()
    )
    nho_map = {sid: int(n) for sid, n in nho_rows}

    for s in sessions:
        p = problems.get(s.problem_id)
        if p is None:
            continue
        cd = p.chuyen_de or "(Chưa phân loại)"
        dang = f"{cd} › {p.dang.ten}" if p.dang else f"{cd} › (Chưa phân dạng)"
        # "dang_ten" (tên dạng THUẦN, không ghép chuyên đề) — khác "ten" của row (luôn là chuỗi
        # "chuyên đề › dạng" ghép sẵn để hiển thị) — cần cho FE khớp đúng key group
        # chuyên_đề/dạng ở màn Giao nhiệm vụ (vd tự mở đúng dạng khi bấm "Giao bài ngay").
        dang_meta.setdefault(dang, {
            "dang_id": p.dang_id, "chuyen_de": p.chuyen_de,
            "dang_ten": p.dang.ten if p.dang else None,
        })
        dang_phien.setdefault(dang, []).append(s)
        loai = p.loai_cau.value
        xong = s.trang_thai == TrangThaiSession.hoan_thanh

        for key, store in ((cd, theo_cd), (dang, theo_dang), (loai, theo_loai)):
            g = store.setdefault(key, _gom())
            g["so_phien"] += 1
            # Tín hiệu vật lộn tính cho MỌI phiên (kể cả chưa hoàn thành) — vì khó khăn xảy ra
            # bất kể cuối cùng có xong hay không.
            g["het_goi_y"] += s.so_lan_het_goi_y or 0
            g["xem_ly_thuyet"] += s.so_lan_xem_ly_thuyet or 0
            g["nho_thay_co"] += nho_map.get(s.id, 0)
            if xong:
                g["so_hoan_thanh"] += 1
                chat_luong = _diem_xu_huong(s)
                g["_diem"].append(chat_luong if chat_luong is not None else 1.0)
                g["_goi_y"].append(s.cap_goi_y_hien_tai or 0)
                g["_het_goi_y_ct"].append(s.so_lan_het_goi_y or 0)
                if s.thoi_gian_giay is not None:
                    g["_tg"].append(s.thoi_gian_giay)

    ds_cd = sorted((_ket_nhom(k, v) for k, v in theo_cd.items()),
                   key=lambda r: (r["diem_thanh_thao"] is None, r["diem_thanh_thao"] or 0))
    ds_dang = sorted((_ket_nhom(k, v, dang_meta.get(k)) for k, v in theo_dang.items()),
                     key=lambda r: (r["diem_thanh_thao"] is None, r["diem_thanh_thao"] or 0))
    for r in ds_dang:
        # Xu hướng riêng của từng dạng (cần ≥4 bài hoàn thành trong dạng, không thì 'chua_du')
        r["xu_huong"] = _xu_huong(dang_phien.get(r["ten"], []))
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
        "so_phien": len(sessions),
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
            chat_luong = _diem_xu_huong(s)
            g["_diem"].append(chat_luong if chat_luong is not None else 1.0)
            g["_goi_y"].append(s.cap_goi_y_hien_tai or 0)
            g["_het_goi_y_ct"].append(s.so_lan_het_goi_y or 0)

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


def tong_hop_lop_gv(db: Session, gv_id: int, lop_id: int | None = None) -> dict:
    """Tổng hợp điểm yếu chung của MỘT lớp + danh sách HS cần chú ý (cho GV).

    `lop_id` có giá trị → CHỈ lớp đó (mặc định của thống kê: gộp nhiều lớp làm chìm khác biệt
    giữa các lớp). None → mọi lớp GV phụ trách (chỉ dùng khi cố ý gộp).

    Kèm `so_mau`/`du_mau` để tầng hiển thị KHÔNG xếp hạng trên mẫu quá nhỏ — cắt theo lớp làm
    mẫu số tụt nhanh, vài lượt làm cũng ra được con số trông rất "báo động" nhưng vô nghĩa.
    """
    from app.models.lop import Lop
    from app.models.user import User, VaiTro

    q_lop = db.query(Lop).filter(Lop.gv_id == gv_id)
    if lop_id is not None:
        q_lop = q_lop.filter(Lop.id == lop_id)
    lop_ids = [lop.id for lop in q_lop.all()]
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
          "so_mau": len(v["_m"]),
          "mastery_tb": round(sum(v["_m"]) / len(v["_m"])) if v["_m"] else None}
         for v in dang_tally.values()),
        key=lambda x: (-x["so_hs"], x["mastery_tb"] if x["mastery_tb"] is not None else 999),
    )[:3]
    hs_can_chu_y.sort(key=lambda x: (-x["so_diem_yeu"], x["ho_ten"]))

    return {
        "so_hoc_sinh": len(hs_list),
        "so_hoc_sinh_co_du_lieu": so_co_dl,
        # du_mau=False → FE hiện "chưa đủ dữ liệu", KHÔNG vẽ xếp hạng "dạng yếu chung".
        "nguong_mau": NGUONG_MAU_TOI_THIEU,
        "du_mau": so_co_dl >= NGUONG_MAU_TOI_THIEU,
        "dang_yeu_chung": dang_yeu_chung,
        "hoc_sinh_can_chu_y": hs_can_chu_y[:10],
    }


# Chống spam: mỗi GV chỉ nhận 1 thông báo "cần chú ý" trong ngần này ngày (dù lịch nền chạy
# thường xuyên hơn) — dedup theo thông báo digest gần nhất, KHÔNG cần cột trạng thái riêng.
NHAC_GV_MOI_N_NGAY = 7
_LIEN_KET_DIGEST = "tien_bo"  # bấm thông báo → mở trang Tiến bộ học sinh (GiaoVienApp)
_SO_TEN_HIEN = 5  # số tên HS hiện thẳng trong nội dung, còn lại rút gọn "…"


def _da_nhac_gan_day(db: Session, gv_id: int, lop_id: int | None = None) -> bool:
    """GV này đã nhận digest điểm yếu CỦA LỚP NÀY trong NHAC_GV_MOI_N_NGAY ngày gần nhất chưa.

    Dedup theo TỪNG LỚP (`lien_ket_id=lop_id`): digest nay tách theo lớp nên nếu dedup theo GV
    như trước thì lớp gửi đầu tiên sẽ chặn mất digest của các lớp còn lại trong cùng tuần.
    """
    from app.models.thong_bao import ThongBao

    moc = datetime.now(timezone.utc) - timedelta(days=NHAC_GV_MOI_N_NGAY)
    q = db.query(ThongBao.id).filter(
        ThongBao.nguoi_nhan_id == gv_id,
        ThongBao.lien_ket_loai == _LIEN_KET_DIGEST,
        ThongBao.tao_luc >= moc,
    )
    if lop_id is not None:
        q = q.filter(ThongBao.lien_ket_id == lop_id)
    return q.first() is not None


def _noi_dung_nhac(hs_can_chu_y: list[dict], dang_yeu_chung: list[dict]) -> str:
    ten = [h["ho_ten"] for h in hs_can_chu_y]
    hien = ", ".join(ten[:_SO_TEN_HIEN])
    if len(ten) > _SO_TEN_HIEN:
        hien += f" và {len(ten) - _SO_TEN_HIEN} em khác"
    nd = f"{len(ten)} học sinh cần chú ý: {hien}."
    if dang_yeu_chung:
        nd += f" Dạng cả lớp còn yếu nhất: {dang_yeu_chung[0]['ten']}."
    nd += " Bấm để xem chi tiết ở Tiến bộ học sinh."
    return nd


def so_sanh_cac_lop_gv(db: Session, gv_id: int) -> list[dict]:
    """MỖI LỚP một dòng trên CÙNG bộ chỉ số — thay cho việc trộn mọi lớp thành một con số.

    Đây là câu trả lời đúng cho nhu cầu "nhìn nhiều lớp": vẫn so sánh được lớp nào đang đuối,
    nhưng không làm chìm khác biệt giữa các lớp như khi gộp. Kèm `du_mau` để không so sánh
    trên lớp còn quá ít dữ liệu.
    """
    from app.models.lop import Lop

    ket = []
    for lop in db.query(Lop).filter(Lop.gv_id == gv_id).order_by(Lop.ten).all():
        th = tong_hop_lop_gv(db, gv_id, lop.id)
        ket.append({
            "lop_id": lop.id,
            "lop_ten": lop.ten,
            "so_hoc_sinh": th["so_hoc_sinh"],
            "so_hoc_sinh_co_du_lieu": th["so_hoc_sinh_co_du_lieu"],
            "du_mau": th["du_mau"],
            "so_hoc_sinh_can_chu_y": len(th["hoc_sinh_can_chu_y"]),
            "dang_yeu_dau": (th["dang_yeu_chung"][0]["ten"] if th["dang_yeu_chung"] else None),
        })
    return ket


def day_nhac_diem_yeu_tuan(db: Session) -> dict:
    """Chủ động đẩy cho từng GV 1 thông báo tuần "N học sinh cần chú ý" (tất định, KHÔNG gọi
    LLM). Chỉ gửi khi lớp CÓ HS cần chú ý và GV chưa nhận trong NHAC_GV_MOI_N_NGAY ngày. Lỗi
    1 GV không chặn GV khác. Dùng cho lịch nền (chạy độc lập với tu_dong_phan_tich)."""
    from app.models.lop import Lop
    from app.models.thong_bao import LoaiThongBao
    from app.models.user import User, VaiTro
    from app.services import thong_bao_service

    gv_ids = [u.id for u in db.query(User).filter(User.vai_tro == VaiTro.gv).all()]
    da_gui = bo_qua = loi = 0
    for gv_id in gv_ids:
        # MỖI LỚP một thông báo riêng: gộp mọi lớp vào 1 digest làm GV không biết em nào thuộc
        # lớp nào, và lớp đông lấn át lớp nhỏ trong danh sách "cần chú ý".
        for lop in db.query(Lop).filter(Lop.gv_id == gv_id).all():
            try:
                if _da_nhac_gan_day(db, gv_id, lop.id):
                    bo_qua += 1
                    continue
                tong_hop = tong_hop_lop_gv(db, gv_id, lop.id)
                can_chu_y = tong_hop["hoc_sinh_can_chu_y"]
                if not can_chu_y:
                    bo_qua += 1
                    continue
                thong_bao_service.tao(
                    db,
                    nguoi_nhan_id=gv_id,
                    noi_dung=_noi_dung_nhac(can_chu_y, tong_hop["dang_yeu_chung"]),
                    loai=LoaiThongBao.he_thong,
                    tieu_de=f"Lớp {lop.ten}: học sinh cần chú ý tuần này",
                    lien_ket_loai=_LIEN_KET_DIGEST,
                    lien_ket_id=lop.id,
                )
                da_gui += 1
            except Exception:
                db.rollback()
                loi += 1
    return {"so_gv": len(gv_ids), "da_gui": da_gui, "bo_qua": bo_qua, "loi": loi}


def _diem_xu_huong(s) -> float | None:
    """Giá trị dùng để đo xu hướng của 1 phiên hoàn thành.

    Ưu tiên `diem_qua_trinh` (0-1, trừ dần theo số lần sai + số lần cần gợi ý) vì `diem`
    của TLN/TN4PA hoàn thành luôn = 1.0 (chỉ TNDS có bậc thang) — so theo `diem` thì xu
    hướng gần như "mù". Phiên cũ chưa có diem_qua_trinh → fallback `diem` (cùng thang 0-1)."""
    if s.diem_qua_trinh is not None:
        return s.diem_qua_trinh
    return s.diem


def _xu_huong(sessions) -> str:
    """Xu hướng tiến bộ dựa trên ĐIỂM QUÁ TRÌNH các bài hoàn thành theo thời gian
    (ít sai hơn / ít cần gợi ý hơn = tiến bộ, kể cả khi bài nào cũng làm xong).

    Chia đôi (cũ/mới) theo thời điểm hoàn thành, so trung bình.
    Trả: 'tien_bo' | 'giam' | 'on_dinh' | 'chua_du'.
    """
    xong = sorted(
        [s for s in sessions
         if s.trang_thai == TrangThaiSession.hoan_thanh and _diem_xu_huong(s) is not None],
        key=lambda s: s.cap_nhat_luc,
    )
    if len(xong) < 4:
        return "chua_du"
    nua = len(xong) // 2
    cu = [_diem_xu_huong(s) for s in xong[:nua]]
    moi = [_diem_xu_huong(s) for s in xong[nua:]]
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
        if r["het_goi_y_tb"] >= 1:
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
