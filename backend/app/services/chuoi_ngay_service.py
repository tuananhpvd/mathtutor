"""
C1 — Chuỗi ngày học + cột mốc nhẹ.
Streak: đếm ngày liên tiếp có hoạt động học (bat tu hom nay hoac hom qua, lui lai).
Cột mốc: ngưỡng số bài hoàn thành hoặc chuỗi ngày đủ → trao mốc + báo HS.
"""

from datetime import date, datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.cot_moc import CotMoc
from app.models.session import Session as SessionModel
from app.models.session import TrangThaiSession

DINH_NGHIA_COT_MOC: list[dict] = [
    {
        "loai": "bai_dau_tien",
        "tieu_de": "🎯 Bài đầu tiên!",
        "mo_ta": "Em đã hoàn thành bài học đầu tiên. Khởi đầu tuyệt vời!",
        "nguong_bai": 1,
    },
    {
        "loai": "bai_thu_5",
        "tieu_de": "⭐ 5 bài hoàn thành!",
        "mo_ta": "Em đã hoàn thành 5 bài học. Tiếp tục cố gắng nhé!",
        "nguong_bai": 5,
    },
    {
        "loai": "bai_thu_10",
        "tieu_de": "🌟 10 bài hoàn thành!",
        "mo_ta": "Em đã hoàn thành 10 bài học. Đang tiến bộ rất tốt!",
        "nguong_bai": 10,
    },
    {
        "loai": "bai_thu_25",
        "tieu_de": "💪 25 bài hoàn thành!",
        "mo_ta": "Kiên trì! Em đã hoàn thành 25 bài học.",
        "nguong_bai": 25,
    },
    {
        "loai": "bai_thu_50",
        "tieu_de": "🏆 50 bài hoàn thành!",
        "mo_ta": "Xuất sắc! Em đã hoàn thành 50 bài học. Thật đáng khen!",
        "nguong_bai": 50,
    },
    {
        "loai": "chuoi_3_ngay",
        "tieu_de": "🔥 3 ngày liên tiếp!",
        "mo_ta": "Em học đều đặn 3 ngày liên tiếp rồi. Giữ vững nhé!",
        "nguong_chuoi": 3,
    },
    {
        "loai": "chuoi_7_ngay",
        "tieu_de": "🔥🔥 7 ngày liên tiếp!",
        "mo_ta": "Một tuần học không nghỉ! Thật tuyệt vời!",
        "nguong_chuoi": 7,
    },
    {
        "loai": "chuoi_14_ngay",
        "tieu_de": "🏅 14 ngày liên tiếp!",
        "mo_ta": "Hai tuần kiên trì! Em rất đáng khen ngợi!",
        "nguong_chuoi": 14,
    },
]


def tinh_chuoi_ngay(db: Session, hs_id: int) -> int:
    """Đếm chuỗi ngày liên tiếp có hoạt động học (bất kỳ phiên nào, không bị ẩn).
    Chuỗi tính từ hôm nay hoặc hôm qua (để không bị đứt khi chưa học hôm nay)."""
    rows = (
        db.query(SessionModel.cap_nhat_luc)
        .filter(
            SessionModel.hoc_sinh_id == hs_id,
            SessionModel.bi_an == False,  # noqa: E712
        )
        .all()
    )
    if not rows:
        return 0

    ngay_hoc: set[date] = set()
    for (dt,) in rows:
        if dt is not None:
            ngay_hoc.add(dt.date() if hasattr(dt, "date") else dt)

    # Tính "hôm nay" theo UTC cho khớp cách lưu cap_nhat_luc (datetime.now(timezone.utc)).
    # Nếu dùng date.today() (giờ địa phương) sẽ lệch múi giờ vào rạng sáng → streak sai.
    hom_nay = datetime.now(timezone.utc).date()
    hom_qua = hom_nay - timedelta(days=1)

    if hom_nay in ngay_hoc:
        ngay_kiem = hom_nay
    elif hom_qua in ngay_hoc:
        ngay_kiem = hom_qua
    else:
        return 0

    chuoi = 0
    while ngay_kiem in ngay_hoc:
        chuoi += 1
        ngay_kiem -= timedelta(days=1)
    return chuoi


