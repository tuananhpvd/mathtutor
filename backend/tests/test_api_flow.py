"""Test tích hợp API luồng TLN (Phase 2)."""

import json

from app.auth.security import hash_password
from app.models.lop import Lop
from app.models.problem import Problem, TrangThaiDuyet
from app.models.solution_step import SolutionStep
from app.models.user import User, VaiTro


def seed_all(db):
    lop = Lop(ten="12A1")
    db.add(lop)
    db.flush()

    hs = User(vai_tro=VaiTro.hs, ho_ten="HS Test", dang_nhap="hs_test",
              mat_khau_hash=hash_password("pass"), lop_id=lop.id)
    gv = User(vai_tro=VaiTro.gv, ho_ten="GV Test", dang_nhap="gv_test",
              mat_khau_hash=hash_password("pass"))
    admin = User(vai_tro=VaiTro.admin, ho_ten="Admin", dang_nhap="admin_test",
                 mat_khau_hash=hash_password("pass"))
    db.add_all([hs, gv, admin])
    db.flush()
    lop.gv_id = gv.id  # HS tự luyện bài của GV chủ nhiệm lớp

    # Bài TLN đã duyệt, thuộc gv (GV chủ nhiệm lớp HS → HS tự chọn được)
    p = Problem(
        chuyen_de="Test", loai_cau="TLN", do_kho="tb",
        de_bai="Tìm x.", loai_dap_an_nhap="gia_tri",
        trang_thai_duyet=TrangThaiDuyet.da_duyet,
        nguoi_tao_id=gv.id,
        meta={"dap_an_cuoi": "5"},
    )
    db.add(p)
    db.flush()
    db.add(SolutionStep(
        problem_id=p.id, thu_tu=1, pham_vi="ca_bai",
        mo_ta="test", bieu_thuc_ket_qua="5",
        danh_sach_goi_y=["gợi 1", "gợi 2"],
    ))
    db.commit()
    return hs, gv, admin, p


def _token(client, dang_nhap, mat_khau="pass"):
    r = client.post("/api/auth/login", json={"dang_nhap": dang_nhap, "mat_khau": mat_khau})
    return r.json()["access_token"]


def _h(token):
    return {"Authorization": f"Bearer {token}"}


def test_luong_tln(client, db):
    hs, gv, admin, p = seed_all(db)
    tok = _token(client, "hs_test")

    # Tạo phiên
    r = client.post("/api/sessions", json={"problem_id": p.id}, headers=_h(tok))
    assert r.status_code == 200, r.text
    sid = r.json()["session_id"]
    assert r.json()["loai_cau"] == "TLN"
    assert r.json()["van_ban"]  # lời mở đầu không rỗng

    # Gửi tin sai
    r = client.post(f"/api/sessions/{sid}/message",
                    json={"noi_dung": "em nghĩ x=3", "dap_an_nhap": "3"},
                    headers=_h(tok))
    assert r.status_code == 200
    assert r.json()["y_dinh"] == "hoi_nguoc"
    assert r.json()["da_xong"] is False

    # Gửi tin đúng
    r = client.post(f"/api/sessions/{sid}/message",
                    json={"noi_dung": "x=5", "dap_an_nhap": "5"},
                    headers=_h(tok))
    assert r.status_code == 200
    assert r.json()["da_xong"] is True
    assert r.json()["y_dinh"] == "ket_thuc"


def test_tu_dong_gan_co_khong_hieu(client, db):
    """HS xin gợi ý vượt ngưỡng → tự gắn cờ 'không hiểu nhiều' cho GV (1 lần/phiên)."""
    from app.models.flag import Flag, LoaiCo

    hs, gv, admin, p = seed_all(db)
    tok = _token(client, "hs_test")
    sid = client.post("/api/sessions", json={"problem_id": p.id},
                      headers=_h(tok)).json()["session_id"]

    # Xin gợi ý đủ ngưỡng (mặc định 3) → tạo đúng 1 cờ
    for _ in range(3):
        r = client.post(f"/api/sessions/{sid}/message",
                        json={"yeu_cau_goi_y": True}, headers=_h(tok))
        assert r.status_code == 200

    co = db.query(Flag).filter(Flag.session_id == sid,
                               Flag.loai_co == LoaiCo.khong_hieu_nhieu).all()
    assert len(co) == 1
    assert co[0].trang_thai.value == "cho_xu_ly"

    # Xin thêm gợi ý → KHÔNG tạo cờ trùng
    client.post(f"/api/sessions/{sid}/message",
                json={"yeu_cau_goi_y": True}, headers=_h(tok))
    co2 = db.query(Flag).filter(Flag.session_id == sid,
                                Flag.loai_co == LoaiCo.khong_hieu_nhieu).all()
    assert len(co2) == 1


