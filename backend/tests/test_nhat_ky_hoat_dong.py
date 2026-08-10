"""Test cho Nhật ký hoạt động Ban giám khảo (GET /api/admin/nhat-ky-hoat-dong)."""

from datetime import datetime, timezone

from app.auth.security import hash_password
from app.models.danh_muc import ChuyenDe, Dang
from app.models.lop import Lop
from app.models.problem import Problem, TrangThaiDuyet
from app.models.session import Session as SessionModel
from app.models.session import TrangThaiSession
from app.models.solution_step import SolutionStep
from app.models.turn import Turn, VaiTroTurn
from app.models.user import User, VaiTro


def _login(client, dn):
    return client.post("/api/auth/login",
                       json={"dang_nhap": dn, "mat_khau": "password"}).json()["access_token"]


def _dt(s: str) -> datetime:
    return datetime.strptime(s, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)


def _seed_lop_demo(db):
    admin = User(vai_tro=VaiTro.admin, ho_ten="Quản trị", dang_nhap="admin",
                 mat_khau_hash=hash_password("password"))
    gvdemo = User(vai_tro=VaiTro.gv, ho_ten="GV Demo", dang_nhap="gvdemo",
                  mat_khau_hash=hash_password("password"),
                  tao_luc=_dt("2026-07-20 08:00:00"))
    db.add_all([admin, gvdemo])
    db.flush()

    lop = Lop(ten="Lớp Demo", gv_id=gvdemo.id)
    db.add(lop)
    db.flush()

    hs = User(vai_tro=VaiTro.hs, ho_ten="HS Demo", dang_nhap="hsdemo",
              mat_khau_hash=hash_password("password"), lop_id=lop.id,
              tao_luc=_dt("2026-07-30 09:00:00"))
    db.add(hs)
    db.flush()

    # Câu hỏi + chuyên đề + dạng của gvdemo, mốc thời gian kiểm soát được.
    cd = ChuyenDe(ten="Ứng dụng của đạo hàm", nguoi_tao_id=gvdemo.id,
                  tao_luc=_dt("2026-07-30 10:00:00"))
    db.add(cd)
    db.flush()
    dang = Dang(chuyen_de_id=cd.id, ten="Tính đơn điệu", nguoi_tao_id=gvdemo.id,
                tao_luc=_dt("2026-07-30 10:05:00"))
    db.add(dang)
    db.flush()

    p = Problem(chuyen_de="Ứng dụng của đạo hàm", dang_id=dang.id, loai_cau="TLN",
               do_kho="de", de_bai="Tìm x", loai_dap_an_nhap="gia_tri",
               trang_thai_duyet=TrangThaiDuyet.da_duyet, nguoi_tao_id=gvdemo.id,
               meta={"dap_an_cuoi": "2"}, tao_luc=_dt("2026-07-30 10:10:00"))
    db.add(p)
    db.flush()
    db.add(SolutionStep(problem_id=p.id, thu_tu=1, pham_vi="ca_bai", mo_ta="b1",
                        bieu_thuc_ket_qua="2", danh_sach_goi_y=["g1"]))
    db.flush()

    # 1 phiên đã hoàn thành của HS Demo, có 1 lượt hội thoại + 1 cờ.
    s = SessionModel(hoc_sinh_id=hs.id, problem_id=p.id,
                     trang_thai=TrangThaiSession.hoan_thanh, diem=1.0,
                     bat_dau_luc=_dt("2026-08-01 19:00:00"),
                     cap_nhat_luc=_dt("2026-08-01 19:05:00"))
    db.add(s)
    db.flush()
    db.add(Turn(session_id=s.id, vai_tro=VaiTroTurn.hoc_sinh, noi_dung="Em trả lời: $2$",
               thoi_diem=_dt("2026-08-01 19:04:00")))
    db.commit()

    return {"admin": admin, "gvdemo": gvdemo, "hs": hs, "lop": lop, "problem": p}


def _seed_gv_hs_khac(db):
    """1 GV + 1 HS THẬT, KHÔNG thuộc Lớp Demo — dùng để xác nhận không bị lẫn vào."""
    gv_that = User(vai_tro=VaiTro.gv, ho_ten="GV Thật", dang_nhap="gvthat",
                  mat_khau_hash=hash_password("password"),
                  tao_luc=_dt("2026-07-15 08:00:00"))
    db.add(gv_that)
    db.flush()
    lop_that = Lop(ten="12A9", gv_id=gv_that.id)
    db.add(lop_that)
    db.flush()
    hs_that = User(vai_tro=VaiTro.hs, ho_ten="HS Thật", dang_nhap="hsthat",
                  mat_khau_hash=hash_password("password"), lop_id=lop_that.id,
                  tao_luc=_dt("2026-07-16 08:00:00"))
    db.add(hs_that)
    db.commit()


