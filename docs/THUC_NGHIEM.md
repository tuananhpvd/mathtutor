# KẾ HOẠCH THỰC NGHIỆM SƯ PHẠM — MathTutor (C5)

> Tài liệu hành động cho GV chủ trì thực nghiệm. Mục tiêu: thu **minh chứng thực tế**
> (số liệu + khảo sát + bài kiểm tra trước/sau) cho báo cáo dự thi. Hệ thống đã có sẵn
> bộ đo tự động (mục 4) — GV không phải ghi chép tay số liệu sử dụng.

## 1. Thiết kế thực nghiệm

- **Mô hình khuyến nghị: trước–sau trên 1–2 lớp** GV đang trực tiếp dạy (khả thi nhất
  với 1 GV). Nếu có đồng nghiệp dạy lớp trình độ tương đương đồng ý tham gia → thêm
  **lớp đối chứng** (học truyền thống, cùng đề kiểm tra) — điểm cộng lớn nhưng không bắt buộc.
- **Thời lượng: 3–4 tuần** luyện tập thực tế (không tính tuần chuẩn bị). Không nén được —
  cần bắt đầu sớm nhất có thể so với hạn nộp báo cáo.
- **Phạm vi kiến thức:** chọn 1–2 chuyên đề đang dạy trong giai đoạn đó (để bài kiểm tra
  trước/sau đo đúng phần HS luyện trên hệ thống).
- **Tính trung thực:** báo cáo ghi rõ đây là *thống kê mô tả trên mẫu nhỏ*, không phải
  kiểm định thống kê; nêu cả hạn chế (không tách được ảnh hưởng của việc dạy trên lớp).

## 2. Lịch trình theo tuần

| Tuần | Việc | Ghi chú |
|---|---|---|
| **0 — chuẩn bị** | Xin phép BGH (mẫu mục 6) + thông báo phụ huynh; hoàn thành checklist kỹ thuật (mục 3); **kiểm tra đầu vào** 45' trên giấy hoặc chế độ đề (C1 nếu kịp); 1 buổi phòng máy cho HS làm quen (đăng nhập, làm thử 1 bài, đổi mật khẩu) | Đề đầu vào giữ lại làm cặp so sánh với đầu ra |
| **1–3 — luyện tập** | GV giao nhiệm vụ theo tuần (tính năng Giao nhiệm vụ có sẵn): 3–5 bài/tuần/HS theo chuyên đề đang dạy; GV theo dõi panel "Hiệu quả phương pháp" + "Bản đồ năng lực lớp", xử lý cờ, trả lời HS nhờ trợ giúp | Số liệu tự tích lũy — không cần ghi tay |
| **4 — tổng kết** | **Kiểm tra đầu ra** (đề tương đương đầu vào — cùng ma trận, khác số liệu); phát **phiếu khảo sát** (mục 5); xuất minh chứng (mục 7) | Chấm 2 đề cùng thang điểm |

## 3. Checklist kỹ thuật TRƯỚC buổi đầu tiên

- [ ] **Bật chế độ chạy thật** (Admin → Cấu hình, KHÔNG sửa code): `llm_provider` stub → gemini;
      key có hạn mức đủ (khuyến nghị bật billing Google); bật lại `tu_dong_phan_tich`.
- [ ] **Đặt phanh chi phí (B4)**: giới hạn lượt/HS/ngày ≈ 30, tổng hệ thống/ngày ≈ 500
      (lớp 40 HS × ~12 lượt/buổi vẫn dư); theo dõi ô "Hôm nay đã dùng" tuần đầu để chỉnh.
- [ ] **Làm thử 1 bài end-to-end** bằng tài khoản HS thật (lời thoại tự nhiên? gợi ý leo thang? chốt chặn ổn?).
- [ ] **Ngân hàng câu hỏi**: ≥ 15–20 câu ĐÃ DUYỆT cho mỗi chuyên đề thực nghiệm, đủ 3 loại câu
      và 3 mức độ (dùng AI sinh + duyệt để làm dày nhanh).
- [ ] **Tài khoản HS**: import từ Excel (tính năng có sẵn), mật khẩu ban đầu phát riêng từng em,
      yêu cầu đổi ngay buổi làm quen.
- [ ] **Đường truy cập từ nhà**: cần hệ thống truy cập được ngoài trường (deploy/B1). Phương án
      tối thiểu nếu chưa deploy: chỉ luyện tại phòng máy trường (giảm tần suất — ghi rõ trong báo cáo).
- [ ] **Sao lưu `dev.db` mỗi tuần** (copy file, đặt tên theo ngày) — dữ liệu thực nghiệm là vàng.

