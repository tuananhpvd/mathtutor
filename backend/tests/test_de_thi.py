"""Tests C1-GĐ1 — đề ôn thi THPT: ghép đề, thi có giờ, chấm, kết quả."""

from datetime import datetime, timedelta, timezone

from app.auth.security import hash_password
from app.models.de_thi import BaiThi
from app.models.lop import Lop
from app.models.problem import Problem, TrangThaiDuyet
from app.models.user import User, VaiTro


def _login(client, dn):
    return client.post("/api/auth/login",
                       json={"dang_nhap": dn, "mat_khau": "pass"}).json()["access_token"]


def _h(tok):
    return {"Authorization": f"Bearer {tok}"}


def _seed(db):
    gv = User(vai_tro=VaiTro.gv, ho_ten="GV Đề", dang_nhap="gv_de",
              mat_khau_hash=hash_password("pass"))
    gv2 = User(vai_tro=VaiTro.gv, ho_ten="GV Khác", dang_nhap="gv2_de",
               mat_khau_hash=hash_password("pass"))
    db.add_all([gv, gv2])
    db.flush()
    lop = Lop(ten="12DE", gv_id=gv.id)
    db.add(lop)
    db.flush()
    hs = User(vai_tro=VaiTro.hs, ho_ten="HS Đề", dang_nhap="hs_de",
              mat_khau_hash=hash_password("pass"), lop_id=lop.id)
    db.add(hs)
    db.flush()

    def bai(loai, meta, nguoi_tao=gv.id):
        p = Problem(chuyen_de="Ôn thi", loai_cau=loai, do_kho="tb", de_bai=f"Câu {loai}?",
                    loai_dap_an_nhap="gia_tri", trang_thai_duyet=TrangThaiDuyet.da_duyet,
                    nguoi_tao_id=nguoi_tao, meta=meta)
        db.add(p)
        db.flush()
        return p

    p_tn = bai("TN4PA", {"phuong_an": {"A": "1", "B": "2", "C": "3", "D": "4"},
                         "dap_an_dung": "B"})
    p_ds = bai("TNDS", {"y": [
        {"ky_hieu": "a", "noi_dung_y": "ý a", "dap_an": "Dung"},
        {"ky_hieu": "b", "noi_dung_y": "ý b", "dap_an": "Sai"},
        {"ky_hieu": "c", "noi_dung_y": "ý c", "dap_an": "Dung"},
        {"ky_hieu": "d", "noi_dung_y": "ý d", "dap_an": "Sai"},
    ]})
    p_tln = bai("TLN", {"dap_an_cuoi": "5"})
    p_gv2 = bai("TLN", {"dap_an_cuoi": "7"}, nguoi_tao=gv2.id)
    db.commit()
    return gv, gv2, hs, p_tn, p_ds, p_tln, p_gv2


def _tao_de(client, h_gv, p_tn, p_ds, p_tln, **ghi_de):
    body = {"ten": "Đề thử số 1", "thoi_gian_phut": 90,
            "cau_theo_phan": {"I": [p_tn.id], "II": [p_ds.id], "III": [p_tln.id]}}
    body.update(ghi_de)
    return client.post("/api/de-thi", headers=h_gv, json=body)


def test_tao_de_validate(db, client):
    gv, gv2, hs, p_tn, p_ds, p_tln, p_gv2 = _seed(db)
    h_gv = _h(_login(client, "gv_de"))

    # Sai loại theo phần: TLN vào phần I (phần III cũng sai nhưng I báo trước)
    r = _tao_de(client, h_gv, p_tln, p_ds, p_tn)
    assert r.status_code == 400 and "Phần I" in r.json()["detail"]

    # Câu của GV khác
    r = _tao_de(client, h_gv, p_tn, p_ds, p_gv2)
    assert r.status_code == 400 and "giáo viên khác" in r.json()["detail"]

    # Đề rỗng
    r = client.post("/api/de-thi", headers=h_gv,
                    json={"ten": "X", "thoi_gian_phut": 90,
                          "cau_theo_phan": {"I": [], "II": [], "III": []}})
    assert r.status_code == 400

    # Hợp lệ
    r = _tao_de(client, h_gv, p_tn, p_ds, p_tln)
    assert r.status_code == 200