def test_admin_xem_duoc_gv_hs_khong(db, client):
    _seed_lop_demo(db)
    for dn in ("gvdemo", "hsdemo"):
        h = {"Authorization": f"Bearer {_login(client, dn)}"}
        r = client.get("/api/admin/nhat-ky-hoat-dong", headers=h)
        assert r.status_code == 403


def test_gom_du_su_kien_va_khong_lan_du_lieu_ngoai_lop_demo(db, client):
    _seed_lop_demo(db)
    _seed_gv_hs_khac(db)
    h = {"Authorization": f"Bearer {_login(client, 'admin')}"}
    r = client.get("/api/admin/nhat-ky-hoat-dong", headers=h)
    assert r.status_code == 200
    data = r.json()
    assert data["lop_tim_thay"] is True
    assert data["lop_ten"] == "Lớp Demo"

    dang_nhaps = {row["dang_nhap"] for row in data["rows"] if row["dang_nhap"]}
    assert dang_nhaps <= {"gvdemo", "hsdemo"}
    assert "gvthat" not in dang_nhaps and "hsthat" not in dang_nhaps

    hanh_dongs = {row["hanh_dong"] for row in data["rows"]}
    assert "Tạo tài khoản" in hanh_dongs
    assert "Bắt đầu làm bài" in hanh_dongs
    assert "Hoàn thành bài" in hanh_dongs
    assert "Tạo câu hỏi" in hanh_dongs
    assert "Tạo chuyên đề" in hanh_dongs
    assert "Tạo dạng" in hanh_dongs
    # Mặc định chi_tiet=False → KHÔNG có lượt hội thoại trong danh sách.
    assert "Học sinh trả lời" not in hanh_dongs


def test_chi_tiet_bat_them_luot_hoi_thoai(db, client):
    _seed_lop_demo(db)
    h = {"Authorization": f"Bearer {_login(client, 'admin')}"}
    r = client.get("/api/admin/nhat-ky-hoat-dong?chi_tiet=true", headers=h)
    hanh_dongs = {row["hanh_dong"] for row in r.json()["rows"]}
    assert "Học sinh trả lời" in hanh_dongs


def test_sap_xep_moi_nhat_truoc(db, client):
    _seed_lop_demo(db)
    h = {"Authorization": f"Bearer {_login(client, 'admin')}"}
    r = client.get("/api/admin/nhat-ky-hoat-dong", headers=h)
    moc = [row["thoi_diem"] for row in r.json()["rows"]]
    assert moc == sorted(moc, reverse=True)


def test_loc_theo_khoang_ngay_khong_loi_va_dung_pham_vi(db, client):
    """Trước đây có rủi ro TypeError (so naive/aware) khi truyền tu_ngay/den_ngay — đây là
    test khóa hành vi đã sửa, không chỉ kiểm tra không lỗi mà còn đúng phạm vi lọc."""
    _seed_lop_demo(db)
    h = {"Authorization": f"Bearer {_login(client, 'admin')}"}

    # Chỉ lấy đúng ngày 2026-07-30 (tạo tài khoản HS + câu hỏi/chuyên đề/dạng) — KHÔNG có
    # phiên học (01/8) hay tạo GV (20/7).
    r = client.get(
        "/api/admin/nhat-ky-hoat-dong?tu_ngay=2026-07-30&den_ngay=2026-07-30", headers=h
    )
    assert r.status_code == 200
    rows = r.json()["rows"]
    assert len(rows) > 0
    hanh_dongs = {row["hanh_dong"] for row in rows}
    assert "Bắt đầu làm bài" not in hanh_dongs
    for row in rows:
        assert row["thoi_diem"].startswith("2026-07-30")


def test_khong_co_lop_demo_tra_ve_rong(db, client):
    admin = User(vai_tro=VaiTro.admin, ho_ten="Quản trị", dang_nhap="admin",
                mat_khau_hash=hash_password("password"))
    db.add(admin)
    db.commit()
    h = {"Authorization": f"Bearer {_login(client, 'admin')}"}
    r = client.get("/api/admin/nhat-ky-hoat-dong", headers=h)
    assert r.status_code == 200
    assert r.json() == {"rows": [], "tong": 0, "lop_tim_thay": False}
