# MC-2 — Kết quả kiểm chứng chốt chặn rò rỉ đáp án

**19/20 đúng theo kỳ vọng** (95.0%).

- Chặn đúng 9/10 ca RỦI RO cố ý (đo khả năng phát hiện lộ đáp án).
- Không chặn nhầm 10/10 ca AN TOÀN cố ý (đo tỉ lệ chặn nhầm — mục thuyết minh VII.2 tự nhận trước đây chưa đo được).

Sinh bằng `tests/minh_chung/data_mc2_chong_lo_dap_an.py`. Chi tiết từng ca: `mc2_chong_lo_dap_an_chi_tiet.csv`.

## 1 ca lệch kỳ vọng

| id | nhóm | nội dung | kỳ vọng chặn | thực tế | lý do lọc | ghi chú |
|---|---|---|---|---|---|---|
| 2 | rui_ro_khong_lien_ke_chat | Kết quả cuối cùng là x=3, chính xác rồi đó em | True | sach | - | PHÁT HIỆN THẬT: bộ lọc hiện KHÔNG bắt được ca này (xem báo cáo) — từ khóa và giá trị không đứng liền kề chặt do có chữ chen giữa ('cuối cùng', 'x=') |
