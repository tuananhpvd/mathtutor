# Bộ minh chứng kiểm thử nội bộ — MathTutor

Thư mục này chứa kết quả **tái lập được** của Bảng 13 (thuyết minh, mục VII.2–VII.3). Mỗi
con số công bố trong thuyết minh là con số một trong các test dưới đây **in ra thật**, không
phải số định trước rồi soạn dữ liệu cho khớp.

## Chạy lại toàn bộ

```powershell
cd backend
.venv\Scripts\pytest.exe tests\minh_chung -v
```

Chạy xong, mọi file `.md`/`.csv` trong thư mục này được **ghi đè lại** bằng kết quả của lần
chạy đó. Nếu ra số khác với thuyết minh, đó là tín hiệu cần cập nhật thuyết minh theo số thật
— không phải sửa lại dữ liệu nguồn (`tests/minh_chung/data_*.py`) để ép ra đúng con số cũ.

## Nguồn dữ liệu & mã kiểm

| Dòng Bảng 13 | Thư mục con | Dữ liệu nguồn | Mã sản phẩm được kiểm |
|---|---|---|---|
| HS – luyện gợi mở | `mc4_*` | `data_mc4_kich_ban.py` (30 kịch bản) | `app/core/orchestrator/rules.py` |
| HS – chống lộ đáp án | `mc2_*` | `data_mc2_chong_lo_dap_an.py` (20 ca) | `app/core/guard/leak.py::kiem_tra_ro_ri` |
| GV – tạo/duyệt câu hỏi | — | Định tính, không có test tự động (xem thuyết minh mục VII.3) | — |
| Chấm toán bằng SymPy | `mc1_*` | `data_mc1_bieu_thuc.py` (100 ca) | `app/core/matching/cas.py::tuong_duong` |
| Quản trị – quyền/hạn mức | `mc5_*` | 4 file test đã có sẵn trong bộ 663 test chính | `test_monitor_idor.py` + `test_sessions_idor.py` + `test_llm_quota.py` + `test_config_safety.py` |
| An toàn phản hồi AI | `mc3_*` | `data_mc3_phan_hoi_ai.py` (250 câu, sinh templated) | `app/core/guard/leak.py::kiem_tra_ro_ri` |

## Vì sao quy mô nhỏ hơn con số ban đầu dự kiến

Bản dự thảo đầu tiên của thuyết minh dùng quy mô 200/40/60/500 ca. Vì giới hạn thời gian,
quy mô mỗi bộ đã **giảm khoảng một nửa** (trừ MC-5, vốn tái dùng nguyên trạng 30 test bảo mật
đã có). Đây là đánh đổi có chủ đích, không phải rút gọn để che giấu kết quả xấu — mọi bộ đều
giữ đủ đa dạng nhóm hiện tượng cần đo (xem "nhóm"/"nhom" trong từng CSV chi tiết).

## Cách đọc số liệu — tránh hiểu lầm

- **MC-1 (SymPy) và MC-4 (orchestrator)** kiểm hành vi có tính **quyết định** (deterministic)
  — không cần "quy mô lớn" để đáng tin, vì không có yếu tố ngẫu nhiên/mơ hồ trong phép so
  khớp đại số hay máy trạng thái. 100% ở đây có ý nghĩa mạnh hơn 100% trong MC-2/MC-3.
- **MC-2 và MC-3 (chốt chặn rò rỉ)** dựa trên **từ khóa/mẫu câu** (regex) — có giới hạn thật
  (xem các ca "lệch kỳ vọng" trong từng báo cáo). Tỉ lệ "bị chặn/tổng" của MC-3 **phụ thuộc
  hoàn toàn vào tỉ lệ câu rủi ro/an toàn được dựng trong corpus** — đọc kèm tỉ lệ dựng
  (200 an toàn : 50 rủi ro), đừng đọc một mình con số phần trăm.
- **Cả MC-1 và MC-3 đều phát hiện các ca lệch kỳ vọng ban đầu do người soạn dữ liệu (không
  phải do lỗi sản phẩm)** — xem mục "lệch kỳ vọng" trong mỗi báo cáo `_tom_tat.md` để biết
  chi tiết cách phát hiện và xử lý minh bạch (không xóa âm thầm).
- **Hai phát hiện thật đáng chú ý nhất** (không phải lỗi tạo dữ liệu, là giới hạn thật của
  quy tắc): (1) `leak.py` yêu cầu từ khóa và giá trị đáp án đứng **liền kề chặt**, nên diễn
  đạt gián tiếp như "kết quả cuối cùng là x=3" có thể lọt; (2) cụm `"đáp số (là|:)"` đòi hỏi
  **khoảng trắng trước dấu hai chấm**, nên "Đáp số:" (văn phong tự nhiên, không cách) không
  khớp trong khi "Đáp số :" (có cách) khớp. Cả hai được ghi nhận cụ thể, chưa sửa code trong
  đợt này (ngoài phạm vi đã thống nhất — phạm vi đợt này chỉ gồm việc "chưa đủ cơ sở/điều
  kiện xác định" (Bảng 12) và bộ minh chứng), là việc đáng làm tiếp theo cho `leak.py`.
