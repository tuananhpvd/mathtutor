"""Tests Phase 10 — API quản trị."""

from app.auth.security import hash_password
from app.models.user import User, VaiTro


def _login(client, dn):
    return client.post("/api/auth/login",
                       json={"dang_nhap": dn, "mat_khau": "password"}).json()["access_token"]


def _seed(db):
    admin = User(vai_tro=VaiTro.admin, ho_ten="Quản trị", dang_nhap="admin",
                 mat_khau_hash=hash_password("password"))
    gv = User(vai_tro=VaiTro.gv, ho_ten="Cô Lan", dang_nhap="gv1",
              mat_khau_hash=hash_password("password"))
    hs = User(vai_tro=VaiTro.hs, ho_ten="HS A", dang_nhap="hs1",
              mat_khau_hash=hash_password("password"))
    db.add_all([admin, gv, hs])
    db.commit()


def test_stats_admin(db, client):
    _seed(db)
    h = {"Authorization": f"Bearer {_login(client, 'admin')}"}
    r = client.get("/api/admin/stats", headers=h)
    assert r.status_code == 200
    data = r.json()
    assert data["so_nguoi_dung"] == 3
    assert data["so_giao_vien"] == 1
    assert data["so_hoc_sinh"] == 1


def test_stats_llm_provider_theo_cau_hinh_db_khong_phai_env(db, client):
    """Bug đã sửa: badge Dashboard từng đọc settings.llm_provider (env, luôn 'stub'
    trong test) thay vì cấu hình Admin đã lưu trong DB — khiến hiện sai provider
    thật đang chạy (get_llm_client ưu tiên đọc DB, không đọc settings)."""
    _seed(db)
    h = {"Authorization": f"Bearer {_login(client, 'admin')}"}

    # Chưa cấu hình gì trong DB → dùng mặc định CAU_HINH_MAC_DINH (gemini), không phải "stub".
    r = client.get("/api/admin/stats", headers=h)
    assert r.json()["llm_provider"] == "gemini"

    # Admin đổi provider trong Cấu hình → Dashboard phải phản ánh đúng ngay.
    client.patch("/api/admin/config", headers=h,
                 json={"khoa": "llm_provider", "gia_tri": "anthropic"})
    r = client.get("/api/admin/stats", headers=h)
    assert r.json()["llm_provider"] == "anthropic"


def test_gan_lop_cho_tai_khoan(db, client):
    _seed(db)
    from app.models.lop import Lop
    lop = Lop(ten="12A1")
    db.add(lop)
    db.commit()
    h = {"Authorization": f"Bearer {_login(client, 'admin')}"}

    lops = client.get("/api/admin/lop", headers=h).json()
    assert any(item["ten"] == "12A1" for item in lops)

    hs = db.query(User).filter_by(dang_nhap="hs1").first()
    r = client.patch(f"/api/admin/users/{hs.id}/lop", headers=h, json={"lop_id": lop.id})
    assert r.status_code == 200 and r.json()["lop_id"] == lop.id

    users = client.get("/api/admin/users", headers=h).json()
    u = next(x for x in users if x["dang_nhap"] == "hs1")
    assert u["lop_ten"] == "12A1"


def test_crud_lop_va_quan_ly(db, client):
    _seed(db)
    h = {"Authorization": f"Bearer {_login(client, 'admin')}"}
    gv = db.query(User).filter_by(dang_nhap="gv1").first()

    # Tạo lớp gán GV
    r = client.post("/api/admin/lop", headers=h, json={"ten": "12A2", "gv_id": gv.id})
    assert r.status_code == 200, r.text
    lop_id = r.json()["id"]

    # Danh sách lớp chi tiết có GV
    lct = client.get("/api/admin/lop-chi-tiet", headers=h).json()
    lop = next(x for x in lct if x["id"] == lop_id)
    assert lop["gv_ten"] == "Cô Lan" and lop["so_hoc_sinh"] == 0

    # Gán học sinh vào lớp
    hs = db.query(User).filter_by(dang_nhap="hs1").first()
    client.patch(f"/api/admin/users/{hs.id}/lop", headers=h, json={"lop_id": lop_id})

    # Quản lý theo giáo viên: GV có lớp + học sinh
    gvs = client.get("/api/admin/giao-vien", headers=h).json()
    g = next(x for x in gvs if x["id"] == gv.id)
    assert any(lp["id"] == lop_id and len(lp["hoc_sinhs"]) == 1 for lp in g["lops"])

    # Quản lý theo học sinh: có lop_ten + gv_ten
    hss = client.get("/api/admin/hoc-sinh", headers=h).json()
    hrow = next(x for x in hss if x["id"] == hs.id)
    assert hrow["lop_ten"] == "12A2" and hrow["gv_ten"] == "Cô Lan"

    # Sửa lớp: đổi tên + gỡ GV
    client.patch(f"/api/admin/lop/{lop_id}", headers=h, json={"ten": "12A3", "gv_id": None})
    lct = client.get("/api/admin/lop-chi-tiet", headers=h).json()
    lop = next(x for x in lct if x["id"] == lop_id)
    assert lop["ten"] == "12A3" and lop["gv_id"] is None

    # Xóa lớp → học sinh bị gỡ khỏi lớp
    client.delete(f"/api/admin/lop/{lop_id}", headers=h)
    hss = client.get("/api/admin/hoc-sinh", headers=h).json()
    assert next(x for x in hss if x["id"] == hs.id)["lop_id"] is None