def test_tu_dong_gan_co_chot_chan(client, db):
    """Phản hồi bị lớp chốt chặn rò rỉ vượt ngưỡng → tự gắn cờ 'chốt chặn nhiều'."""
    from app.models.flag import Flag, LoaiCo

    lop = Lop(ten="12B")
    db.add(lop)
    db.flush()
    hs = User(vai_tro=VaiTro.hs, ho_ten="HS Chot", dang_nhap="hs_chot",
              mat_khau_hash=hash_password("pass"), lop_id=lop.id)
    db.add(hs)
    # Bài có gợi ý CỐ Ý lộ đáp án để lớp chốt chặn kích hoạt mỗi lượt.
    p = Problem(
        chuyen_de="Test", loai_cau="TLN", do_kho="tb",
        de_bai="Tìm x.", loai_dap_an_nhap="gia_tri",
        trang_thai_duyet=TrangThaiDuyet.da_duyet, meta={"dap_an_cuoi": "5"},
    )
    db.add(p)
    db.flush()
    db.add(SolutionStep(
        problem_id=p.id, thu_tu=1, pham_vi="ca_bai", mo_ta="t",
        bieu_thuc_ket_qua="5", danh_sach_goi_y=["đáp án là 5", "kết quả là 5"],
    ))
    db.commit()

    tok = _token(client, "hs_chot")
    sid = client.post("/api/sessions", json={"problem_id": p.id},
                      headers=_h(tok)).json()["session_id"]
    for _ in range(3):
        r = client.post(f"/api/sessions/{sid}/message",
                        json={"yeu_cau_goi_y": True}, headers=_h(tok))
        assert r.status_code == 200

    co = db.query(Flag).filter(Flag.session_id == sid,
                               Flag.loai_co == LoaiCo.chot_chan_nhieu).all()
    assert len(co) == 1, "phải tự gắn đúng 1 cờ chốt chặn nhiều"


def test_thoi_gian_chan_nghi_khi_quay_lai_lam_sau(client, db):
    """Rời đi lâu (gap lớn) chỉ tính tối đa = ngưỡng nghỉ, không phồng thời gian."""
    from datetime import datetime, timedelta, timezone

    from app.models.session import Session as SessionModel

    hs, gv, admin, p = seed_all(db)
    # Đặt ngưỡng nghỉ = 60s cho dễ kiểm tra
    atok = _token(client, "admin_test")
    client.patch("/api/admin/config", headers=_h(atok),
                 json={"khoa": "nguong_nghi_giay", "gia_tri": 60})

    tok = _token(client, "hs_test")
    sid = client.post("/api/sessions", json={"problem_id": p.id},
                      headers=_h(tok)).json()["session_id"]

    # Giả lập học sinh rời đi 2 giờ: lùi mốc tương tác gần nhất về quá khứ
    s = db.get(SessionModel, sid)
    s.cap_nhat_luc = datetime.now(timezone.utc) - timedelta(hours=2)
    db.commit()

    # Quay lại làm và hoàn thành ngay
    r = client.post(f"/api/sessions/{sid}/message",
                    json={"noi_dung": "x=5", "dap_an_nhap": "5"}, headers=_h(tok))
    assert r.json()["da_xong"] is True
    # Thời gian phải bị chặn ở ~ngưỡng (60s), KHÔNG phải ~7200s
    assert r.json()["thoi_gian_giay"] <= 60


