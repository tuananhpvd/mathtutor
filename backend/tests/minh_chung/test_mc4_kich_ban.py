"""
MC-4 — Chạy 30 kịch bản (data_mc4_kich_ban.py) qua ĐÚNG bộ điều phối sản phẩm dùng
(core/orchestrator/rules.py), so kết quả cuối `da_xong` với `da_xong_mong_doi`, xuất báo cáo
cho thuyết minh Bảng 13.

Bất biến kiểm chung cho MỌI kịch bản (không chỉ riêng từng ca): cấp gợi ý dùng KHÔNG BAO GIỜ
vượt ngưỡng tối đa của độ khó — đây chính là hành vi "gợi ý bắc thang 2-5 mức" mục IV.1.7 nói
tới, kiểm bằng máy chứ không chỉ đọc code.
"""

import csv
from pathlib import Path

from app.core.matching.cas import KetQuaSoKhop
from app.core.orchestrator.rules import xu_ly_tln, xu_ly_tn4pa, xu_ly_tnds
from app.core.orchestrator.state import TrangThaiPhien

from .data_mc4_kich_ban import KICH_BAN, SO_GOI_Y_THEO_DO_KHO, _steps_tln, _steps_tn4pa, _steps_tnds

THU_MUC_BAO_CAO = Path(__file__).resolve().parents[3] / "docs" / "minh_chung"


def _chay_tln(kb: dict) -> TrangThaiPhien:
    st = TrangThaiPhien(loai_cau="TLN", steps=_steps_tln(kb["do_kho"], kb["so_buoc"]))
    for hv in kb["hanh_vi"]:
        loai = hv[0]
        if loai == "dung":
            _, st = xu_ly_tln(st, KetQuaSoKhop.DUNG, "hs nhap dung")
        elif loai == "sai":
            _, st = xu_ly_tln(st, KetQuaSoKhop.SAI, "hs nhap sai")
        elif loai == "khong_doc_duoc":
            _, st = xu_ly_tln(st, KetQuaSoKhop.KHONG_PHAN_TICH_DUOC, "???")
        elif loai == "chua_du_co_so":
            _, st = xu_ly_tln(st, KetQuaSoKhop.CHUA_DU_CO_SO, "sqrt(x-1)")
        elif loai == "goi_y":
            _, st = xu_ly_tln(st, None, "", yeu_cau_goi_y=True)
        if st.da_xong:
            break
    return st


def _chay_tn4pa(kb: dict) -> TrangThaiPhien:
    st = TrangThaiPhien(loai_cau="TN4PA", steps=_steps_tn4pa(kb["do_kho"], kb["so_buoc"]))
    bb = kb["bat_buoc_suy_luan"]
    for hv in kb["hanh_vi"]:
        loai = hv[0]
        if loai == "chon_dung":
            _, st = xu_ly_tn4pa(st, KetQuaSoKhop.DUNG, "em chon", bat_buoc_suy_luan=bb,
                                la_chon_dap_an=True)
        elif loai == "chon_sai":
            _, st = xu_ly_tn4pa(st, KetQuaSoKhop.SAI, "em chon", bat_buoc_suy_luan=bb,
                                la_chon_dap_an=True)
        elif loai == "suy_luan_dung":
            _, st = xu_ly_tn4pa(st, KetQuaSoKhop.DUNG, "y'=...", bat_buoc_suy_luan=bb,
                                la_chon_dap_an=False)
        elif loai == "suy_luan_sai":
            _, st = xu_ly_tn4pa(st, KetQuaSoKhop.SAI, "y'=sai", bat_buoc_suy_luan=bb,
                                la_chon_dap_an=False)
        elif loai == "suy_luan_khong_doc_duoc":
            _, st = xu_ly_tn4pa(st, KetQuaSoKhop.KHONG_PHAN_TICH_DUOC, "???",
                                bat_buoc_suy_luan=bb, la_chon_dap_an=False)
        elif loai == "suy_luan_chua_du_co_so":
            _, st = xu_ly_tn4pa(st, KetQuaSoKhop.CHUA_DU_CO_SO, "sqrt(x-1)",
                                bat_buoc_suy_luan=bb, la_chon_dap_an=False)
        elif loai == "goi_y":
            _, st = xu_ly_tn4pa(st, None, "", yeu_cau_goi_y=True)
        if st.da_xong:
            break
    return st


