"""
MC-4 — 30 kịch bản luyện gợi mở (thuyết minh Bảng 13, dòng "HS - luyện gợi mở"; giảm nửa từ
60 theo yêu cầu rút gọn thời gian).

Mỗi kịch bản là một CHUỖI HÀNH VI đi qua ĐÚNG bộ điều phối sản phẩm dùng
(`xu_ly_tln`/`xu_ly_tn4pa`/`xu_ly_tnds` — core/orchestrator/rules.py), không phải mô phỏng
riêng. Phủ đủ 3 loại câu × 3 mức độ khó (2/3/4 gợi ý) × các kiểu hành vi: đúng ngay, sai rồi
đúng, xin gợi ý tới cạn, nhập không đọc được (KHONG_PHAN_TICH_DUOC), thiếu điều kiện xác định
(CHUA_DU_CO_SO — mới thêm phần B), không bao giờ đúng.

Mỗi bước hành vi là một tuple (loai_hanh_vi, ...tham_so). `da_xong_mong_doi` được suy luận
TRỰC TIẾP từ logic đã có 74 test đơn vị khóa (test_orchestrator.py, test_tn4pa_tnds.py) —
không phải đoán.
"""

# Hành vi: "dung" | "sai" | "khong_doc_duoc" | "chua_du_co_so" | "goi_y" (xin gợi ý, không nộp)
SO_GOI_Y_THEO_DO_KHO = {"de": 2, "tb": 3, "kho": 4}


def _steps_tln(do_kho: str, so_buoc: int) -> list[dict]:
    n = SO_GOI_Y_THEO_DO_KHO[do_kho]
    return [
        {"thu_tu": i, "pham_vi": "ca_bai", "mo_ta": f"bước {i}",
         "bieu_thuc_ket_qua": "1", "danh_sach_goi_y": [f"gợi {j}" for j in range(n)]}
        for i in range(1, so_buoc + 1)
    ]


def _steps_tn4pa(do_kho: str, so_buoc_suy_luan: int) -> list[dict]:
    n = SO_GOI_Y_THEO_DO_KHO[do_kho]
    return [
        {"thu_tu": i, "pham_vi": "ca_bai", "mo_ta": f"bước {i}",
         "bieu_thuc_ket_qua": "1", "danh_sach_goi_y": [f"gợi {j}" for j in range(n)]}
        for i in range(1, so_buoc_suy_luan + 1)
    ]


def _steps_tnds(do_kho: str) -> list[dict]:
    n = SO_GOI_Y_THEO_DO_KHO[do_kho]
    return [
        {"thu_tu": 1, "pham_vi": p, "mo_ta": f"ý {p}", "bieu_thuc_ket_qua": "Dung",
         "danh_sach_goi_y": [f"gợi {j}" for j in range(n)]}
        for p in ("a", "b", "c", "d")
    ]