def _seed_tn4pa(db, bat_buoc: bool):
    gv = db.query(User).filter_by(dang_nhap="gv_test").first()  # GV chủ nhiệm từ seed_all
    p = Problem(
        chuyen_de="Test", loai_cau="TN4PA", do_kho="de",
        de_bai="Hàm số đồng biến trên khoảng nào?", loai_dap_an_nhap="chon_phuong_an",
        trang_thai_duyet=TrangThaiDuyet.da_duyet, nguoi_tao_id=gv.id,
        meta={"phuong_an": {"A": "1", "B": "2", "C": "3", "D": "4"},
              "dap_an_dung": "B", "bat_buoc_suy_luan": bat_buoc},
    )
    db.add(p)
    db.flush()
    db.add(SolutionStep(
        problem_id=p.id, thu_tu=1, pham_vi="ca_bai",
        mo_ta="Tính y' và xét dấu", bieu_thuc_ket_qua="4*x - 4",
        danh_sach_goi_y=["gợi 1", "gợi 2"],
    ))
    db.commit()
    return p


def test_tn4pa_bat_buoc_suy_luan_hai_pha(client, db):
    seed_all(db)
    p = _seed_tn4pa(db, bat_buoc=True)
    tok = _token(client, "hs_test")

    # Tạo phiên: chưa mở khóa chọn đáp án, có mô tả bước
    r = client.post("/api/sessions", json={"problem_id": p.id}, headers=_h(tok))
    assert r.status_code == 200, r.text
    sid = r.json()["session_id"]
    assert r.json()["cho_chon_dap_an"] is False
    assert r.json()["buoc_mo_ta"] == "Tính y' và xét dấu"

    # Bấm chọn đáp án ngay → bị chặn, vẫn chưa mở khóa
    r = client.post(f"/api/sessions/{sid}/message",
                    json={"noi_dung": "", "dap_an_nhap": "B"}, headers=_h(tok))
    assert r.json()["cho_chon_dap_an"] is False
    assert r.json()["da_xong"] is False

    # Nhập biểu thức bước đúng → mở khóa chọn đáp án
    r = client.post(f"/api/sessions/{sid}/message",
                    json={"noi_dung": "y'=4x-4", "dap_an_nhap": "4*x-4"}, headers=_h(tok))
    assert r.json()["y_dinh"] == "xac_nhan_dung"
    assert r.json()["cho_chon_dap_an"] is True

    # Chọn đáp án đúng → hoàn thành
    r = client.post(f"/api/sessions/{sid}/message",
                    json={"noi_dung": "", "dap_an_nhap": "B"}, headers=_h(tok))
    assert r.json()["da_xong"] is True
    assert r.json()["y_dinh"] == "ket_thuc"


def test_tn4pa_chon_ngay_hai_pha(client, db):
    seed_all(db)
    p = _seed_tn4pa(db, bat_buoc=False)
    tok = _token(client, "hs_test")

    r = client.post("/api/sessions", json={"problem_id": p.id}, headers=_h(tok))
    sid = r.json()["session_id"]
    assert r.json()["cho_chon_dap_an"] is True  # mở ngay

    r = client.post(f"/api/sessions/{sid}/message",
                    json={"noi_dung": "", "dap_an_nhap": "B"}, headers=_h(tok))
    assert r.json()["da_xong"] is True


def _seed_tnds(db):
    gv = db.query(User).filter_by(dang_nhap="gv_test").first()  # GV chủ nhiệm từ seed_all
    p = Problem(
        chuyen_de="Test", loai_cau="TNDS", do_kho="tb",
        de_bai="Xét đúng/sai các mệnh đề.", loai_dap_an_nhap="dung_sai_4y",
        trang_thai_duyet=TrangThaiDuyet.da_duyet, nguoi_tao_id=gv.id,
        meta={"y": [
            {"ky_hieu": "a", "noi_dung_y": "ý a", "dap_an": "Dung", "bat_buoc_suy_luan": True},
            {"ky_hieu": "b", "noi_dung_y": "ý b", "dap_an": "Sai", "bat_buoc_suy_luan": False},
            {"ky_hieu": "c", "noi_dung_y": "ý c", "dap_an": "Dung", "bat_buoc_suy_luan": False},
            {"ky_hieu": "d", "noi_dung_y": "ý d", "dap_an": "Sai", "bat_buoc_suy_luan": False},
        ]},
    )
    db.add(p)
    db.flush()
    db.add(SolutionStep(problem_id=p.id, thu_tu=1, pham_vi="a", mo_ta="Tính f(0)",
                        bieu_thuc_ket_qua="2", danh_sach_goi_y=["g a1", "g a2"]))
    for ky in ("b", "c", "d"):
        db.add(SolutionStep(problem_id=p.id, thu_tu=1, pham_vi=ky, mo_ta=f"ý {ky}",
                            bieu_thuc_ket_qua="", danh_sach_goi_y=["g1"]))
    db.commit()
    return p


