"""
MC-1 — Chạy bộ 100 biểu thức (data_mc1_bieu_thuc.py) qua đúng hàm CAS sản phẩm dùng
(`tuong_duong()`), so với ky_vong, xuất báo cáo cho thuyết minh Bảng 13.

Con số công bố PHẢI là con số hàm này in ra — KHÔNG được sửa `data_mc1_bieu_thuc.py` để
nắn cho khớp một con số định trước. Nếu chạy ra khác với Bảng 13 trong thuyết minh, phải sửa
thuyết minh theo con số thật, kèm giải thích các ca lệch.
"""

import csv
from pathlib import Path

from app.core.matching.cas import KetQuaSoKhop, tuong_duong

from .data_mc1_bieu_thuc import CAC_CA

THU_MUC_BAO_CAO = Path(__file__).resolve().parents[3] / "docs" / "minh_chung"


def _chay_mot_ca(ca: dict) -> dict:
    ket_qua = tuong_duong(
        ca["hs_nhap"], ca["chuan"],
        che_do=ca["che_do"], lam_tron=ca["lam_tron"],
    )
    dung = ket_qua.value == ca["ky_vong"]
    return {**ca, "ket_qua_thuc_te": ket_qua.value, "dung": dung}


def test_mc1_do_chinh_xac_bieu_thuc():
    ket_qua = [_chay_mot_ca(c) for c in CAC_CA]
    so_dung = sum(1 for r in ket_qua if r["dung"])
    tong = len(ket_qua)
    lech = [r for r in ket_qua if not r["dung"]]

    THU_MUC_BAO_CAO.mkdir(parents=True, exist_ok=True)
    duong_dan_csv = THU_MUC_BAO_CAO / "mc1_bieu_thuc_chi_tiet.csv"
    with open(duong_dan_csv, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=[
            "id", "nhom", "hs_nhap", "chuan", "che_do", "lam_tron",
            "ky_vong", "ket_qua_thuc_te", "dung", "ghi_chu",
        ])
        w.writeheader()
        w.writerows(ket_qua)

    duong_dan_md = THU_MUC_BAO_CAO / "mc1_bieu_thuc_tom_tat.md"
    with open(duong_dan_md, "w", encoding="utf-8") as f:
        f.write("# MC-1 — Kết quả kiểm chứng CAS (chấm toán bằng SymPy)\n\n")
        f.write(f"**{so_dung}/{tong} đúng theo kỳ vọng** "
                f"({so_dung / tong * 100:.1f}%).\n\n")
        f.write("Sinh bằng `tests/minh_chung/data_mc1_bieu_thuc.py` (random.seed cố định, "
                "chạy lại ra đúng bộ này). Chi tiết từng ca: `mc1_bieu_thuc_chi_tiet.csv`.\n\n")
        if lech:
            f.write(f"## {len(lech)} ca lệch kỳ vọng\n\n")
            f.write("| id | nhóm | hs_nhap | chuan | kỳ vọng | thực tế | ghi chú |\n")
            f.write("|---|---|---|---|---|---|---|\n")
            for r in lech:
                f.write(f"| {r['id']} | {r['nhom']} | `{r['hs_nhap']}` | `{r['chuan']}` "
                        f"| {r['ky_vong']} | {r['ket_qua_thuc_te']} | {r['ghi_chu']} |\n")
        else:
            f.write("Không có ca nào lệch kỳ vọng.\n")

    # Ngưỡng khóa hồi quy: KHÔNG phải "phải đạt 100%" (điều đó sẽ mời gọi nắn dữ liệu cho
    # qua) — chỉ đảm bảo CAS không tệ đi so với lần chạy đã công bố trong thuyết minh dưới
    # 90%. Nếu tương lai < 90%, đây là hồi quy THẬT cần điều tra, không phải bug ở bộ test.
    assert so_dung / tong >= 0.90, (
        f"Độ chính xác CAS giảm còn {so_dung}/{tong} — xem {duong_dan_md} để biết ca nào lệch"
    )


def test_mc1_du_lieu_du_lieu_hop_le():
    """Khóa cấu trúc dữ liệu — tránh ca nào đó bị thiếu trường do sửa generator sai."""
    assert len(CAC_CA) >= 90, "Bộ dữ liệu MC-1 phải còn xấp xỉ 100 ca (giảm nửa từ 200 gốc)"
    ky_vong_hop_le = {k.value for k in KetQuaSoKhop}
    for c in CAC_CA:
        assert c["ky_vong"] in ky_vong_hop_le
        assert c["hs_nhap"] is not None and c["chuan"] is not None
