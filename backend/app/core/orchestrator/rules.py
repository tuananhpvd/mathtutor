"""
Quy tắc chuyển trạng thái orchestrator.
Phase 2: TLN. Phase 3: mở rộng TN4PA + TNDS.
"""

from app.core.matching.cas import KetQuaSoKhop
from app.core.orchestrator.directive import ChiThi
from app.core.orchestrator.state import TrangThaiPhien

# ---------- Helpers ----------


def _lay_goi_y(trang_thai: TrangThaiPhien) -> str:
    d = trang_thai.buoc_data()
    if d is None:
        return "hãy tiếp tục suy nghĩ"
    lst = d.get("danh_sach_goi_y", ["hãy thử lại"])
    idx = min(trang_thai.cap_goi_y_hien_tai, len(lst) - 1)
    return lst[idx]


def _tim_buoc_tiep(trang_thai: TrangThaiPhien) -> int | None:
    buoc_hien = trang_thai.buoc_hien_tai
    pham_vi = "ca_bai"
    so_buoc = {s["thu_tu"] for s in trang_thai.steps if s.get("pham_vi", "ca_bai") == pham_vi}
    candidates = sorted(b for b in so_buoc if b > buoc_hien)
    return candidates[0] if candidates else None


def _tim_y_tiep(trang_thai: TrangThaiPhien) -> str | None:
    """TNDS: tìm ý tiếp theo chưa xong."""
    order = ["a", "b", "c", "d"]
    done = trang_thai.trang_thai_y
    for ky_hieu in order:
        if done.get(ky_hieu) != "xong":
            return ky_hieu
    return None


def _chi_thi(trang_thai, y_dinh, y_goi_y, ngu_canh_hs, y_dang_xet=None) -> ChiThi:
    return ChiThi(
        loai_cau=trang_thai.loai_cau,
        y_dinh=y_dinh,
        buoc=trang_thai.buoc_hien_tai,
        y_dang_xet=y_dang_xet or trang_thai.y_hien_tai,
        cap_goi_y=trang_thai.cap_goi_y_hien_tai,
        y_goi_y=y_goi_y,
        ngu_canh_hs=ngu_canh_hs,
    )


# ---------- TLN ----------


def xu_ly_tln(
    trang_thai: TrangThaiPhien,
    ket_qua_so_khop: KetQuaSoKhop | None,
    ngu_canh_hs: str = "",
    yeu_cau_goi_y: bool = False,
) -> tuple[ChiThi, TrangThaiPhien]:
    st = trang_thai

    if ket_qua_so_khop is None and not yeu_cau_goi_y:
        return _chi_thi(st, "dinh_huong", _lay_goi_y(st), ngu_canh_hs), st

    if yeu_cau_goi_y:
        so_max = st.so_goi_y_buoc()
        st.cap_goi_y_hien_tai = min(st.cap_goi_y_hien_tai + 1, so_max - 1)
        st.so_lan_khong_hieu += 1
        return _chi_thi(st, "goi_y", _lay_goi_y(st), ngu_canh_hs), st

    if ket_qua_so_khop == KetQuaSoKhop.KHONG_PHAN_TICH_DUOC:
        return _chi_thi(st, "goi_y",
                        "em hãy nhập lại bằng một biểu thức toán hợp lệ nhé (số, phân số, căn...)",
                        ngu_canh_hs), st

    if ket_qua_so_khop == KetQuaSoKhop.DUNG:
        buoc_tiep = _tim_buoc_tiep(st)
        if buoc_tiep is None:
            st.da_xong = True
            return _chi_thi(st, "ket_thuc",
                            "khen HS đã hoàn thành bài, tóm tắt mạch suy nghĩ (không nêu đáp án)",
                            ngu_canh_hs), st
        st.buoc_hien_tai = buoc_tiep
        st.cap_goi_y_hien_tai = 0
        st.so_lan_sai_lien_tiep = 0
        return _chi_thi(st, "xac_nhan_dung", _lay_goi_y(st), ngu_canh_hs), st

    st.so_lan_sai_lien_tiep += 1
    return _chi_thi(st, "hoi_nguoc", _lay_goi_y(st), ngu_canh_hs), st


# ---------- TN4PA ----------


