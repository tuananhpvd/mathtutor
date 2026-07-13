"""Regression IDOR — POST /api/sessions PHẢI kiểm quyền truy cập bài GIỐNG HỆT
GET /api/problems/{id} (bất biến "GV chỉ thấy lớp mình", CLAUDE.md mục 3).

Trước khi vá, `tao_phien_moi` chỉ kiểm bài 'đã duyệt' — HS đoán được problem_id của
bài GV/lớp khác (hoặc bài đã bị ẩn) vẫn tạo được phiên và làm bài. Bộ test này canh
gác: chỉ bài của GV chủ nhiệm HOẶC được giao nhiệm vụ, và không bị ẩn, mới tạo phiên."""

from app.auth.security import hash_password
from app.models.lop import Lop
from app.models.nhiem_vu import NhiemVu, NhiemVuBai, NhiemVuHocSinh
from app.models.problem import Problem, TrangThaiDuyet
from app.models.solution_step import SolutionStep
from app.models.user import User, VaiTro


def _login(client, dn):
    return client.post("/api/auth/login",
                       json={"dang_nhap": dn, "mat_khau": "pass"}).json()["access_token"]


def _h(tok):
    return {"Authorization": f"Bearer {tok}"}


def _bai(db, nguoi_tao_id, *, bi_an=False, duyet=True):
    p = Problem(
        chuyen_de="Test", loai_cau="TLN", do_kho="tb", de_bai="Tìm x.",
        loai_dap_an_nhap="gia_tri",
        trang_thai_duyet=TrangThaiDuyet.da_duyet if duyet else TrangThaiDuyet.cho_duyet,
        nguoi_tao_id=nguoi_tao_id, bi_an=bi_an, meta={"dap_an_cuoi": "5"},
    )
    db.add(p)
    db.flush()
    db.add(SolutionStep(problem_id=p.id, thu_tu=1, pham_vi="ca_bai",
                        mo_ta="b1", bieu_thuc_ket_qua="5", danh_sach_goi_y=["g1", "g2"]))
    return p


def _seed(db):
    """gv1 chủ nhiệm lớp của hs1; gv2 là GV khác không liên quan."""
    gv1 = User(vai_tro=VaiTro.gv, ho_ten="GV1", dang_nhap="gv1",
               mat_khau_hash=hash_password("pass"))
    gv2 = User(vai_tro=VaiTro.gv, ho_ten="GV2", dang_nhap="gv2",
               mat_khau_hash=hash_password("pass"))
    db.add_all([gv1, gv2])
    db.flush()
    lop1 = Lop(ten="12A1", gv_id=gv1.id)
    db.add(lop1)
    db.flush()
    hs1 = User(vai_tro=VaiTro.hs, ho_ten="HS1", dang_nhap="hs1",
               mat_khau_hash=hash_password("pass"), lop_id=lop1.id)
    db.add(hs1)
    db.flush()
    p_gv1 = _bai(db, gv1.id)                       # bài GV chủ nhiệm → HS được làm
    p_gv2 = _bai(db, gv2.id)                       # bài GV khác đã duyệt → CHẶN
    p_gv1_an = _bai(db, gv1.id, bi_an=True)        # bài GV chủ nhiệm nhưng bị ẩn → CHẶN
    p_gv2_giao = _bai(db, gv2.id)                  # bài GV khác NHƯNG được giao nhiệm vụ → cho
    db.commit()

    # Giao p_gv2_giao cho hs1 qua nhiệm vụ
    nv = NhiemVu(gv_id=gv2.id, tieu_de="Luyện tập")
    db.add(nv)
    db.flush()
    db.add(NhiemVuBai(nhiem_vu_id=nv.id, problem_id=p_gv2_giao.id))
    db.add(NhiemVuHocSinh(nhiem_vu_id=nv.id, hoc_sinh_id=hs1.id))
    db.commit()
    return hs1, p_gv1, p_gv2, p_gv1_an, p_gv2_giao


def _tao_phien(client, tok, pid):
    return client.post("/api/sessions", json={"problem_id": pid}, headers=_h(tok))


def test_hs_tao_phien_bai_cua_minh_ok(db, client):
    hs1, p_gv1, *_ = _seed(db)
    r = _tao_phien(client, _login(client, "hs1"), p_gv1.id)
    assert r.status_code == 200, r.text


def test_hs_khong_tao_phien_bai_gv_khac(db, client):
    hs1, p_gv1, p_gv2, *_ = _seed(db)
    r = _tao_phien(client, _login(client, "hs1"), p_gv2.id)
    assert r.status_code == 404


def test_hs_khong_tao_phien_bai_bi_an(db, client):
    hs1, p_gv1, p_gv2, p_gv1_an, _ = _seed(db)
    r = _tao_phien(client, _login(client, "hs1"), p_gv1_an.id)
    assert r.status_code == 404


def test_hs_tao_phien_bai_duoc_giao_nhiem_vu_ok(db, client):
    """Bài của GV khác nhưng ĐƯỢC GIAO qua nhiệm vụ → HS vẫn tạo phiên được (đúng nghiệp vụ)."""
    hs1, p_gv1, p_gv2, p_gv1_an, p_gv2_giao = _seed(db)
    r = _tao_phien(client, _login(client, "hs1"), p_gv2_giao.id)
    assert r.status_code == 200, r.text
