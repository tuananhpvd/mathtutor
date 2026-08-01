"""
MC-2 — Chạy bộ 20 ca (data_mc2_chong_lo_dap_an.py) qua đúng lớp chốt chặn sản phẩm dùng
(`kiem_tra_ro_ri()`), xuất báo cáo cho thuyết minh Bảng 13.

Con số công bố PHẢI là con số hàm này in ra. Nếu chạy ra khác thuyết minh, sửa thuyết minh
theo kết quả thật — không sửa dữ liệu để nắn cho khớp một con số định trước.
"""

import csv
from pathlib import Path

from app.core.guard.leak import MucDoRoRi, kiem_tra_ro_ri

from .data_mc2_chong_lo_dap_an import CAC_CA

THU_MUC_BAO_CAO = Path(__file__).resolve().parents[3] / "docs" / "minh_chung"


def _chay_mot_ca(ca: dict) -> dict:
    kq = kiem_tra_ro_ri(ca["noi_dung"], ca["gia_tri_dap_an"], ca["loai_cau"])
    chan_thuc_te = kq.muc_do == MucDoRoRi.ro_ri
    dung = chan_thuc_te == ca["ky_vong_chan"]
    return {**ca, "muc_do_thuc_te": kq.muc_do.value, "chan_thuc_te": chan_thuc_te,
            "dung": dung, "ly_do_loc": "; ".join(kq.ly_do)}


def test_mc2_do_chinh_xac_chong_lo_dap_an():
    ket_qua = [_chay_mot_ca(c) for c in CAC_CA]
    so_dung = sum(1 for r in ket_qua if r["dung"])
    tong = len(ket_qua)
    lech = [r for r in ket_qua if not r["dung"]]

    so_rui_ro = sum(1 for c in CAC_CA if c["ky_vong_chan"])
    so_an_toan = tong - so_rui_ro
    chan_dung_rui_ro = sum(1 for r in ket_qua if r["ky_vong_chan"] and r["chan_thuc_te"])
    khong_chan_nham_an_toan = sum(
        1 for r in ket_qua if not r["ky_vong_chan"] and not r["chan_thuc_te"]
    )

    THU_MUC_BAO_CAO.mkdir(parents=True, exist_ok=True)
    with open(THU_MUC_BAO_CAO / "mc2_chong_lo_dap_an_chi_tiet.csv", "w",
              newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=[
            "id", "nhom", "noi_dung", "gia_tri_dap_an", "loai_cau",
            "ky_vong_chan", "muc_do_thuc_te", "chan_thuc_te", "dung", "ly_do_loc", "ghi_chu",
        ])
        w.writeheader()
        w.writerows(ket_qua)

    with open(THU_MUC_BAO_CAO / "mc2_chong_lo_dap_an_tom_tat.md", "w", encoding="utf-8") as f:
        f.write("# MC-2 — Kết quả kiểm chứng chốt chặn rò rỉ đáp án\n\n")
        f.write(f"**{so_dung}/{tong} đúng theo kỳ vọng** ({so_dung / tong * 100:.1f}%).\n\n")
        f.write(f"- Chặn đúng {chan_dung_rui_ro}/{so_rui_ro} ca RỦI RO cố ý "
                f"(đo khả năng phát hiện lộ đáp án).\n")
        f.write(f"- Không chặn nhầm {khong_chan_nham_an_toan}/{so_an_toan} ca AN TOÀN cố ý "
                f"(đo tỉ lệ chặn nhầm — mục thuyết minh VII.2 tự nhận trước đây chưa đo được).\n\n")
        f.write("Sinh bằng `tests/minh_chung/data_mc2_chong_lo_dap_an.py`. "
                "Chi tiết từng ca: `mc2_chong_lo_dap_an_chi_tiet.csv`.\n\n")
        if lech:
            f.write(f"## {len(lech)} ca lệch kỳ vọng\n\n")
            f.write("| id | nhóm | nội dung | kỳ vọng chặn | thực tế | lý do lọc | ghi chú |\n")
            f.write("|---|---|---|---|---|---|---|\n")
            for r in lech:
                f.write(f"| {r['id']} | {r['nhom']} | {r['noi_dung']} | {r['ky_vong_chan']} "
                        f"| {r['muc_do_thuc_te']} | {r['ly_do_loc'] or '-'} | {r['ghi_chu']} |\n")
        else:
            f.write("Không có ca nào lệch kỳ vọng.\n")

    # Ngưỡng khóa hồi quy — không phải "phải 100%" (tránh mời gọi nắn dữ liệu). Bộ lọc dựa
    # trên từ khóa/regex nên CÓ giới hạn thật (xem ca #2) — ngưỡng 80% đủ bắt hồi quy nặng
    # (vd sửa nhầm làm mất hẳn một nhóm từ khóa) mà không đòi hỏi bộ lọc hoàn hảo.
    assert so_dung / tong >= 0.80, (
        f"Độ chính xác chốt chặn giảm còn {so_dung}/{tong} — xem báo cáo để biết ca nào lệch"
    )