def test_sua_va_xoa_tai_khoan(db, client):
    _seed(db)
    h = {"Authorization": f"Bearer {_login(client, 'admin')}"}
    hs = db.query(User).filter_by(dang_nhap="hs1").first()

    # Sửa họ tên + đổi mật khẩu
    r = client.patch(f"/api/admin/users/{hs.id}", headers=h,
                     json={"ho_ten": "HS Mới", "mat_khau": "moi123"})
    assert r.status_code == 200 and r.json()["ho_ten"] == "HS Mới"
    # Đăng nhập bằng mật khẩu mới
    assert client.post("/api/auth/login",
                       json={"dang_nhap": "hs1", "mat_khau": "moi123"}).status_code == 200

    # Xóa HS chưa có phiên → OK
    assert client.delete(f"/api/admin/users/{hs.id}", headers=h).status_code == 200
    assert not db.query(User).filter_by(dang_nhap="hs1").first()


def test_xoa_hs_co_phien_bi_chan(db, client):
    _seed(db)
    from app.models.problem import Problem, TrangThaiDuyet
    from app.models.session import Session as S
    h = {"Authorization": f"Bearer {_login(client, 'admin')}"}
    hs = db.query(User).filter_by(dang_nhap="hs1").first()
    p = Problem(chuyen_de="X", loai_cau="TLN", do_kho="tb", de_bai="?",
                loai_dap_an_nhap="gia_tri", trang_thai_duyet=TrangThaiDuyet.da_duyet,
                meta={"dap_an_cuoi": "1"})
    db.add(p)
    db.flush()
    db.add(S(hoc_sinh_id=hs.id, problem_id=p.id))
    db.commit()
    r = client.delete(f"/api/admin/users/{hs.id}", headers=h)
    assert r.status_code == 400 and "Khóa" in r.json()["detail"]


def test_stats_phan_quyen_chan_gv_hs(db, client):
    _seed(db)
    for dn in ["gv1", "hs1"]:
        h = {"Authorization": f"Bearer {_login(client, dn)}"}
        assert client.get("/api/admin/stats", headers=h).status_code == 403


def test_tao_va_khoa_tai_khoan(db, client):
    _seed(db)
    h = {"Authorization": f"Bearer {_login(client, 'admin')}"}

    r = client.post("/api/admin/users", headers=h, json={
        "ho_ten": "HS Mới", "dang_nhap": "hs99", "mat_khau": "123456", "vai_tro": "hs"})
    assert r.status_code == 200
    uid = r.json()["id"]

    # đăng nhập được
    assert client.post("/api/auth/login",
                       json={"dang_nhap": "hs99", "mat_khau": "123456"}).status_code == 200

    # khóa
    r2 = client.patch(f"/api/admin/users/{uid}/trang-thai", headers=h,
                      json={"trang_thai": "khoa"})
    assert r2.status_code == 200
    assert r2.json()["trang_thai"] == "khoa"

    # bị khóa → login 403
    assert client.post("/api/auth/login",
                       json={"dang_nhap": "hs99", "mat_khau": "123456"}).status_code == 403


def test_tao_tai_khoan_trung_dang_nhap(db, client):
    _seed(db)
    h = {"Authorization": f"Bearer {_login(client, 'admin')}"}
    r = client.post("/api/admin/users", headers=h, json={
        "ho_ten": "Trùng", "dang_nhap": "gv1", "mat_khau": "123456", "vai_tro": "gv"})
    assert r.status_code == 400