def _chay_tnds(kb: dict) -> TrangThaiPhien:
    st = TrangThaiPhien(loai_cau="TNDS", steps=_steps_tnds(kb["do_kho"]))
    # Khởi tạo ý đầu tiên (dinh_huong) trước khi feed hành vi — đúng luồng thật.
    _, st = xu_ly_tnds(st, None, "")
    thu_tu_y = ["a", "b", "c", "d"]

    def bb_hien_tai():
        idx = thu_tu_y.index(st.y_hien_tai)
        return kb["bat_buoc_suy_luan"][idx]

    for hv in kb["hanh_vi"]:
        loai = hv[0]
        bb = bb_hien_tai()
        if loai == "chot_dung":
            _, st = xu_ly_tnds(st, KetQuaSoKhop.DUNG, "Dung", bat_buoc_suy_luan_y=bb,
                               la_chon_dung_sai=True)
        elif loai == "chot_sai":
            _, st = xu_ly_tnds(st, KetQuaSoKhop.SAI, "Sai", bat_buoc_suy_luan_y=bb,
                               la_chon_dung_sai=True)
        elif loai == "suy_luan_dung":
            _, st = xu_ly_tnds(st, KetQuaSoKhop.DUNG, "y'=...", bat_buoc_suy_luan_y=bb,
                               la_chon_dung_sai=False)
        elif loai == "suy_luan_sai":
            _, st = xu_ly_tnds(st, KetQuaSoKhop.SAI, "y'=sai", bat_buoc_suy_luan_y=bb,
                               la_chon_dung_sai=False)
        elif loai == "suy_luan_khong_doc_duoc":
            _, st = xu_ly_tnds(st, KetQuaSoKhop.KHONG_PHAN_TICH_DUOC, "???",
                               bat_buoc_suy_luan_y=bb, la_chon_dung_sai=False)
        elif loai == "suy_luan_chua_du_co_so":
            _, st = xu_ly_tnds(st, KetQuaSoKhop.CHUA_DU_CO_SO, "sqrt(x-1)",
                               bat_buoc_suy_luan_y=bb, la_chon_dung_sai=False)
        elif loai == "goi_y":
            _, st = xu_ly_tnds(st, None, "", yeu_cau_goi_y=True)
        if st.da_xong:
            break
    return st


_CHAY_THEO_LOAI = {"TLN": _chay_tln, "TN4PA": _chay_tn4pa, "TNDS": _chay_tnds}


def _chay_mot_kich_ban(kb: dict) -> dict:
    st = _CHAY_THEO_LOAI[kb["loai_cau"]](kb)
    da_xong_dung = st.da_xong == kb["da_xong_mong_doi"]
    so_max = SO_GOI_Y_THEO_DO_KHO[kb["do_kho"]]
    gioi_han_dung = st.cap_goi_y_hien_tai <= so_max - 1  # bất biến: không vượt trần
    return {
        "id": kb["id"], "loai_cau": kb["loai_cau"], "do_kho": kb["do_kho"],
        "mo_ta": kb["mo_ta"], "da_xong_mong_doi": kb["da_xong_mong_doi"],
        "da_xong_thuc_te": st.da_xong, "cap_goi_y_cuoi": st.cap_goi_y_hien_tai,
        "so_goi_y_toi_da": so_max,
        "dung": da_xong_dung and gioi_han_dung,
    }


def test_mc4_kich_ban_luyen_goi_mo():
    ket_qua = [_chay_mot_kich_ban(kb) for kb in KICH_BAN]
    so_dung = sum(1 for r in ket_qua if r["dung"])
    tong = len(ket_qua)
    lech = [r for r in ket_qua if not r["dung"]]

    THU_MUC_BAO_CAO.mkdir(parents=True, exist_ok=True)
    with open(THU_MUC_BAO_CAO / "mc4_kich_ban_chi_tiet.csv", "w",
              newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=[
            "id", "loai_cau", "do_kho", "mo_ta", "da_xong_mong_doi", "da_xong_thuc_te",
            "cap_goi_y_cuoi", "so_goi_y_toi_da", "dung",
        ])
        w.writeheader()
        w.writerows(ket_qua)

    with open(THU_MUC_BAO_CAO / "mc4_kich_ban_tom_tat.md", "w", encoding="utf-8") as f:
        f.write("# MC-4 — Kết quả 30 kịch bản luyện gợi mở\n\n")
        f.write(f"**{so_dung}/{tong} đúng theo kỳ vọng** ({so_dung / tong * 100:.1f}%).\n\n")
        for loai in ("TLN", "TN4PA", "TNDS"):
            cac_ca = [r for r in ket_qua if r["loai_cau"] == loai]
            sd = sum(1 for r in cac_ca if r["dung"])
            f.write(f"- {loai}: {sd}/{len(cac_ca)}\n")
        f.write("\nSinh bằng `tests/minh_chung/data_mc4_kich_ban.py`, chạy qua "
                "`core/orchestrator/rules.py` thật. Chi tiết: `mc4_kich_ban_chi_tiet.csv`.\n\n")
        if lech:
            f.write(f"## {len(lech)} kịch bản lệch kỳ vọng\n\n")
            f.write("| id | loại | độ khó | mô tả | mong đợi | thực tế | cấp gợi ý cuối/tối đa |\n")
            f.write("|---|---|---|---|---|---|---|\n")
            for r in lech:
                f.write(f"| {r['id']} | {r['loai_cau']} | {r['do_kho']} | {r['mo_ta']} "
                        f"| {r['da_xong_mong_doi']} | {r['da_xong_thuc_te']} "
                        f"| {r['cap_goi_y_cuoi']}/{r['so_goi_y_toi_da']} |\n")
        else:
            f.write("Không có kịch bản nào lệch kỳ vọng.\n")

    assert so_dung == tong, f"{tong - so_dung} kịch bản lệch kỳ vọng — xem báo cáo chi tiết"
