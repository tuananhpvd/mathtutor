from dataclasses import dataclass

from app.core.matching.cas import CheDoSoKhop, KetQuaSoKhop, tuong_duong
from app.core.matching.scoring import diem_bac_thang


@dataclass
class KetQuaMatch:
    ket_qua: KetQuaSoKhop
    diem: float | None = None  # chỉ TNDS


def so_khop_tnds_mot_y(
    dap_an_nhap: str,
    du_lieu_chuan: dict,
    ky_hieu_y: str,
) -> KetQuaMatch:
    """So khớp một ý TNDS. dap_an_nhap = 'dung'|'sai'."""
    y_list = du_lieu_chuan.get("y", [])
    for y in y_list:
        if y["ky_hieu"] == ky_hieu_y:
            chuan = y["dap_an"]
            eq = str(dap_an_nhap).strip().lower() == chuan.strip().lower()
            return KetQuaMatch(ket_qua=KetQuaSoKhop.DUNG if eq else KetQuaSoKhop.SAI)
    raise ValueError(f"Không tìm thấy ý '{ky_hieu_y}' trong du_lieu_chuan")


def so_khop(
    loai_cau: str,
    dap_an_nhap: str | dict,
    du_lieu_chuan: dict,
    che_do_so_khop: str = "tuong_duong",
) -> KetQuaMatch:
    che_do = CheDoSoKhop(che_do_so_khop)

    if loai_cau == "TN4PA":
        dap_dung = du_lieu_chuan.get("dap_an_dung", "")
        nhap = str(dap_an_nhap).strip().upper()
        eq = nhap == dap_dung.strip().upper()
        return KetQuaMatch(ket_qua=KetQuaSoKhop.DUNG if eq else KetQuaSoKhop.SAI)

    if loai_cau == "TNDS":
        # dap_an_nhap: dict[str, str] {"a": "Dung", "b": "Sai", ...}
        y_list = du_lieu_chuan.get("y", [])
        k = 0
        for y in y_list:
            ky_hieu = y["ky_hieu"]
            chuan = y["dap_an"]
            nhap_y = str(dap_an_nhap.get(ky_hieu, "")).strip()
            if nhap_y.lower() == chuan.lower():
                k += 1
        diem = diem_bac_thang(k)
        ket = KetQuaSoKhop.DUNG if k == len(y_list) else KetQuaSoKhop.SAI
        return KetQuaMatch(ket_qua=ket, diem=diem)

    if loai_cau == "TLN":
        chuan = du_lieu_chuan.get("dap_an_cuoi", "")
        lam_tron = du_lieu_chuan.get("quy_tac_lam_tron")
        ket = tuong_duong(str(dap_an_nhap), str(chuan), che_do, lam_tron)
        return KetQuaMatch(ket_qua=ket)

    raise ValueError(f"Loại câu không hỗ trợ: {loai_cau}")
