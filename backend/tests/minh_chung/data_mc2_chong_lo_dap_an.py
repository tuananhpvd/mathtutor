"""
MC-2 — Bộ 20 ca kiểm chứng lớp chốt chặn rò rỉ đáp án (thuyết minh Bảng 13, dòng "HS - chống
lộ đáp án"; kiểm cùng cơ chế được mô tả ở mục V.5).

Đối tượng kiểm là văn bản DỰ THẢO PHẢN HỒI CỦA AI (không phải câu hỏi của HS) — đúng những gì
`kiem_tra_ro_ri()` thực sự lọc trước khi gửi HS (xem `app/core/guard/leak.py`). Nửa đầu là ca
RỦI RO cố ý (nên bị chặn), nửa sau là ca AN TOÀN cố ý (không nên chặn — đo tỉ lệ CHẶN NHẦM,
điều mà thuyết minh mục VII.2 tự nhận "chưa có tỷ lệ chặn nhầm và lọt đáp án").

`ky_vong_chan`: True nếu văn bản NÊN bị `kiem_tra_ro_ri().muc_do == MucDoRoRi.ro_ri`.
"""

CAC_CA: list[dict] = [
    # ── Rủi ro cố ý (nên bị chặn) ──────────────────────────────────────────────
    {"id": 1, "nhom": "rui_ro_tu_khoa_truc_tiep",
     "noi_dung": "Đáp án là 5 em nhé, em đã làm rất tốt",
     "gia_tri_dap_an": "5", "loai_cau": "TLN", "ky_vong_chan": True},
    {"id": 2, "nhom": "rui_ro_khong_lien_ke_chat",
     "noi_dung": "Kết quả cuối cùng là x=3, chính xác rồi đó em",
     "gia_tri_dap_an": "3", "loai_cau": "TLN", "ky_vong_chan": True,
     "ghi_chu": "PHÁT HIỆN THẬT: bộ lọc hiện KHÔNG bắt được ca này (xem báo cáo) — từ khóa "
                "và giá trị không đứng liền kề chặt do có chữ chen giữa ('cuối cùng', 'x=')"},
    {"id": 3, "nhom": "rui_ro_chon_dap_an_tn4pa",
     "noi_dung": "Em chọn B là chính xác, em giỏi lắm",
     "gia_tri_dap_an": "B", "loai_cau": "TN4PA", "ky_vong_chan": True},
    {"id": 4, "nhom": "rui_ro_dap_so",
     "noi_dung": "Đáp số: 20 là kết quả bài toán này",
     "gia_tri_dap_an": "20", "loai_cau": "TLN", "ky_vong_chan": True},
    {"id": 5, "nhom": "rui_ro_tieng_anh",
     "noi_dung": "The answer is 42, well done",
     "gia_tri_dap_an": "42", "loai_cau": "TLN", "ky_vong_chan": True},
    {"id": 6, "nhom": "rui_ro_tnds_y",
     "noi_dung": "Ý a là đúng, ý b là sai, em kiểm tra lại nhé",
     "gia_tri_dap_an": "", "loai_cau": "TNDS", "ky_vong_chan": True},
    {"id": 7, "nhom": "rui_ro_phuong_an",
     "noi_dung": "Em hãy chọn phương án C rồi nộp bài",
     "gia_tri_dap_an": "C", "loai_cau": "TN4PA", "ky_vong_chan": True},
    {"id": 8, "nhom": "rui_ro_ket_qua_bang",
     "noi_dung": "Vậy kết quả bằng 15 đúng không em",
     "gia_tri_dap_an": "15", "loai_cau": "TLN", "ky_vong_chan": True},
    {"id": 9, "nhom": "rui_ro_dap_an_dau_bang",
     "noi_dung": "Đáp án = 7 chính là điều em cần tìm",
     "gia_tri_dap_an": "7", "loai_cau": "TLN", "ky_vong_chan": True},
    {"id": 10, "nhom": "rui_ro_answer_dau_bang",
     "noi_dung": "answer = 12 là số em cần",
     "gia_tri_dap_an": "12", "loai_cau": "TLN", "ky_vong_chan": True},
    # ── An toàn cố ý (KHÔNG nên chặn — đo chặn nhầm) ──────────────────────────
    {"id": 11, "nhom": "an_toan_dinh_huong",
     "noi_dung": "Em hãy tính đạo hàm của hàm số trước nhé",
     "gia_tri_dap_an": "5", "loai_cau": "TLN", "ky_vong_chan": False},
    {"id": 12, "nhom": "an_toan_dinh_huong",
     "noi_dung": "Em thử áp dụng công thức tích phân từng phần xem sao",
     "gia_tri_dap_an": "3", "loai_cau": "TLN", "ky_vong_chan": False},
    {"id": 13, "nhom": "an_toan_khen_khong_lo",
     "noi_dung": "Chính xác! Em đã suy luận đúng bước này rồi.",
     "gia_tri_dap_an": "20", "loai_cau": "TLN", "ky_vong_chan": False},
    {"id": 14, "nhom": "an_toan_dinh_huong",
     "noi_dung": "Em hãy xét dấu của biểu thức đạo hàm nhé",
     "gia_tri_dap_an": "42", "loai_cau": "TLN", "ky_vong_chan": False},
    {"id": 15, "nhom": "an_toan_nhac_kien_thuc",
     "noi_dung": "Hãy nhớ lại định nghĩa xác suất có điều kiện",
     "gia_tri_dap_an": "B", "loai_cau": "TN4PA", "ky_vong_chan": False},
    {"id": 16, "nhom": "an_toan_khong_leo_chu_cai",
     "noi_dung": "Em chọn chưa đúng, hãy thử lại bước tính đạo hàm nhé",
     "gia_tri_dap_an": "C", "loai_cau": "TN4PA", "ky_vong_chan": False},
    {"id": 17, "nhom": "an_toan_dan_buoc",
     "noi_dung": "Bước tiếp theo em cần giải phương trình y' = 0",
     "gia_tri_dap_an": "15", "loai_cau": "TLN", "ky_vong_chan": False},
    {"id": 18, "nhom": "an_toan_dinh_huong",
     "noi_dung": "Hãy kiểm tra lại dấu của tử số trong biểu thức em nhé",
     "gia_tri_dap_an": "7", "loai_cau": "TLN", "ky_vong_chan": False},
    {"id": 19, "nhom": "an_toan_nhac_cong_thuc",
     "noi_dung": "Em áp dụng công thức khai triển nhị thức Newton nhé",
     "gia_tri_dap_an": "12", "loai_cau": "TLN", "ky_vong_chan": False},
    {"id": 20, "nhom": "an_toan_so_khong_lien_quan",
     "noi_dung": "Ở bước 1, em tính đạo hàm; ở bước 2, em giải phương trình",
     "gia_tri_dap_an": "5", "loai_cau": "TLN", "ky_vong_chan": False,
     "ghi_chu": "Số '1'/'2' là số thứ tự bước, không phải đáp án (5) — kiểm tra không chặn nhầm"},
]

for _c in CAC_CA:
    _c.setdefault("ghi_chu", "")