def xu_ly_tn4pa(
    trang_thai: TrangThaiPhien,
    ket_qua_so_khop: KetQuaSoKhop | None,
    ngu_canh_hs: str = "",
    yeu_cau_goi_y: bool = False,
    bat_buoc_suy_luan: bool = False,  # phải làm đúng >=1 bước trước khi được chọn đáp án
    la_chon_dap_an: bool = False,     # lượt này HS gửi 1 chữ cái A/B/C/D (không phải biểu thức)
) -> tuple[ChiThi, TrangThaiPhien]:
    """TN4PA 2 pha:

    - Pha suy luận (chỉ khi bat_buoc_suy_luan): HS nhập biểu thức kết quả của bước,
      CAS chấm; đúng thì mở khóa cho chọn đáp án.
    - Pha chọn đáp án: HS gửi chữ cái A/B/C/D, so khớp với đáp án đúng.

    Mốc mở khóa: không bắt buộc suy luận, HOẶC đã làm đúng tối thiểu 1 bước
    (buoc_hien_tai > 1).
    """
    st = trang_thai

    def _da_mo_dap_an() -> bool:
        return (not bat_buoc_suy_luan) or st.buoc_hien_tai > 1

    # Lượt mở đầu / chưa nhập gì
    if ket_qua_so_khop is None and not yeu_cau_goi_y:
        return _chi_thi(st, "dinh_huong", _lay_goi_y(st), ngu_canh_hs), st

    # Xin gợi ý
    if yeu_cau_goi_y:
        so_max = st.so_goi_y_buoc()
        st.cap_goi_y_hien_tai = min(st.cap_goi_y_hien_tai + 1, so_max - 1)
        st.so_lan_khong_hieu += 1
        return _chi_thi(st, "goi_y", _lay_goi_y(st), ngu_canh_hs), st

    # Nhập không hợp lệ (biểu thức bước không parse được)
    if ket_qua_so_khop == KetQuaSoKhop.KHONG_PHAN_TICH_DUOC:
        return _chi_thi(st, "goi_y",
                        "em hãy nhập lại bằng một biểu thức toán hợp lệ nhé",
                        ngu_canh_hs), st

    # --- HS chọn đáp án (chữ cái) ---
    if la_chon_dap_an:
        if not _da_mo_dap_an():
            return _chi_thi(st, "goi_y",
                            "em hãy hoàn thành bước suy luận trước khi chọn đáp án nhé",
                            ngu_canh_hs), st
        if ket_qua_so_khop == KetQuaSoKhop.DUNG:
            st.da_xong = True
            return _chi_thi(st, "ket_thuc",
                            "khen HS chọn đúng, nhắc mạch suy nghĩ (không nhắc lại đáp án)",
                            ngu_canh_hs), st
        st.so_lan_sai_lien_tiep += 1
        return _chi_thi(st, "hoi_nguoc",
                        "em đã tính ra kết quả rồi, thử đối chiếu lại với từng phương án xem nhé",
                        ngu_canh_hs), st

    # --- HS nhập biểu thức cho bước suy luận ---
    if ket_qua_so_khop == KetQuaSoKhop.DUNG:
        st.cap_goi_y_hien_tai = 0
        st.so_lan_sai_lien_tiep = 0
        buoc_tiep = _tim_buoc_tiep(st)
        # Mở khóa đáp án sau khi làm đúng tối thiểu 1 bước (đẩy buoc_hien_tai > 1).
        st.buoc_hien_tai = buoc_tiep if buoc_tiep is not None else st.buoc_hien_tai + 1
        return _chi_thi(st, "xac_nhan_dung",
                        "khen HS tính đúng bước này, mời em chọn phương án phù hợp",
                        ngu_canh_hs), st

    # Sai biểu thức bước
    st.so_lan_sai_lien_tiep += 1
    return _chi_thi(st, "hoi_nguoc", _lay_goi_y(st), ngu_canh_hs), st


# ---------- TNDS ----------


def xu_ly_tnds(
    trang_thai: TrangThaiPhien,
    ket_qua_y: KetQuaSoKhop | None,  # kết quả cho ý đang xét
    ngu_canh_hs: str = "",
    yeu_cau_goi_y: bool = False,
) -> tuple[ChiThi, TrangThaiPhien]:
    st = trang_thai

    # Khởi tạo ý đầu tiên nếu chưa có
    if st.y_hien_tai is None:
        st.y_hien_tai = "a"
        if not st.trang_thai_y:
            st.trang_thai_y = {"a": "dang_lam", "b": "chua", "c": "chua", "d": "chua"}
        return _chi_thi(st, "dinh_huong", _lay_goi_y(st), ngu_canh_hs), st

    if yeu_cau_goi_y:
        so_max = st.so_goi_y_buoc()
        st.cap_goi_y_hien_tai = min(st.cap_goi_y_hien_tai + 1, so_max - 1)
        st.so_lan_khong_hieu += 1
        return _chi_thi(st, "goi_y", _lay_goi_y(st), ngu_canh_hs), st

    if ket_qua_y is None:
        return _chi_thi(st, "dinh_huong", _lay_goi_y(st), ngu_canh_hs), st

    if ket_qua_y == KetQuaSoKhop.KHONG_PHAN_TICH_DUOC:
        return _chi_thi(st, "goi_y",
                        "em hãy chọn Đúng hoặc Sai cho ý này nhé",
                        ngu_canh_hs), st

    # HS trả lời ý hiện tại (đúng hoặc sai đều ghi nhận và chuyển ý)
    # (với TNDS, không phạt sai — chỉ ghi nhận để tính điểm cuối)
    st.trang_thai_y[st.y_hien_tai] = "xong"
    if ket_qua_y == KetQuaSoKhop.DUNG:
        st.so_y_dung += 1
    y_tiep = _tim_y_tiep(st)

    if y_tiep is None:
        # Xong cả 4 ý
        st.da_xong = True
        return _chi_thi(st, "tom_tat",
                        "tóm tắt mạch suy nghĩ 4 ý, không nêu đáp án từng ý",
                        ngu_canh_hs), st

    st.y_hien_tai = y_tiep
    st.trang_thai_y[y_tiep] = "dang_lam"
    st.cap_goi_y_hien_tai = 0

    y_dinh = "xac_nhan_dung" if ket_qua_y == KetQuaSoKhop.DUNG else "chuyen_y"
    return _chi_thi(st, y_dinh, _lay_goi_y(st), ngu_canh_hs, y_dang_xet=y_tiep), st