def test_khong_khoa_duoc_admin(db, client):
    _seed(db)
    h = {"Authorization": f"Bearer {_login(client, 'admin')}"}
    admin = db.query(User).filter(User.dang_nhap == "admin").first()
    r = client.patch(f"/api/admin/users/{admin.id}/trang-thai", headers=h,
                     json={"trang_thai": "khoa"})
    assert r.status_code == 400


def test_cau_hinh_get_va_set(db, client):
    _seed(db)
    h = {"Authorization": f"Bearer {_login(client, 'admin')}"}

    r = client.get("/api/admin/config", headers=h)
    assert r.status_code == 200
    assert "nguong_co_khong_hieu" in r.json()
    assert "bang_bac_thang" in r.json()

    r2 = client.patch("/api/admin/config", headers=h,
                      json={"khoa": "nguong_co_khong_hieu", "gia_tri": 5})
    assert r2.status_code == 200
    assert r2.json()["nguong_co_khong_hieu"] == 5

    # đọc lại vẫn còn
    assert client.get("/api/admin/config", headers=h).json()["nguong_co_khong_hieu"] == 5


def test_cau_hinh_llm_provider_va_khoa_an(db, client):
    _seed(db)
    h = {"Authorization": f"Bearer {_login(client, 'admin')}"}

    # Mặc định provider gemini; khóa chưa đặt
    r = client.get("/api/admin/config", headers=h).json()
    assert r["llm_provider"] == "gemini"
    assert r["llm_api_key_gemini_da_dat"] is False
    assert "llm_api_key_gemini" not in r  # KHÔNG lộ khóa nguyên văn

    # Đặt khóa Gemini → cờ da_dat = True, vẫn không lộ khóa
    client.patch("/api/admin/config", headers=h,
                 json={"khoa": "llm_api_key_gemini", "gia_tri": "AIza-secret-123"})
    r2 = client.get("/api/admin/config", headers=h).json()
    assert r2["llm_api_key_gemini_da_dat"] is True
    assert "AIza-secret-123" not in str(r2)

    # Gửi khóa rỗng KHÔNG xóa khóa cũ
    client.patch("/api/admin/config", headers=h,
                 json={"khoa": "llm_api_key_gemini", "gia_tri": ""})
    assert client.get("/api/admin/config", headers=h).json()["llm_api_key_gemini_da_dat"] is True

    # Đổi provider sang anthropic
    client.patch("/api/admin/config", headers=h,
                 json={"khoa": "llm_provider", "gia_tri": "anthropic"})
    assert client.get("/api/admin/config", headers=h).json()["llm_provider"] == "anthropic"


def test_cau_hinh_khoa_khong_hop_le(db, client):
    _seed(db)
    h = {"Authorization": f"Bearer {_login(client, 'admin')}"}
    r = client.patch("/api/admin/config", headers=h,
                     json={"khoa": "khoa_la", "gia_tri": 1})
    assert r.status_code == 400


# ----- Cache lay_cau_hinh (hiệu năng) -----

def test_cau_hinh_cache_tra_cung_object_trong_ttl(db):
    """Gọi 2 lần liên tiếp trong TTL phải trả về ĐÚNG cùng 1 object (từ cache), không phải
    2 dict mới tạo từ truy vấn DB — chứng minh cache thật sự hoạt động, không chỉ giá trị
    giống nhau mà trùng identity."""
    from app.services.admin_service import lay_cau_hinh

    c1 = lay_cau_hinh(db)
    c2 = lay_cau_hinh(db)
    assert c1 is c2


def test_cau_hinh_cache_xoa_khi_ghi(db, client):
    """Sửa cấu hình xong phải thấy hiệu lực NGAY (không đợi hết TTL) — dat_cau_hinh phải
    chủ động xóa cache."""
    from app.services.admin_service import lay_cau_hinh

    _seed(db)
    h = {"Authorization": f"Bearer {_login(client, 'admin')}"}
    assert lay_cau_hinh(db)["nguong_co_khong_hieu"] == 3  # mặc định, nạp vào cache

    client.patch("/api/admin/config", headers=h,
                 json={"khoa": "nguong_co_khong_hieu", "gia_tri": 7})
    assert lay_cau_hinh(db)["nguong_co_khong_hieu"] == 7  # không phải giá trị cache cũ