def test_tnds_suy_luan_va_bat_dung_moi_qua_y(client, db):
    seed_all(db)
    p = _seed_tnds(db)
    tok = _token(client, "hs_test")

    r = client.post("/api/sessions", json={"problem_id": p.id}, headers=_h(tok))
    sid = r.json()["session_id"]
    assert r.json()["cho_chon_dung_sai"] is False  # ý a bắt buộc suy luận

    # Chốt Đúng ngay khi chưa suy luận → bị chặn
    r = client.post(f"/api/sessions/{sid}/message",
                    json={"noi_dung": "", "dap_an_nhap": "Dung"}, headers=_h(tok))
    assert r.json()["cho_chon_dung_sai"] is False
    assert r.json()["da_xong"] is False

    # Suy luận đúng (f(0)=2) → mở khóa
    r = client.post(f"/api/sessions/{sid}/message",
                    json={"noi_dung": "2", "dap_an_nhap": "2"}, headers=_h(tok))
    assert r.json()["y_dinh"] == "xac_nhan_dung"
    assert r.json()["cho_chon_dung_sai"] is True

    # Chốt SAI → phải ở lại ý a
    r = client.post(f"/api/sessions/{sid}/message",
                    json={"noi_dung": "", "dap_an_nhap": "Sai"}, headers=_h(tok))
    assert r.json()["y_hien_tai"] == "a"
    assert r.json()["y_dinh"] == "hoi_nguoc"

    # Chốt ĐÚNG → sang ý b, ghi thời gian ý a
    r = client.post(f"/api/sessions/{sid}/message",
                    json={"noi_dung": "", "dap_an_nhap": "Dung"}, headers=_h(tok))
    assert r.json()["y_hien_tai"] == "b"
    assert "a" in (r.json()["thoi_gian_y"] or {})
    assert r.json()["cho_chon_dung_sai"] is True  # ý b không bắt buộc suy luận


def test_tnds_hoan_thanh_co_dap_an_y_va_thoi_gian(client, db):
    seed_all(db)
    p = _seed_tnds(db)
    tok = _token(client, "hs_test")
    r = client.post("/api/sessions", json={"problem_id": p.id}, headers=_h(tok))
    sid = r.json()["session_id"]

    def msg(body):
        return client.post(f"/api/sessions/{sid}/message", json=body, headers=_h(tok)).json()

    # ý a: suy luận rồi chốt Đúng
    msg({"noi_dung": "2", "dap_an_nhap": "2"})
    r = msg({"noi_dung": "", "dap_an_nhap": "Dung"})
    assert r["da_xong"] is False
    assert r.get("dap_an_y") is None  # chưa xong → không lộ đáp án
    # ý b/c/d không bắt buộc suy luận; chốt đúng theo đáp án chuẩn (Sai/Dung/Sai)
    msg({"noi_dung": "", "dap_an_nhap": "Sai"})   # b
    msg({"noi_dung": "", "dap_an_nhap": "Dung"})  # c
    r = msg({"noi_dung": "", "dap_an_nhap": "Sai"})  # d → hoàn thành
    assert r["da_xong"] is True
    assert r["dap_an_y"] == {"a": "Dung", "b": "Sai", "c": "Dung", "d": "Sai"}
    assert set((r["thoi_gian_y"] or {}).keys()) == {"a", "b", "c", "d"}


