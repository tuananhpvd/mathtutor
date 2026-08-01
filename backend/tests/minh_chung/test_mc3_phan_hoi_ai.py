"""
MC-3 — Chạy corpus 250 phản hồi AI mô phỏng (data_mc3_phan_hoi_ai.py) qua lớp chốt chặn
sản phẩm dùng (`kiem_tra_ro_ri()`), xuất báo cáo cho thuyết minh Bảng 13.

Đọc `data_mc3_phan_hoi_ai.py` để biết CÁCH DỰNG corpus trước khi diễn giải con số — tỉ lệ
chặn/tổng phụ thuộc tỉ lệ câu rủi ro/an toàn được dựng, không phải một hằng số nội tại của
bộ lọc.
"""

import csv
from pathlib import Path

from app.core.guard.leak import MucDoRoRi, kiem_tra_ro_ri

from .data_mc3_phan_hoi_ai import CAC_CA

THU_MUC_BAO_CAO = Path(__file__).resolve().parents[3] / "docs" / "minh_chung"


def _chay_mot_ca(ca: dict) -> dict:
    kq = kiem_tra_ro_ri(ca["noi_dung"], None, "TLN")
    chan_thuc_te = kq.muc_do == MucDoRoRi.ro_ri
    dung = chan_thuc_te == ca["ky_vong_chan"]
    return {**ca, "muc_do_thuc_te": kq.muc_do.value, "chan_thuc_te": chan_thuc_te, "dung": dung}


def test_mc3_an_toan_phan_hoi_ai():
    ket_qua = [_chay_mot_ca(c) for c in CAC_CA]
    tong = len(ket_qua)
    so_bi_chan = sum(1 for r in ket_qua if r["chan_thuc_te"])

    so_rui_ro = sum(1 for c in CAC_CA if c["ky_vong_chan"])
    so_an_toan = tong - so_rui_ro
    chan_dung_rui_ro = sum(1 for r in ket_qua if r["ky_vong_chan"] and r["chan_thuc_te"])
    chan_nham_an_toan = sum(1 for r in ket_qua if not r["ky_vong_chan"] and r["chan_thuc_te"])
    lech = [r for r in ket_qua if not r["dung"]]

    THU_MUC_BAO_CAO.mkdir(parents=True, exist_ok=True)
    with open(THU_MUC_BAO_CAO / "mc3_phan_hoi_ai_chi_tiet.csv", "w",
              newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=[
            "id", "nhom", "noi_dung", "ky_vong_chan", "muc_do_thuc_te", "chan_thuc_te", "dung",
        ])
        w.writeheader()
        w.writerows(ket_qua)

    with open(THU_MUC_BAO_CAO / "mc3_phan_hoi_ai_tom_tat.md", "w", encoding="utf-8") as f:
        f.write("# MC-3 — Kết quả kiểm chứng an toàn phản hồi AI (corpus mô phỏng)\n\n")
        f.write(f"**Corpus {tong} câu** = {so_an_toan} câu AN TOÀN (mô phỏng phản hồi Socratic "
                f"bình thường) + {so_rui_ro} câu RỦI RO cố ý (mô phỏng các dạng lộ đáp án "
                f"thường gặp) — xem `data_mc3_phan_hoi_ai.py` mục đầu file để biết đầy đủ "
                f"phương pháp dựng.\n\n")
        f.write(f"- **{so_bi_chan}/{tong} câu bị chặn/thay** "
                f"({so_bi_chan / tong * 100:.1f}% — con số này PHỤ THUỘC tỉ lệ dựng ở trên, "
                f"không phải hằng số nội tại của bộ lọc).\n")
        f.write(f"- Chặn đúng {chan_dung_rui_ro}/{so_rui_ro} câu rủi ro "
                f"({chan_dung_rui_ro / so_rui_ro * 100:.1f}% — đo khả năng phát hiện).\n")
        f.write(f"- Chặn NHẦM {chan_nham_an_toan}/{so_an_toan} câu an toàn "
                f"({chan_nham_an_toan / so_an_toan * 100:.1f}% — đo tỉ lệ chặn nhầm, mục "
                f"thuyết minh VII.2 tự nhận trước đây chưa đo được).\n\n")
        f.write("Chi tiết từng câu: `mc3_phan_hoi_ai_chi_tiet.csv`.\n\n")
        if lech:
            f.write(f"## {len(lech)} câu lệch kỳ vọng\n\n")
            f.write("| id | nhóm | nội dung | kỳ vọng chặn | thực tế |\n")
            f.write("|---|---|---|---|---|\n")
            for r in lech:
                f.write(f"| {r['id']} | {r['nhom']} | {r['noi_dung']} | {r['ky_vong_chan']} "
                        f"| {r['muc_do_thuc_te']} |\n")
        else:
            f.write("Không có câu nào lệch kỳ vọng.\n")

    # Ngưỡng khóa hồi quy riêng cho từng phía — không gộp chung 1 ngưỡng vì ý nghĩa khác
    # nhau: bỏ lọt đáp án nguy hiểm hơn chặn nhầm (chặn nhầm chỉ làm mất 1 câu, bỏ lọt làm
    # lộ đáp án thật).
    ty_le_phat_hien = chan_dung_rui_ro / so_rui_ro
    ty_le_chan_nham = chan_nham_an_toan / so_an_toan
    assert ty_le_phat_hien >= 0.80, (
        f"Tỉ lệ phát hiện rủi ro giảm còn {ty_le_phat_hien:.1%} — xem báo cáo chi tiết"
    )
    assert ty_le_chan_nham <= 0.10, (
        f"Tỉ lệ chặn nhầm tăng lên {ty_le_chan_nham:.1%} — xem báo cáo chi tiết"
    )