def test_luong_thi_day_du_va_cham_diem(db, client):
    gv, gv2, hs, p_tn, p_ds, p_tln, p_gv2 = _seed(db)
    h_gv = _h(_login(client, "gv_de"))
    h_hs = _h(_login(client, "hs_de"))

    de_id = _tao_de(client, h_gv, p_tn, p_ds, p_tln).json()["id"]

    # Chưa phát hành: HS không thấy, không bắt đầu được
    assert client.get("/api/de-thi", headers=h_hs).json() == []
    assert client.post(f"/api/de-thi/{de_id}/bat-dau", headers=h_hs).status_code == 400

    client.patch(f"/api/de-thi/{de_id}/phat-hanh", headers=h_gv, json={"phat_hanh": True})
    ds = client.get("/api/de-thi", headers=h_hs).json()
    assert len(ds) == 1 and ds[0]["diem_toi_da"] == 1.75  # 0.25 + 1.0 + 0.5

    # Bắt đầu thi — KHÔNG lộ bất kỳ đáp án nào khi đang thi
    r = client.post(f"/api/de-thi/{de_id}/bat-dau", headers=h_hs)
    assert r.status_code == 200
    bai = r.json()
    assert bai["trang_thai"] == "dang_thi" and bai["con_lai_giay"] > 0
    assert "dap_an_dung" not in r.text and "dap_an_cuoi" not in r.text
    assert '"dap_an":' not in r.text  # đáp án từng ý TNDS

    # Bắt đầu lại khi đang thi → trả về cùng bài (làm tiếp, không mở bài mới)
    r2 = client.post(f"/api/de-thi/{de_id}/bat-dau", headers=h_hs)
    assert r2.json()["bai_thi_id"] == bai["bai_thi_id"]

    cau = {c["phan"]: c for c in bai["cau_list"]}
    bai_lam = {
        str(cau["I"]["de_thi_cau_id"]): "B",                    # đúng → 0.25
        str(cau["II"]["de_thi_cau_id"]): {"a": "Dung", "b": "Sai", "c": "Dung", "d": "Dung"},
        # 3/4 ý đúng → bậc thang 0.5
        str(cau["III"]["de_thi_cau_id"]): "5",                   # đúng → 0.5
    }
    # Autosave
    r = client.patch(f"/api/de-thi/bai/{bai['bai_thi_id']}/luu", headers=h_hs,
                     json={"bai_lam": bai_lam})
    assert r.json()["trang_thai"] == "dang_thi"

    # Nộp
    r = client.post(f"/api/de-thi/bai/{bai['bai_thi_id']}/nop", headers=h_hs, json={})
    kq = r.json()
    assert kq["trang_thai"] == "da_nop"
    assert kq["diem"] == 1.25  # 0.25 + 0.5 + 0.5
    # Sau nộp: có đáp án đúng để ôn tập
    theo_phan = {c["phan"]: c for c in kq["cau_list"]}
    assert theo_phan["I"]["dap_an_dung"]["dap_an_dung"] == "B"
    assert theo_phan["II"]["diem"] == 0.5 and theo_phan["II"]["dung"] is False
    assert theo_phan["III"]["dung"] is True

    # GV xem kết quả lớp
    r = client.get(f"/api/de-thi/{de_id}/ket-qua-lop", headers=h_gv)
    assert r.status_code == 200 and r.json()[0]["diem"] == 1.25

    # Đề đã có bài → không xóa được
    assert client.delete(f"/api/de-thi/{de_id}", headers=h_gv).status_code == 400


def test_het_gio_tu_nop(db, client):
    gv, gv2, hs, p_tn, p_ds, p_tln, p_gv2 = _seed(db)
    h_gv = _h(_login(client, "gv_de"))
    h_hs = _h(_login(client, "hs_de"))
    de_id = _tao_de(client, h_gv, p_tn, p_ds, p_tln).json()["id"]
    client.patch(f"/api/de-thi/{de_id}/phat-hanh", headers=h_gv, json={"phat_hanh": True})

    bai = client.post(f"/api/de-thi/{de_id}/bat-dau", headers=h_hs).json()
    cau_i = next(c for c in bai["cau_list"] if c["phan"] == "I")
    client.patch(f"/api/de-thi/bai/{bai['bai_thi_id']}/luu", headers=h_hs,
                 json={"bai_lam": {str(cau_i["de_thi_cau_id"]): "B"}})

    # Giả lập hết giờ: lùi bat_dau_luc quá 90 phút
    b = db.get(BaiThi, bai["bai_thi_id"])
    b.bat_dau_luc = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=95)
    db.commit()

    # Chỉ cần XEM bài là server tự chốt (đồng hồ server quyết định)
    kq = client.get(f"/api/de-thi/bai/{bai['bai_thi_id']}", headers=h_hs).json()
    assert kq["trang_thai"] == "da_nop"
    assert kq["diem"] == 0.25  # đáp án đã autosave trước hạn vẫn được tính


def test_quyen_bai_thi(db, client):
    gv, gv2, hs, p_tn, p_ds, p_tln, p_gv2 = _seed(db)
    h_gv = _h(_login(client, "gv_de"))
    h_hs = _h(_login(client, "hs_de"))
    de_id = _tao_de(client, h_gv, p_tn, p_ds, p_tln).json()["id"]
    client.patch(f"/api/de-thi/{de_id}/phat-hanh", headers=h_gv, json={"phat_hanh": True})
    bai = client.post(f"/api/de-thi/{de_id}/bat-dau", headers=h_hs).json()

    # HS khác không xem được bài thi của người khác
    hs2 = User(vai_tro=VaiTro.hs, ho_ten="HS2", dang_nhap="hs2_de",
               mat_khau_hash=hash_password("pass"))
    db.add(hs2)
    db.commit()
    r = client.get(f"/api/de-thi/bai/{bai['bai_thi_id']}", headers=_h(_login(client, "hs2_de")))
    assert r.status_code == 404

    # GV khác không xem được kết quả lớp của đề GV này
    r = client.get(f"/api/de-thi/{de_id}/ket-qua-lop", headers=_h(_login(client, "gv2_de")))
    assert r.status_code == 404
