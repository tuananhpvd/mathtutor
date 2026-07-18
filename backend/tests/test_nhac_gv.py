"""Chủ động nhắc GV mỗi tuần "N học sinh cần chú ý" (day_nhac_diem_yeu_tuan).

Tạo phiên hoàn thành ĐIỂM THẤP trực tiếp qua ORM để HS bị xếp dạng yếu (tất định, không
qua luồng HTTP), rồi kiểm: gửi đúng 1 thông báo/GV, dedup 7 ngày, không gửi khi lớp không
có HS cần chú ý."""

from datetime import datetime, timedelta, timezone

from app.auth.security import hash_password
from app.models.danh_muc import ChuyenDe, Dang
from app.models.lop import Lop
from app.models.problem import Problem, TrangThaiDuyet
from app.models.session import Session as SessionModel
from app.models.session import TrangThaiSession
from app.models.thong_bao import ThongBao
from app.models.user import User, VaiTro
from app.services.phan_tich_service import day_nhac_diem_yeu_tuan


def _bai(db, dang_id, nguoi_tao_id):
    p = Problem(
        chuyen_de="Khảo sát hàm số", dang_id=dang_id, loai_cau="TNDS", do_kho="tb",
        de_bai="Xét tính đúng/sai.", loai_dap_an_nhap="dung_sai_4y",
        trang_thai_duyet=TrangThaiDuyet.da_duyet, nguoi_tao_id=nguoi_tao_id,
        meta={"y": [{"ky_hieu": k, "noi_dung_y": k, "dap_an": "Dung"} for k in "abcd"]},
    )
    db.add(p)
    db.flush()
    return p


def _phien_yeu(db, hs_id, problem_id, diem=0.1):
    """Phiên HOÀN THÀNH điểm thấp → kéo điểm thành thạo của dạng xuống 'cần cải thiện'."""
    db.add(SessionModel(
        hoc_sinh_id=hs_id, problem_id=problem_id,
        trang_thai=TrangThaiSession.hoan_thanh, diem=diem, thoi_gian_giay=120,
    ))


def _lop_gv_hs(db, gv_dn, hs_dn):
    lop = Lop(ten=f"Lop-{gv_dn}")
    db.add(lop)
    db.flush()
    gv = User(vai_tro=VaiTro.gv, ho_ten=f"GV {gv_dn}", dang_nhap=gv_dn,
              mat_khau_hash=hash_password("password"))
    db.add(gv)
    db.flush()
    lop.gv_id = gv.id
    hs = User(vai_tro=VaiTro.hs, ho_ten=f"HS {hs_dn}", dang_nhap=hs_dn,
              mat_khau_hash=hash_password("password"), lop_id=lop.id)
    db.add(hs)
    db.flush()
    return gv, hs


def _dang(db):
    cd = ChuyenDe(ten="Khảo sát hàm số", thu_tu=1)
    db.add(cd)
    db.flush()
    d = Dang(chuyen_de_id=cd.id, ten="Tìm cực trị", thu_tu=1)
    db.add(d)
    db.flush()
    return d


def _dem_nhac(db, gv_id):
    return (
        db.query(ThongBao)
        .filter(ThongBao.nguoi_nhan_id == gv_id, ThongBao.lien_ket_loai == "tien_bo")
        .count()
    )


def test_nhac_gv_khi_co_hs_can_chu_y(db):
    gv, hs = _lop_gv_hs(db, "gv1", "hs1")
    d = _dang(db)
    for _ in range(2):  # >= NGUONG_NHOM (2) bài hoàn thành cùng dạng, điểm thấp → dạng yếu
        p = _bai(db, d.id, gv.id)
        _phien_yeu(db, hs.id, p.id)
    db.commit()

    ket = day_nhac_diem_yeu_tuan(db)
    assert ket["da_gui"] == 1
    assert _dem_nhac(db, gv.id) == 1

    tb = db.query(ThongBao).filter(ThongBao.nguoi_nhan_id == gv.id).first()
    assert "cần chú ý" in tb.noi_dung
    assert tb.lien_ket_loai == "tien_bo"
    assert hs.ho_ten in tb.noi_dung


def test_dedup_khong_gui_lai_trong_7_ngay(db):
    gv, hs = _lop_gv_hs(db, "gv2", "hs2")
    d = _dang(db)
    for _ in range(2):
        p = _bai(db, d.id, gv.id)
        _phien_yeu(db, hs.id, p.id)
    db.commit()

    assert day_nhac_diem_yeu_tuan(db)["da_gui"] == 1
    # Gọi lại ngay → dedup, KHÔNG tạo thêm
    assert day_nhac_diem_yeu_tuan(db)["da_gui"] == 0
    assert _dem_nhac(db, gv.id) == 1


def test_gui_lai_sau_7_ngay(db):
    gv, hs = _lop_gv_hs(db, "gv3", "hs3")
    d = _dang(db)
    for _ in range(2):
        p = _bai(db, d.id, gv.id)
        _phien_yeu(db, hs.id, p.id)
    db.commit()

    assert day_nhac_diem_yeu_tuan(db)["da_gui"] == 1
    # Đẩy thông báo cũ về QUÁ 7 ngày trước → được nhắc lại
    tb = db.query(ThongBao).filter(ThongBao.nguoi_nhan_id == gv.id).first()
    tb.tao_luc = datetime.now(timezone.utc) - timedelta(days=8)
    db.commit()
    assert day_nhac_diem_yeu_tuan(db)["da_gui"] == 1
    assert _dem_nhac(db, gv.id) == 2


def test_khong_gui_khi_khong_co_hs_can_chu_y(db):
    # GV có HS nhưng HS chưa hoàn thành bài nào → không có điểm yếu → không nhắc
    gv, hs = _lop_gv_hs(db, "gv4", "hs4")
    db.commit()
    ket = day_nhac_diem_yeu_tuan(db)
    assert ket["da_gui"] == 0
    assert _dem_nhac(db, gv.id) == 0