def test_cau_hinh_cache_buoc_1_lam_ban_cache(db):
    """Cặp với test ngay sau. Cố tình "làm bẩn" cache bằng giá trị không phải mặc định,
    KHÔNG qua dat_cau_hinh (hàm đó tự xóa cache khi ghi nên không mô phỏng được tình huống
    cần kiểm — cache còn sót lại từ 1 request/test TRƯỚC mà không ai chủ động dọn)."""
    import time

    import app.services.admin_service as admin_service

    admin_service._cau_hinh_cache = {**admin_service.CAU_HINH_MAC_DINH, "llm_provider": "GIA_LAP_RO_RI"}
    admin_service._cau_hinh_cache_luc = time.monotonic()


def test_cau_hinh_cache_buoc_2_khong_ro_ri_sang_test_khac(db):
    """DB test này hoàn toàn mới (fixture 'db' tạo lại bảng từ đầu), nhưng cache
    lay_cau_hinh() là biến toàn tiến trình Python — nếu không có gì chủ động dọn giữa các
    test, giá trị "bẩn" gài ở test trước sẽ rò rỉ sang đây dù DB này chưa hề ghi gì. Fixture
    autouse `_xoa_cache_cau_hinh` (conftest.py) phải chặn đúng việc này."""
    from app.services.admin_service import lay_cau_hinh

    assert lay_cau_hinh(db)["llm_provider"] == "gemini"


def test_users_list_admin(db, client):
    _seed(db)
    h = {"Authorization": f"Bearer {_login(client, 'admin')}"}
    r = client.get("/api/admin/users", headers=h)
    assert r.status_code == 200
    assert len(r.json()) == 3


# ----- Từ khóa an toàn quản lý qua admin (không sửa code) -----

def test_tu_khoa_an_toan_mac_dinh_hien_du_khi_chua_tuy_chinh(db, client):
    _seed(db)
    h = {"Authorization": f"Bearer {_login(client, 'admin')}"}
    r = client.get("/api/admin/config", headers=h).json()
    assert any(t["tu_khoa"] == "tự tử" for t in r["tu_khoa_khan_cap"])
    assert all(t["la_mac_dinh"] for t in r["tu_khoa_khan_cap"])


def test_them_tu_khoa_moi_va_ap_dung_ngay_trong_chat(db, client):
    """Admin thêm 1 từ khóa mới KHÔNG có sẵn trong code — HS gõ đúng từ đó ngay lập tức
    bị lớp lọc phát hiện, không cần sửa code/deploy lại."""
    from app.auth.security import hash_password
    from app.models.lop import Lop
    from app.models.problem import Problem, TrangThaiDuyet
    from app.models.solution_step import SolutionStep
    from app.models.user import User, VaiTro

    _seed(db)
    h = {"Authorization": f"Bearer {_login(client, 'admin')}"}

    r = client.get("/api/admin/config", headers=h).json()
    danh_sach = r["tu_khoa_khong_phu_hop"] + [{"tu_khoa": "bỏ học đi bụi", "kich_hoat": True}]
    r2 = client.patch("/api/admin/config", headers=h,
                      json={"khoa": "tu_khoa_khong_phu_hop", "gia_tri": danh_sach})
    assert r2.status_code == 200
    them = next(t for t in r2.json()["tu_khoa_khong_phu_hop"] if t["tu_khoa"] == "bỏ học đi bụi")
    assert them["la_mac_dinh"] is False

    # HS gõ đúng từ mới thêm (không dấu) → phải bị lọc, dù từ này chưa từng có trong code.
    lop = Lop(ten="12A1")
    db.add(lop)
    db.flush()
    gv = User(vai_tro=VaiTro.gv, ho_ten="GV X", dang_nhap="gvtukhoa",
              mat_khau_hash=hash_password("password"))
    hs = User(vai_tro=VaiTro.hs, ho_ten="HS A", dang_nhap="hstukhoa",
              mat_khau_hash=hash_password("password"), lop_id=lop.id)
    db.add_all([gv, hs])
    db.flush()
    lop.gv_id = gv.id
    p = Problem(chuyen_de="Test", loai_cau="TLN", do_kho="tb", de_bai="Tìm x.",
                loai_dap_an_nhap="gia_tri", trang_thai_duyet=TrangThaiDuyet.da_duyet,
                nguoi_tao_id=gv.id, meta={"dap_an_cuoi": "5"})
    db.add(p)
    db.flush()
    db.add(SolutionStep(problem_id=p.id, thu_tu=1, pham_vi="ca_bai", mo_ta="b1",
                        bieu_thuc_ket_qua="5", danh_sach_goi_y=["g1", "g2"]))
    db.commit()
    h_hs = {"Authorization": f"Bearer {_login(client, 'hstukhoa')}"}
    rp = client.post("/api/sessions", headers=h_hs, json={"problem_id": p.id})
    sid = rp.json()["session_id"]
    rm = client.post(f"/api/sessions/{sid}/message", headers=h_hs,
                     json={"noi_dung": "em muon bo hoc di bui"})
    assert rm.status_code == 200
    assert rm.json()["y_dinh"] == "tu_choi"
    assert "bỏ học đi bụi" not in rm.json()["van_ban"]  # không lặp từ khóa cho HS thấy