## 4. Chỉ số thu thập (nguồn: TỰ ĐỘNG trừ 2 mục ✍)

| Chỉ số | Nguồn | Dùng cho |
|---|---|---|
| Phân bố mức gợi ý khi hoàn thành (mức 0/1/2/3+), % tự làm | Panel "Hiệu quả phương pháp" + nút Xuất CSV | Chứng minh HS TỰ tìm đáp án, không bị mớm |
| Xu hướng phụ thuộc gợi ý (5 bài đầu → 5 gần nhất, từng HS) | Bảng trong panel + CSV | Chứng minh tiến bộ theo thời gian |
| Bản đồ năng lực lớp trước/sau (chụp tuần 0 và tuần 4) | Card "Bản đồ năng lực lớp" | Hình ảnh trực quan cho slide |
| Số bài/tuần, điểm TB, thời gian làm bài | Panel + trang Tiến bộ | Mức độ sử dụng thật |
| ✍ Điểm kiểm tra đầu vào / đầu ra | GV chấm | So sánh trước–sau (chỉ số chính) |
| ✍ Phiếu khảo sát cảm nhận HS | Mục 5 | Góc nhìn người học + trích dẫn |

## 5. Phiếu khảo sát học sinh (phát cuối tuần 4, ẩn danh)

> Trả lời theo mức: 1 = Hoàn toàn không đồng ý · 2 · 3 · 4 · 5 = Hoàn toàn đồng ý

1. Các câu hỏi gợi mở giúp em TỰ tìm ra đáp án thay vì được cho sẵn lời giải.
2. Sau khi dùng MathTutor, em tự tin hơn khi gặp dạng bài tương tự.
3. Gợi ý của hệ thống vừa sức — không quá lộ, không quá mơ hồ.
4. Em thích học kiểu được dẫn dắt từng bước hơn là xem đáp án ngay.
5. Phần "Xem lại bài" (lời giải chuẩn + hành trình của em) giúp em hiểu mình sai ở đâu.
6. Em có thể tự học ở nhà bằng hệ thống mà không cần người kèm.
7. Giao diện dễ dùng, công thức toán hiển thị rõ ràng.
8. Bản đồ năng lực/tiến độ giúp em biết mình cần luyện thêm phần nào.
9. So với việc hỏi các AI khác (ChatGPT...), cách học này giúp em HIỂU bài hơn.
10. Em muốn tiếp tục dùng MathTutor sau đợt thực nghiệm.

Câu mở: (a) Điều em thích nhất ở MathTutor là gì? (b) Điều gì khiến em khó chịu/muốn thay đổi?

## 6. Mẫu xin phép & thông báo (rút gọn — điều chỉnh theo trường)

- **Tờ trình BGH:** mục đích (thử nghiệm công cụ hỗ trợ tự học Toán 12 do GV xây dựng,
  phục vụ [tên cuộc thi]); phạm vi (lớp ..., 4 tuần, ngoài giờ chính khóa); cam kết
  (không thu phí, không ảnh hưởng chương trình, dữ liệu HS ẩn danh trong mọi báo cáo).
- **Thông báo phụ huynh (gửi nhóm lớp):** con sẽ luyện Toán trên hệ thống web do GV phát
  triển, AI chỉ ĐẶT CÂU HỎI GỢI MỞ chứ không giải hộ; tài khoản riêng, không quảng cáo,
  không thu thập thông tin ngoài kết quả học tập; PH có thể yêu cầu xem dữ liệu của con.

## 7. Đạo đức dữ liệu & xuất minh chứng cho báo cáo

- Báo cáo/slide dùng **mã HS (HS01, HS02...)** thay tên thật; ảnh chụp màn hình che cột họ tên.
- Bộ minh chứng nên gồm: (1) CSV hiệu quả phương pháp tuần 4; (2) ảnh Bản đồ năng lực lớp
  tuần 0 vs tuần 4 đặt cạnh nhau; (3) bảng điểm trước/sau (trung bình, số HS tăng điểm);
  (4) tổng hợp khảo sát (điểm TB từng câu + 3–5 trích dẫn câu mở); (5) ảnh 1 đoạn hội
  thoại gợi mở tiêu biểu (che tên).
- Lưu ý khi diễn giải: tiến bộ = tổ hợp của cả dạy trên lớp + hệ thống; số liệu "giảm phụ
  thuộc gợi ý" và "% tự làm tăng" là minh chứng ĐẶC THÙ của phương pháp gợi mở mà lớp học
  truyền thống không đo được — đây là điểm nhấn khi thuyết trình.