def dem_ngay_hoc(db: Session, hs_id: int) -> int:
    """Tổng SỐ NGÀY (distinct) HS có hoạt động học — khác chuỗi liên tiếp (tinh_chuoi_ngay).
    Dùng cho lời chào trang chủ 'Em đã học được X ngày, trong đó có Y ngày liên tiếp'."""
    rows = (
        db.query(SessionModel.cap_nhat_luc)
        .filter(
            SessionModel.hoc_sinh_id == hs_id,
            SessionModel.bi_an == False,  # noqa: E712
        )
        .all()
    )
    ngay_hoc: set[date] = set()
    for (dt,) in rows:
        if dt is not None:
            ngay_hoc.add(dt.date() if hasattr(dt, "date") else dt)
    return len(ngay_hoc)


def dem_bai_hoan_thanh(db: Session, hs_id: int) -> int:
    return (
        db.query(SessionModel)
        .filter(
            SessionModel.hoc_sinh_id == hs_id,
            SessionModel.bi_an == False,  # noqa: E712
            SessionModel.trang_thai == TrangThaiSession.hoan_thanh,
        )
        .count()
    )


def kiem_tra_va_cap_nhat_cot_moc(db: Session, hs_id: int) -> None:
    """Sau khi HS hoàn thành bài, kiểm tra và trao cột mốc mới (nếu đủ điều kiện).
    Gọi trong cùng transaction — không commit lẻ."""
    tong_bai = dem_bai_hoan_thanh(db, hs_id)
    chuoi = tinh_chuoi_ngay(db, hs_id)

    da_dat = {
        r.loai
        for r in db.query(CotMoc.loai).filter(CotMoc.hoc_sinh_id == hs_id).all()
    }

    for m in DINH_NGHIA_COT_MOC:
        if m["loai"] in da_dat:
            continue
        dat = (
            ("nguong_bai" in m and tong_bai >= m["nguong_bai"])
            or ("nguong_chuoi" in m and chuoi >= m["nguong_chuoi"])
        )
        if not dat:
            continue

        db.add(CotMoc(
            hoc_sinh_id=hs_id,
            loai=m["loai"],
            tieu_de=m["tieu_de"],
            mo_ta=m["mo_ta"],
        ))
        db.flush()  # hiển thị ngay trong session để tránh trao trùng nếu gọi lại trong cùng tx
        da_dat.add(m["loai"])
        from app.models.thong_bao import LoaiThongBao, ThongBao
        db.add(ThongBao(
            nguoi_nhan_id=hs_id,
            loai=LoaiThongBao.he_thong,
            tieu_de=m["tieu_de"],
            noi_dung=m["mo_ta"],
        ))


def ho_so_chuoi_va_moc(db: Session, hs_id: int) -> dict:
    chuoi = tinh_chuoi_ngay(db, hs_id)
    so_ngay = dem_ngay_hoc(db, hs_id)
    tong_bai = dem_bai_hoan_thanh(db, hs_id)

    cot_moc_list = (
        db.query(CotMoc)
        .filter(CotMoc.hoc_sinh_id == hs_id)
        .order_by(CotMoc.dat_luc.desc())
        .all()
    )

    return {
        "chuoi_ngay": chuoi,
        "so_ngay_hoc": so_ngay,
        "tong_bai_hoan_thanh": tong_bai,
        "cot_moc_da_dat": [
            {
                "loai": m.loai,
                "tieu_de": m.tieu_de,
                "mo_ta": m.mo_ta,
                "dat_luc": m.dat_luc.isoformat() if m.dat_luc else None,
            }
            for m in cot_moc_list
        ],
    }