def test_phien_cua_toi_trang_thai(client, db):
    hs, gv, admin, p = seed_all(db)
    tok = _token(client, "hs_test")
    # Chưa làm → không có trong danh sách
    assert client.get("/api/sessions/cua-toi", headers=_h(tok)).json() == []
    # Tạo phiên → đang làm
    sid = client.post("/api/sessions", json={"problem_id": p.id}, headers=_h(tok)).json()["session_id"]
    r = client.get("/api/sessions/cua-toi", headers=_h(tok)).json()
    assert len(r) == 1 and r[0]["problem_id"] == p.id
    assert r[0]["trang_thai"] == "dang_lam" and r[0]["session_id"] == sid
    # Hoàn thành (TLN đáp án 5) → hoan_thanh
    client.post(f"/api/sessions/{sid}/message",
                json={"noi_dung": "x=5", "dap_an_nhap": "5"}, headers=_h(tok))
    r = client.get("/api/sessions/cua-toi", headers=_h(tok)).json()
    assert r[0]["trang_thai"] == "hoan_thanh"


def test_get_problems_hs_khong_co_dap_an(client, db):
    hs, gv, admin, p = seed_all(db)
    tok = _token(client, "hs_test")

    r = client.get(f"/api/problems/{p.id}", headers=_h(tok))
    assert r.status_code == 200
    data = r.json()
    # Không được chứa trường đáp án
    assert "dap_an_cuoi" not in json.dumps(data)
    assert "dap_an_dung" not in json.dumps(data)


def test_admin_endpoint_chặn_hs(client, db):
    hs, gv, admin, p = seed_all(db)
    tok = _token(client, "hs_test")
    r = client.get("/api/admin/ping", headers=_h(tok))
    assert r.status_code == 403


def test_admin_endpoint_chặn_gv(client, db):
    hs, gv, admin, p = seed_all(db)
    tok = _token(client, "gv_test")
    r = client.get("/api/admin/ping", headers=_h(tok))
    assert r.status_code == 403


def test_chuyen_de_id_va_dang_id_theo_bai_va_phien(client, db):
    """GET /problems/{id} và GET /sessions/{id} phải trả đúng chuyen_de_id/dang_id (dùng cho
    tính năng 'Xem lại lý thuyết' theo đúng dạng HS đang làm — cần ID, không phải tên hiển thị)."""
    from app.models.danh_muc import ChuyenDe, Dang

    hs, gv, admin, _p_cu = seed_all(db)
    tok_gv = _token(client, "gv_test")
    tok_hs = _token(client, "hs_test")

    cd = ChuyenDe(ten="Đạo hàm", nguoi_tao_id=gv.id)
    db.add(cd)
    db.flush()
    dang = Dang(chuyen_de_id=cd.id, ten="Cực trị", nguoi_tao_id=gv.id)
    db.add(dang)
    db.flush()
    p = Problem(
        chuyen_de="Đạo hàm", dang_id=dang.id, loai_cau="TLN", do_kho="tb",
        de_bai="Tìm cực trị.", loai_dap_an_nhap="gia_tri",
        trang_thai_duyet=TrangThaiDuyet.da_duyet, nguoi_tao_id=gv.id,
        meta={"dap_an_cuoi": "1"},
    )
    db.add(p)
    db.commit()

    r = client.get(f"/api/problems/{p.id}", headers=_h(tok_hs))
    assert r.status_code == 200
    assert r.json()["dang_id"] == dang.id
    assert r.json()["chuyen_de_id"] == cd.id

    sid = client.post("/api/sessions", json={"problem_id": p.id}, headers=_h(tok_hs)).json()["session_id"]
    r2 = client.get(f"/api/sessions/{sid}", headers=_h(tok_hs))
    assert r2.status_code == 200
    assert r2.json()["dang_id"] == dang.id
    assert r2.json()["chuyen_de_id"] == cd.id

    # Bài KHÔNG có dang_id (dữ liệu cũ/chưa gán dạng) → cả 2 trường None, không lỗi
    r3 = client.get(f"/api/problems/{_p_cu.id}", headers=_h(tok_gv))
    assert r3.json()["dang_id"] is None
    assert r3.json()["chuyen_de_id"] is None