def test_tu_khoa_mac_dinh_chi_tat_duoc_khong_the_mat_khoi_danh_sach(db, client):
    """Gửi lên danh sách THIẾU 1 từ khóa mặc định (vd lỗi giao diện/gọi API thủ công) →
    server tự thêm lại ở trạng thái BẬT, không cho phép làm mất từ khóa nền an toàn."""
    _seed(db)
    h = {"Authorization": f"Bearer {_login(client, 'admin')}"}
    r = client.get("/api/admin/config", headers=h).json()
    con_lai = [t for t in r["tu_khoa_khan_cap"] if t["tu_khoa"] != "tự tử"]
    r2 = client.patch("/api/admin/config", headers=h,
                      json={"khoa": "tu_khoa_khan_cap", "gia_tri": con_lai})
    assert r2.status_code == 200
    tu_tu = next(t for t in r2.json()["tu_khoa_khan_cap"] if t["tu_khoa"] == "tự tử")
    assert tu_tu["kich_hoat"] is True
    assert tu_tu["la_mac_dinh"] is True


def test_tat_tu_khoa_mac_dinh_thi_khong_con_bat_duoc_nhung_van_con_trong_danh_sach(db, client):
    _seed(db)
    h = {"Authorization": f"Bearer {_login(client, 'admin')}"}
    r = client.get("/api/admin/config", headers=h).json()
    moi = [
        {**t, "kich_hoat": False} if t["tu_khoa"] == "ma túy" else t
        for t in r["tu_khoa_khong_phu_hop"]
    ]
    client.patch("/api/admin/config", headers=h,
                 json={"khoa": "tu_khoa_khong_phu_hop", "gia_tri": moi})

    from app.services.admin_service import lay_tu_khoa_an_toan
    tu_khoa = lay_tu_khoa_an_toan(db)
    assert "ma túy" not in tu_khoa["tu_khoa_khong_phu_hop"]

    r2 = client.get("/api/admin/config", headers=h).json()
    ma_tuy = next(t for t in r2["tu_khoa_khong_phu_hop"] if t["tu_khoa"] == "ma túy")
    assert ma_tuy["kich_hoat"] is False
    assert ma_tuy["la_mac_dinh"] is True


def test_tu_khoa_thu_dung_danh_sach_dang_luu(db, client):
    _seed(db)
    h = {"Authorization": f"Bearer {_login(client, 'admin')}"}
    r = client.post("/api/admin/tu-khoa-thu", headers=h, json={"van_ban": "em muốn chết"})
    assert r.status_code == 200
    assert r.json()["an_toan"] is False
    assert r.json()["khan_cap"] is True

    r2 = client.post("/api/admin/tu-khoa-thu", headers=h,
                     json={"van_ban": "em tính đạo hàm ra sao"})
    assert r2.json()["an_toan"] is True


def test_tu_khoa_thu_khong_phai_admin_bi_chan(db, client):
    _seed(db)
    h = {"Authorization": f"Bearer {_login(client, 'gv1')}"}
    r = client.post("/api/admin/tu-khoa-thu", headers=h, json={"van_ban": "test"})
    assert r.status_code == 403


