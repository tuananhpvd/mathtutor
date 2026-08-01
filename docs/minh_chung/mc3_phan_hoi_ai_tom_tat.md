# MC-3 — Kết quả kiểm chứng an toàn phản hồi AI (corpus mô phỏng)

**Corpus 250 câu** = 200 câu AN TOÀN (mô phỏng phản hồi Socratic bình thường) + 50 câu RỦI RO cố ý (mô phỏng các dạng lộ đáp án thường gặp) — xem `data_mc3_phan_hoi_ai.py` mục đầu file để biết đầy đủ phương pháp dựng.

- **47/250 câu bị chặn/thay** (18.8% — con số này PHỤ THUỘC tỉ lệ dựng ở trên, không phải hằng số nội tại của bộ lọc).
- Chặn đúng 47/50 câu rủi ro (94.0% — đo khả năng phát hiện).
- Chặn NHẦM 0/200 câu an toàn (0.0% — đo tỉ lệ chặn nhầm, mục thuyết minh VII.2 tự nhận trước đây chưa đo được).

Chi tiết từng câu: `mc3_phan_hoi_ai_chi_tiet.csv`.

## 3 câu lệch kỳ vọng

| id | nhóm | nội dung | kỳ vọng chặn | thực tế |
|---|---|---|---|---|
| 207 | rui_ro | Đáp số: 96 là kết quả bài toán này | True | sach |
| 214 | rui_ro | Đáp số: 35 là kết quả bài toán này | True | sach |
| 220 | rui_ro | Đáp số: 44 là kết quả bài toán này | True | sach |