KICH_BAN: list[dict] = [
    # ── TLN (10) ──────────────────────────────────────────────────────────────
    {"id": 1, "loai_cau": "TLN", "do_kho": "de", "so_buoc": 1,
     "hanh_vi": [("dung",)], "da_xong_mong_doi": True,
     "mo_ta": "Đúng ngay bước duy nhất (dễ)"},
    {"id": 2, "loai_cau": "TLN", "do_kho": "tb", "so_buoc": 2,
     "hanh_vi": [("dung",), ("dung",)], "da_xong_mong_doi": True,
     "mo_ta": "Đúng liên tiếp 2 bước (trung bình)"},
    {"id": 3, "loai_cau": "TLN", "do_kho": "tb", "so_buoc": 1,
     "hanh_vi": [("sai",), ("dung",)], "da_xong_mong_doi": True,
     "mo_ta": "Sai 1 lần rồi tự sửa đúng"},
    {"id": 4, "loai_cau": "TLN", "do_kho": "kho", "so_buoc": 2,
     "hanh_vi": [("goi_y",), ("sai",), ("dung",), ("dung",)], "da_xong_mong_doi": True,
     "mo_ta": "Xin gợi ý rồi sai rồi đúng, sang bước 2 đúng luôn"},
    {"id": 5, "loai_cau": "TLN", "do_kho": "kho", "so_buoc": 1,
     "hanh_vi": [("goi_y",), ("goi_y",), ("goi_y",), ("goi_y",), ("goi_y",)],
     "da_xong_mong_doi": False, "mo_ta": "Xin gợi ý vượt ngưỡng (4 mức) — chưa hoàn thành"},
    {"id": 6, "loai_cau": "TLN", "do_kho": "de", "so_buoc": 1,
     "hanh_vi": [("khong_doc_duoc",), ("dung",)], "da_xong_mong_doi": True,
     "mo_ta": "Nhập không đọc được rồi nhập lại đúng — không tính là sai"},
    {"id": 7, "loai_cau": "TLN", "do_kho": "tb", "so_buoc": 3,
     "hanh_vi": [("dung",), ("dung",), ("dung",)], "da_xong_mong_doi": True,
     "mo_ta": "Đúng liên tiếp cả 3 bước"},
    {"id": 8, "loai_cau": "TLN", "do_kho": "kho", "so_buoc": 2,
     "hanh_vi": [("sai",), ("sai",), ("sai",), ("dung",), ("dung",)],
     "da_xong_mong_doi": True, "mo_ta": "Sai 3 lần liên tiếp rồi tự sửa đúng"},
    {"id": 9, "loai_cau": "TLN", "do_kho": "de", "so_buoc": 1,
     "hanh_vi": [("chua_du_co_so",), ("dung",)], "da_xong_mong_doi": True,
     "mo_ta": "Biểu thức có căn thiếu điều kiện xác định rồi bổ sung đúng (phần B)"},
    {"id": 10, "loai_cau": "TLN", "do_kho": "tb", "so_buoc": 1,
     "hanh_vi": [("sai",), ("sai",)], "da_xong_mong_doi": False,
     "mo_ta": "Sai mãi, không bao giờ đúng — chưa hoàn thành"},

    # ── TN4PA (10) ────────────────────────────────────────────────────────────
    {"id": 11, "loai_cau": "TN4PA", "do_kho": "de", "bat_buoc_suy_luan": False,
     "so_buoc": 1, "hanh_vi": [("chon_dung",)], "da_xong_mong_doi": True,
     "mo_ta": "Không bắt buộc suy luận, chọn đúng ngay"},
    {"id": 12, "loai_cau": "TN4PA", "do_kho": "tb", "bat_buoc_suy_luan": False,
     "so_buoc": 1, "hanh_vi": [("chon_sai",), ("chon_dung",)], "da_xong_mong_doi": True,
     "mo_ta": "Chọn sai rồi chọn đúng"},
    {"id": 13, "loai_cau": "TN4PA", "do_kho": "tb", "bat_buoc_suy_luan": True,
     "so_buoc": 1, "hanh_vi": [("suy_luan_dung",), ("chon_dung",)],
     "da_xong_mong_doi": True, "mo_ta": "Bắt buộc suy luận: suy luận đúng rồi chọn đúng"},
    {"id": 14, "loai_cau": "TN4PA", "do_kho": "kho", "bat_buoc_suy_luan": True,
     "so_buoc": 1, "hanh_vi": [("suy_luan_sai",), ("suy_luan_dung",), ("chon_dung",)],
     "da_xong_mong_doi": True, "mo_ta": "Suy luận sai rồi đúng rồi chọn đúng"},
    {"id": 15, "loai_cau": "TN4PA", "do_kho": "tb", "bat_buoc_suy_luan": True,
     "so_buoc": 1, "hanh_vi": [("chon_dung",)], "da_xong_mong_doi": False,
     "mo_ta": "Chọn đáp án ngay khi CHƯA mở khóa (bắt buộc suy luận) — bị chặn"},
    {"id": 16, "loai_cau": "TN4PA", "do_kho": "de", "bat_buoc_suy_luan": True,
     "so_buoc": 2, "hanh_vi": [("suy_luan_dung",), ("suy_luan_dung",), ("chon_dung",)],
     "da_xong_mong_doi": True, "mo_ta": "2 bước suy luận đúng liên tiếp rồi chọn đúng"},
    {"id": 17, "loai_cau": "TN4PA", "do_kho": "tb", "bat_buoc_suy_luan": True,
     "so_buoc": 1, "hanh_vi": [("suy_luan_chua_du_co_so",), ("suy_luan_dung",), ("chon_dung",)],
     "da_xong_mong_doi": True, "mo_ta": "Suy luận thiếu điều kiện xác định rồi đúng (phần B)"},
    {"id": 18, "loai_cau": "TN4PA", "do_kho": "de", "bat_buoc_suy_luan": False,
     "so_buoc": 1, "hanh_vi": [("goi_y",), ("goi_y",), ("chon_dung",)],
     "da_xong_mong_doi": True, "mo_ta": "Xin gợi ý 2 lần rồi chọn đúng"},
    {"id": 19, "loai_cau": "TN4PA", "do_kho": "kho", "bat_buoc_suy_luan": True,
     "so_buoc": 1, "hanh_vi": [("suy_luan_khong_doc_duoc",), ("suy_luan_dung",), ("chon_dung",)],
     "da_xong_mong_doi": True, "mo_ta": "Suy luận nhập không đọc được rồi đúng"},
    {"id": 20, "loai_cau": "TN4PA", "do_kho": "de", "bat_buoc_suy_luan": False,
     "so_buoc": 1, "hanh_vi": [("chon_sai",), ("chon_sai",)], "da_xong_mong_doi": False,
     "mo_ta": "Chọn sai 2 lần liên tiếp — chưa hoàn thành"},

    # ── TNDS (10, luôn 4 ý a-b-c-d) ───────────────────────────────────────────
    {"id": 21, "loai_cau": "TNDS", "do_kho": "de", "bat_buoc_suy_luan": [False] * 4,
     "hanh_vi": [("chot_dung",), ("chot_dung",), ("chot_dung",), ("chot_dung",)],
     "da_xong_mong_doi": True, "mo_ta": "Chốt đúng cả 4 ý liên tiếp, không bắt buộc suy luận"},
    {"id": 22, "loai_cau": "TNDS", "do_kho": "tb", "bat_buoc_suy_luan": [True, False, False, False],
     "hanh_vi": [("suy_luan_dung",), ("chot_dung",), ("chot_dung",), ("chot_dung",), ("chot_dung",)],
     "da_xong_mong_doi": True, "mo_ta": "Ý a bắt buộc suy luận đúng rồi chốt, 3 ý sau chốt thẳng"},
    {"id": 23, "loai_cau": "TNDS", "do_kho": "tb", "bat_buoc_suy_luan": [False] * 4,
     "hanh_vi": [("chot_dung",), ("chot_sai",), ("chot_dung",), ("chot_dung",), ("chot_dung",)],
     "da_xong_mong_doi": True, "mo_ta": "Ý b chốt sai trước, ở lại rồi chốt đúng, vẫn hoàn thành"},
    {"id": 24, "loai_cau": "TNDS", "do_kho": "kho", "bat_buoc_suy_luan": [True] * 4,
     "hanh_vi": [
         ("suy_luan_dung",), ("chot_dung",), ("suy_luan_dung",), ("chot_dung",),
         ("suy_luan_dung",), ("chot_dung",), ("suy_luan_dung",), ("chot_dung",),
     ], "da_xong_mong_doi": True, "mo_ta": "Cả 4 ý đều bắt buộc suy luận, đều đúng ngay"},
    {"id": 25, "loai_cau": "TNDS", "do_kho": "tb", "bat_buoc_suy_luan": [True, False, False, False],
     "hanh_vi": [("suy_luan_sai",), ("suy_luan_dung",), ("chot_dung",), ("chot_dung",),
                 ("chot_dung",), ("chot_dung",)],
     "da_xong_mong_doi": True, "mo_ta": "Ý a suy luận sai rồi đúng, vẫn qua được"},
    {"id": 26, "loai_cau": "TNDS", "do_kho": "de", "bat_buoc_suy_luan": [True, False, False, False],
     "hanh_vi": [("suy_luan_chua_du_co_so",), ("suy_luan_dung",), ("chot_dung",),
                 ("chot_dung",), ("chot_dung",), ("chot_dung",)],
     "da_xong_mong_doi": True, "mo_ta": "Ý a suy luận thiếu điều kiện xác định rồi đúng (phần B)"},
    {"id": 27, "loai_cau": "TNDS", "do_kho": "tb", "bat_buoc_suy_luan": [False, True, False, False],
     "hanh_vi": [("chot_dung",), ("suy_luan_khong_doc_duoc",), ("suy_luan_dung",),
                 ("chot_dung",), ("chot_dung",), ("chot_dung",)],
     "da_xong_mong_doi": True, "mo_ta": "Ý b suy luận nhập không đọc được rồi đúng"},
    {"id": 28, "loai_cau": "TNDS", "do_kho": "de", "bat_buoc_suy_luan": [False] * 4,
     "hanh_vi": [("chot_dung",), ("chot_dung",), ("chot_dung",), ("chot_sai",), ("chot_sai",)],
     "da_xong_mong_doi": False, "mo_ta": "Ý d chốt sai mãi — chưa hoàn thành"},
    {"id": 29, "loai_cau": "TNDS", "do_kho": "tb", "bat_buoc_suy_luan": [False, False, True, False],
     "hanh_vi": [("chot_dung",), ("chot_dung",), ("goi_y",), ("suy_luan_dung",), ("chot_dung",),
                 ("chot_dung",)],
     "da_xong_mong_doi": True, "mo_ta": "Ý c xin gợi ý trước khi suy luận đúng rồi chốt"},
    {"id": 30, "loai_cau": "TNDS", "do_kho": "kho", "bat_buoc_suy_luan": [False] * 4,
     "hanh_vi": [
         ("goi_y",), ("goi_y",), ("goi_y",), ("chot_dung",),
         ("goi_y",), ("goi_y",), ("goi_y",), ("chot_dung",),
         ("chot_dung",), ("chot_dung",),
     ], "da_xong_mong_doi": True, "mo_ta": "Xin gợi ý nhiều lần ở 2 ý đầu (độ khó cao, 4 mức)"},
]