def test_admin_tu_doi_mat_khau_va_ho_ten(db, client):
    """Admin trước đây KHÔNG có cách nào tự đổi mật khẩu (sua_tai_khoan() chặn cứng mọi sửa
    lên tài khoản admin) — /admin/ho-so là lối đi RIÊNG, chỉ tác động đúng tài khoản người
    gọi, không đụng rào chắn đó."""
    _seed(db)
    tok = _login(client, "admin")
    h = {"Authorization": f"Bearer {tok}"}

    r = client.get("/api/admin/ho-so", headers=h)
    assert r.status_code == 200
    assert r.json() == {
        "id": r.json()["id"], "ho_ten": "Quản trị", "dang_nhap": "admin",
        "vai_tro": "admin", "trang_thai": "hoat_dong",
    }

    r2 = client.patch("/api/admin/ho-so", headers=h,
                      json={"ho_ten": "Quản trị viên", "mat_khau": "matkhaumoi123"})
    assert r2.status_code == 200, r2.text
    assert r2.json()["ho_ten"] == "Quản trị viên"

    # Đăng nhập lại bằng mật khẩu MỚI xác nhận đã đổi thật (không chỉ đổi trong response)
    r3 = client.post("/api/auth/login", json={"dang_nhap": "admin", "mat_khau": "matkhaumoi123"})
    assert r3.status_code == 200, r3.text

    # Mật khẩu cũ không còn dùng được
    r4 = client.post("/api/auth/login", json={"dang_nhap": "admin", "mat_khau": "password"})
    assert r4.status_code == 401


def test_admin_ho_so_khong_phai_admin_bi_chan(db, client):
    _seed(db)
    h = {"Authorization": f"Bearer {_login(client, 'gv1')}"}
    assert client.get("/api/admin/ho-so", headers=h).status_code == 403
    assert client.patch("/api/admin/ho-so", headers=h, json={"ho_ten": "x"}).status_code == 403


def test_admin_khong_tu_khoa_duoc_qua_sua_tai_khoan(db, client):
    """Rào chắn cũ (sua_tai_khoan chặn sửa admin) vẫn nguyên vẹn — /admin/ho-so KHÔNG mở
    thêm lỗ hổng cho phép admin sửa MỘT admin KHÁC qua route quản lý tài khoản chung."""
    _seed(db)
    admin2 = User(vai_tro=VaiTro.admin, ho_ten="Admin 2", dang_nhap="admin2",
                 mat_khau_hash=hash_password("password"))
    db.add(admin2)
    db.commit()

    h = {"Authorization": f"Bearer {_login(client, 'admin')}"}
    r = client.patch(f"/api/admin/users/{admin2.id}", headers=h, json={"ho_ten": "x"})
    assert r.status_code == 400


def test_import_tai_khoan_qua_2000_dong_bi_chan(db, client):
    """max_length=2000 trên ImportTaiKhoanRequest.tai_khoans — chặn batch khổng lồ tốn
    RAM/CPU không giới hạn, TRƯỚC KHI chạm tới service (lỗi validate 422)."""
    _seed(db)
    h = {"Authorization": f"Bearer {_login(client, 'admin')}"}
    tai_khoans = [
        {"ho_ten": f"HS {i}", "dang_nhap": f"hsx{i}", "mat_khau": "123456", "vai_tro": "hs"}
        for i in range(2001)
    ]
    r = client.post("/api/admin/users/import-batch", headers=h, json={"tai_khoans": tai_khoans})
    assert r.status_code == 422


def test_mat_khau_toi_thieu_6_ky_tu(db, client):
    """Chuẩn mật khẩu ≥ 6 ký tự (nâng từ 4): tạo tài khoản mật khẩu 5 ký tự bị chặn (422),
    6 ký tự OK. Login KHÔNG áp min nên tài khoản seed/cũ mật khẩu ngắn hơn vẫn đăng nhập được."""
    _seed(db)
    h = {"Authorization": f"Bearer {_login(client, 'admin')}"}

    r5 = client.post("/api/admin/users", headers=h, json={
        "ho_ten": "Ngắn", "dang_nhap": "hsngan", "mat_khau": "12345", "vai_tro": "hs"})
    assert r5.status_code == 422

    r6 = client.post("/api/admin/users", headers=h, json={
        "ho_ten": "Đủ", "dang_nhap": "hsdu", "mat_khau": "123456", "vai_tro": "hs"})
    assert r6.status_code == 200

    # Tài khoản seed 'gv1' (mật khẩu "password" 8 ký tự, tạo thẳng qua _seed không qua schema)
    # vẫn đăng nhập bình thường — min chỉ áp lúc tạo/đổi, không áp lúc login.
    assert client.post("/api/auth/login",
                       json={"dang_nhap": "gv1", "mat_khau": "password"}).status_code == 200
