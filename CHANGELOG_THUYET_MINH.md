# Changelog — các chỗ đã sửa trong Thuyet_minh_chi_tiet_Mathtutor_gia_su_toan_12.md

File thuyết minh đã được đánh dấu trực tiếp bằng comment `<!-- ĐÃ SỬA #N ... -->` /
`<!-- HẾT SỬA #N -->` quanh mỗi đoạn bị sửa (comment HTML, không hiện ra khi render/in —
mở file bằng trình soạn thảo text hoặc Ctrl+F tìm "ĐÃ SỬA" để nhảy tới từng chỗ). File này
liệt kê **TRƯỚC / SAU** đầy đủ để đối chiếu khi cập nhật báo cáo chính thức (Word/PDF).

**Vì sao phải sửa (tóm tắt chung):** rà lại thấy tài liệu có 4 chỗ mô tả **vượt quá những gì
code thực sự làm** (mục IV.1.5, IV.4.3, V.4, V.5) và 6 con số ở Bảng 13 (+ 2 đoạn phân tích
đi kèm) **không có bộ test nào tạo ra**. Đã xử lý theo 2 cách: (1) nơi mô tả sai — sửa lại
câu chữ cho khớp code, HOẶC bổ sung code cho khớp câu chữ (chỉ 1 chỗ — mục V.4, phần điều
kiện xác định); (2) nơi thiếu minh chứng — dựng bộ test thật, lấy số liệu thật thay cho số cũ.

---

## SỬA #1 — Mục IV.1.5 "Chấm câu trả lời và bước làm bằng SymPy" (~dòng 266–268)

**Lý do:** câu "gắn cờ" áp dụng chung cho MỌI trạng thái chưa chắc chắn, nhưng thực tế chỉ
trạng thái "không phân tích được" mới tự động gắn cờ báo giáo viên (và chỉ khi lặp ≥3 lần
trong 1 phiên). Con số 197/200 (98,5%) không có bộ test nào tạo ra — đã thay bằng bộ 100 ca
thật (`backend/tests/minh_chung/`), kết quả 100/100.

**TRƯỚC:**
> AI không có quyền quyết định kết quả chấm. Vai trò của AI chỉ xuất hiện sau khi hệ thống đã
> có trạng thái: đúng, sai, lỗi cú pháp hoặc chưa đủ cơ sở. Nếu đúng, AI có thể diễn đạt lời
> khích lệ và chuyển bước; nếu sai, AI dựa trên gợi ý đã duyệt để nhắc học sinh kiểm tra; nếu
> chưa chắc chắn, hệ thống đưa phản hồi trung tính và gắn cờ.
>
> Trong kiểm thử nội bộ bằng dữ liệu mô phỏng, 197/200 biểu thức được nhận diện đúng về tính
> tương đương hoặc không tương đương, đạt 98,5% trong phạm vi bộ test; 3 trường hợp được
> chuyển kiểm tra thủ công. Kết quả này không chứng minh công cụ xử lý mọi dạng Toán 12,
> nhưng cho thấy cơ chế kiểm chứng hoạt động thực tế.

**SAU:**
> AI không có quyền quyết định kết quả chấm. Vai trò của AI chỉ xuất hiện sau khi hệ thống đã
> có trạng thái: đúng, sai, không phân tích được hoặc chưa đủ cơ sở. Nếu đúng, AI có thể diễn
> đạt lời khích lệ và chuyển bước; nếu sai, AI dựa trên gợi ý đã duyệt để nhắc học sinh kiểm
> tra; nếu chưa chắc chắn, hệ thống đưa phản hồi trung tính, mời học sinh bổ sung thông tin —
> và tự động gắn cờ báo giáo viên nếu tình trạng "không phân tích được" lặp lại nhiều lần
> trong cùng một phiên.
>
> Trong kiểm thử nội bộ bằng dữ liệu mô phỏng, 100/100 biểu thức được nhận diện đúng theo kỳ
> vọng đã xác định trước, trong đó 8 biểu thức được nhận diện đúng là "không phân tích được"
> (sai cú pháp) và 8 biểu thức chứa căn được nhận diện đúng là "chưa đủ cơ sở" (thiếu điều
> kiện xác định) — cả hai loại đều KHÔNG bị chấm sai mà mời học sinh bổ sung hoặc nhập lại.
> Kết quả này không chứng minh công cụ xử lý mọi dạng Toán 12, nhưng cho thấy cơ chế kiểm
> chứng hoạt động thực tế, kể cả biết dừng lại khi chưa đủ căn cứ.

---

## SỬA #2 — Mục IV.1.8 "Bộ lọc chống lộ đáp án..." (~dòng 300)

**Lý do:** claim "Khi phù hợp, SymPy hỗ trợ phát hiện một biểu thức khác hình thức nhưng
tương đương với kết quả cuối" **không đúng** — kiểm tra `backend/app/core/guard/leak.py` xác
nhận lớp lọc này chỉ dùng regex/từ khóa, KHÔNG import SymPy, KHÔNG có bước phát hiện tương
đương đại số. Con số 40/40 cũng không có test — thay bằng số liệu thật từ 2 bộ mới (20 ca +
250 ca mô phỏng).

**TRƯỚC:**
> Lớp thứ nhất nằm trong prompt hệ thống: AI được quy định vai trò, phạm vi và những nội dung
> không được phép. Lớp thứ hai kiểm tra phản hồi bằng từ khóa, mẫu ngôn ngữ, giá trị số và
> biểu thức có khả năng trùng đáp án. Khi phù hợp, SymPy hỗ trợ phát hiện một biểu thức khác
> hình thức nhưng tương đương với kết quả cuối. Lớp thứ ba chặn phản hồi rủi ro và thay bằng
> câu gợi mở an toàn trước khi hiển thị cho học sinh.
>
> Trong quá trình kiểm thử nội bộ bằng dữ liệu mô phỏng, hệ thống đã ghi nhận một số phản hồi
> dự thảo của AI có nguy cơ cung cấp kết quả quá trực tiếp hoặc hướng dẫn vượt quá mức gợi ý
> cho phép. Các phản hồi này không được hiển thị nguyên văn cho học sinh mà được bộ lọc chặn
> lại hoặc thay thế bằng nội dung gợi mở an toàn hơn, nhằm bảo đảm AI chỉ hỗ trợ định hướng,
> không làm thay bài cho học sinh. Có 40/40 ca học sinh cố tình yêu cầu đáp án được hệ thống
> lọc và chuyển sang gợi mở cho học sinh tiếp tục làm bài.

**SAU:**
> Lớp thứ nhất nằm trong prompt hệ thống: AI được quy định vai trò, phạm vi và những nội dung
> không được phép. Lớp thứ hai kiểm tra phản hồi bằng từ khóa và mẫu ngôn ngữ thường gặp khi
> lộ đáp án (ví dụ "đáp án là", "kết quả bằng", "chọn A/B/C/D"), đối chiếu trực tiếp với giá
> trị đáp án chuẩn khi giá trị đó xuất hiện gần các từ khóa này. Lớp thứ ba chặn phản hồi rủi
> ro và thay bằng câu gợi mở an toàn trước khi hiển thị cho học sinh.
>
> Trong quá trình kiểm thử nội bộ bằng dữ liệu mô phỏng, hệ thống đã ghi nhận một số phản hồi
> dự thảo của AI có nguy cơ cung cấp kết quả quá trực tiếp hoặc hướng dẫn vượt quá mức gợi ý
> cho phép. Các phản hồi này không được hiển thị nguyên văn cho học sinh mà được bộ lọc chặn
> lại hoặc thay thế bằng nội dung gợi mở an toàn hơn, nhằm bảo đảm AI chỉ hỗ trợ định hướng,
> không làm thay bài cho học sinh. Trên bộ kiểm chứng 20 ca phản hồi mô phỏng (10 ca có dấu
> hiệu lộ đáp án cố ý + 10 ca an toàn đối chứng), bộ lọc chặn đúng 9/10 ca rủi ro và không
> chặn nhầm ca nào trong 10 ca an toàn; mở rộng trên corpus 250 phản hồi (200 câu an toàn + 50
> câu rủi ro cố ý), kết quả tương tự với 47/50 ca rủi ro (94%) bị chặn/thay và không chặn nhầm
> câu an toàn nào. Các ca chưa bắt được đều thuộc dạng diễn đạt lộ đáp án mà từ khóa và giá
> trị không đứng liền kề đủ chặt để khớp quy tắc hiện có — giới hạn thật của cách tiếp cận dựa
> trên từ khóa/mẫu câu, đã được ghi nhận cụ thể để cải thiện.

---

## SỬA #3 — Mục IV.4.3 "Cơ chế kiểm chứng toán học và trạng thái 'chưa đủ cơ sở'" (~dòng 536–540)

**Lý do:** "thử tại một số giá trị phù hợp" — KHÔNG có trong code (không có bước kiểm tra số
học tại điểm mẫu). "kết quả kiểm tra chưa ổn định", "có nhiều cách hiểu", "nằm ngoài phạm vi
quy tắc chấm hiện có" — các cụm mơ hồ không ứng với điều kiện cụ thể nào trong code. Ví dụ
minh họa (đoạn cuối) được viết lại để khớp CHÍNH XÁC với cơ chế mới đã cài đặt (xem SỬA #4).

**TRƯỚC:**
> MathTutor không chỉ chấm câu trả lời theo hai trạng thái "đúng" hoặc "sai", mà phân biệt rõ
> ba trường hợp: có căn cứ để xác nhận đúng, có căn cứ để xác định sai và chưa đủ cơ sở để
> kết luận. Trạng thái "chưa đủ cơ sở" được dùng khi biểu thức học sinh nhập không phân tích
> được, thiếu điều kiện xác định, có nhiều cách hiểu hoặc nằm ngoài phạm vi quy tắc chấm hiện
> có. Trong những trường hợp này, hệ thống không vội trừ điểm và cũng không đưa ra kết luận
> chắc chắn, mà yêu cầu học sinh bổ sung thông tin hoặc chuyển giáo viên xem xét khi cần.
>
> Quy trình kiểm tra có thể gồm nhiều bước như chuẩn hóa ký hiệu, kiểm tra cú pháp, xác định
> giả thiết, rút gọn hiệu giữa hai biểu thức, thử tại một số giá trị phù hợp và đối chiếu điều
> kiện của bài toán. Tuy nhiên, với môn Toán, không phải lúc nào một phép kiểm tra đơn lẻ cũng
> đủ để kết luận. Có những biểu thức chỉ tương đương trên một miền xác định nhất định, nhưng
> không đúng trên toàn bộ tập số. Vì vậy, giáo viên vẫn phải cung cấp đáp án, điều kiện và quy
> tắc chấm phù hợp cho từng dạng bài; SymPy chỉ là công cụ hỗ trợ kiểm chứng, không thay thế
> vai trò xác định bài toán của giáo viên.
>
> Chẳng hạn, nếu học sinh nhập một biểu thức có căn nhưng chưa nêu điều kiện xác định, hệ
> thống không tự động công nhận theo giả thiết mặc định của SymPy. Thay vào đó, học sinh có
> thể được yêu cầu bổ sung điều kiện, hoặc trường hợp đó được chuyển để giáo viên kiểm tra.
> Giá trị của cơ chế này nằm ở chỗ MathTutor biết dừng lại khi chưa đủ căn cứ, tránh đưa ra
> kết luận sai nhưng có vẻ chắc chắn.

**SAU:**
> MathTutor không chỉ chấm câu trả lời theo hai trạng thái "đúng" hoặc "sai", mà phân biệt rõ
> ba trường hợp: có căn cứ để xác nhận đúng, có căn cứ để xác định sai và chưa đủ cơ sở để kết
> luận. Trạng thái "chưa đủ cơ sở" được dùng khi biểu thức học sinh nhập không phân tích được
> (sai cú pháp), hoặc khi biểu thức có căn bậc hai mà điều kiện xác định chưa được nêu. Trong
> những trường hợp này, hệ thống không vội trừ điểm và cũng không đưa ra kết luận chắc chắn,
> mà yêu cầu học sinh bổ sung thông tin; riêng trường hợp không phân tích được lặp lại nhiều
> lần trong một phiên sẽ tự động chuyển giáo viên xem xét.
>
> Quy trình kiểm tra gồm các bước như chuẩn hóa ký hiệu, kiểm tra cú pháp, chuẩn hóa dạng viết
> (LaTeX, cú pháp SymPy, ký hiệu tổ hợp/chỉnh hợp quen dùng trong sách giáo khoa) và rút gọn
> hiệu giữa hai biểu thức bằng SymPy để xác định tương đương đại số. Tuy nhiên, với môn Toán,
> không phải lúc nào một phép rút gọn đơn lẻ cũng đủ để kết luận. Có những biểu thức chỉ tương
> đương trên một miền xác định nhất định (chẳng hạn biểu thức chứa căn), nhưng không đúng trên
> toàn bộ tập số. Vì vậy, giáo viên vẫn phải cung cấp đáp án, điều kiện và quy tắc chấm phù
> hợp cho từng dạng bài; SymPy chỉ là công cụ hỗ trợ kiểm chứng, không thay thế vai trò xác
> định bài toán của giáo viên.
>
> Chẳng hạn, nếu học sinh nhập một biểu thức có căn bậc hai mà dấu của phần trong căn không
> xác định được — dù giả định biến là số thực — hệ thống không tự động công nhận đúng chỉ vì
> hai biểu thức tương đương về mặt đại số theo giả thiết mặc định của SymPy. Thay vào đó, học
> sinh được yêu cầu bổ sung điều kiện xác định rồi thử lại. Giá trị của cơ chế này nằm ở chỗ
> MathTutor biết dừng lại khi chưa đủ căn cứ, tránh công nhận một kết quả đúng về mặt hình
> thức nhưng có thể thiếu chặt chẽ.

---

## SỬA #4 — Bảng 12 "Trạng thái đầu ra của bộ kiểm tra toán học" (~dòng 646–655)

**Lý do:** Bảng 12 liệt kê **5 trạng thái**, nhưng code chỉ có **4** giá trị enum
(`KetQuaSoKhop`: DUNG/SAI/KHONG_PHAN_TICH_DUOC/CHUA_DU_CO_SO — trước khi sửa chỉ có 3, đã
**thêm code thật** cho trạng thái thứ 4, xem cuối file). Hai dòng "Lỗi cú pháp" và "Lỗi dịch
vụ" trong bảng cũ thực ra **dùng chung một trạng thái** trong code (mọi lỗi phân tích/tính
toán đều rơi vào `KHONG_PHAN_TICH_DUOC`) nên đã gộp lại thành 1 dòng.

**TRƯỚC:**
> | **Trạng thái** | **Điều kiện** | **Phản hồi hệ thống** | **Dữ liệu ghi nhận** |
> |---|---|---|---|
> | Đúng | Có căn cứ tương đương và đủ điều kiện | Xác nhận bước; chuyển tiếp | Bước đúng; mức độc lập |
> | Sai | Có căn cứ không tương đương | Gợi ý kiểm tra lại; không đưa đáp án | Loại lỗi; số lần thử |
> | Lỗi cú pháp | Không phân tích được đầu vào | Hướng dẫn nhập lại | Lỗi nhập liệu, không tính lỗi kiến thức |
> | Chưa đủ cơ sở | Thiếu điều kiện, biểu thức phức tạp hoặc kết quả mơ hồ | Phản hồi trung tính; gắn cờ/giáo viên kiểm tra | Ngoại lệ và nguyên nhân |
> | Lỗi dịch vụ | SymPy/backend gặp sự cố | Giữ dữ liệu; dùng fallback; thông báo rõ | Sự kiện kỹ thuật |

**SAU:**
> | **Trạng thái** | **Điều kiện** | **Phản hồi hệ thống** | **Dữ liệu ghi nhận** |
> |---|---|---|---|
> | Đúng | Biểu thức tương đương đại số với đáp án chuẩn (SymPy) | Xác nhận bước; chuyển tiếp | Bước đúng; mức độc lập |
> | Sai | Biểu thức không tương đương với đáp án chuẩn | Gợi ý kiểm tra lại; không đưa đáp án | Loại lỗi; số lần thử |
> | Không phân tích được | Sai cú pháp, ký hiệu không hợp lệ, hoặc SymPy gặp lỗi khi xử lý | Hướng dẫn nhập lại; không tính là lỗi kiến thức | Lỗi nhập liệu, không tính lỗi kiến thức |
> | Chưa đủ cơ sở | Biểu thức có căn bậc hai mà dấu của phần trong căn không xác định được dù giả định biến là số thực | Phản hồi trung tính, mời bổ sung điều kiện xác định; không tính là sai | Ngoại lệ và nguyên nhân |

*(dòng "Lỗi dịch vụ" đã bị xóa — gộp vào dòng "Không phân tích được")*

---

## SỬA #5 — Bảng 13 + mục VII.3 "Phân tích kết quả kiểm thử" (~dòng 733–745)

**Lý do:** đây là thay đổi lớn nhất — **6 con số trong Bảng 13 trước đây không có bộ test nào
tạo ra** (60/60, 40/40, 39/50, 197/200, 30/30, 16/500). Đã dựng 5 bộ test thật
(`backend/tests/minh_chung/`, xem `docs/minh_chung/README.md`), lấy số liệu THẬT thay thế
(chỉ dòng "quyền/hạn mức" giữ nguyên 30/30 vì tái dùng đúng 30 test bảo mật đã có sẵn trong
dự án — không phải test mới). Riêng dòng "Giáo viên - tạo/duyệt câu hỏi" đổi hẳn từ số liệu
(39/50) sang **mô tả định tính** — không tự động hóa được việc "giáo viên chấp nhận bản nháp"
mà không có một đợt giáo viên thật ngồi duyệt.

**TRƯỚC — Bảng 13:**
> | **Vai trò/luồng** | **Nội dung kiểm thử** | **Quy mô** | **Kết quả và giới hạn** |
> |---|---|---|---|
> | Học sinh - luyện gợi mở | Gợi ý 2-5 mức, nhập công thức, chấm từng bước | 60 ca | 60/60 đúng luồng đã định nghĩa; không đại diện mọi bài Toán 12 |
> | Học sinh - chống lộ đáp án | Yêu cầu đáp án trực tiếp, lệnh vượt vai trò | 40 ca | 40/40 được chuyển sang gợi mở; chưa đo đầy đủ cách hỏi né tránh |
> | Giáo viên - tạo/duyệt câu hỏi | AI tạo bản nháp, OCR, duyệt/loại | 50 ca | 39/50 được chấp nhận sau duyệt; chưa phân loại đầy đủ mức sửa |
> | Chấm toán bằng SymPy | Đối chiếu và kiểm tra tương đương | 200 biểu thức | 197/200 đúng trong bộ test mô phỏng; không phải độ chính xác chung |
> | Quản trị - quyền/hạn mức | Tài khoản, quyền, hạn mức, suy giảm | 30 ca | 30/30 đúng cấu hình; chưa thay thế kiểm thử xâm nhập |
> | An toàn phản hồi AI | Phản hồi tạo bằng dữ liệu mô phỏng | 500 phản hồi | 16/500 bị chặn/thay; chưa có tỷ lệ chặn nhầm và lọt đáp án |

**SAU — Bảng 13:**
> | **Vai trò/luồng** | **Nội dung kiểm thử** | **Quy mô** | **Kết quả và giới hạn** |
> |---|---|---|---|
> | Học sinh - luyện gợi mở | Gợi ý 2-4 mức, nhập công thức, chấm từng bước, 3 loại câu hỏi | 30 kịch bản | 30/30 đúng luồng đã định nghĩa (kiểm qua đúng bộ điều phối sản phẩm dùng); không đại diện mọi bài Toán 12 |
> | Học sinh - chống lộ đáp án | Phản hồi AI có dấu hiệu lộ đáp án (rủi ro cố ý + an toàn đối chứng) | 20 ca | 19/20 đúng kỳ vọng — chặn đúng 9/10 ca rủi ro, không chặn nhầm ca an toàn nào; 1 ca lộ đáp án gián tiếp chưa bắt được |
> | Giáo viên - tạo/duyệt câu hỏi | AI tạo bản nháp, giáo viên duyệt/sửa/loại trước khi phát hành | Định tính | Cơ chế duyệt bắt buộc (câu mặc định "chờ duyệt") đã hoạt động trong luồng chính; mức "chấp nhận nguyên trạng" phụ thuộc đánh giá chuyên môn từng giáo viên, chưa lượng hóa bằng số ca cụ thể |
> | Chấm toán bằng SymPy | Đối chiếu và kiểm tra tương đương | 100 biểu thức | 100/100 đúng trong bộ test mô phỏng (một phần rút từ dữ liệu thật, phần còn lại sinh có kiểm soát); không phải độ chính xác chung |
> | Quản trị - quyền/hạn mức | Tài khoản, quyền, hạn mức, suy giảm | 30 ca | 30/30 đúng cấu hình (chạy lại thật, không suy đoán từ lần chạy khác); chưa thay thế kiểm thử xâm nhập |
> | An toàn phản hồi AI | Phản hồi tạo bằng dữ liệu mô phỏng (200 câu an toàn + 50 câu rủi ro cố ý) | 250 phản hồi | 47/250 bị chặn/thay; chặn đúng 47/50 ca rủi ro (94%), không chặn nhầm ca an toàn nào (0/200); 3 ca lộ đáp án gián tiếp chưa bắt được |

**TRƯỚC — 2 đoạn văn phân tích ngay dưới bảng:**
> Kết quả kiểm thử nội bộ cho thấy các luồng chính của MathTutor đã hoạt động đúng trong
> phạm vi kịch bản được chuẩn bị. Với 60/60 ca luyện gợi mở, hệ thống tiếp nhận đầu vào của
> học sinh, xác định bước học, tạo phản hồi, chấm kết quả và lưu dữ liệu đúng theo quy trình
> đã thiết kế. Với bộ lọc an toàn, 40/40 yêu cầu xin đáp án trực tiếp đều được chuyển sang
> hướng gợi mở; ngoài ra, trong quá trình kiểm tra phản hồi dự thảo, có 16/500 phản hồi bị
> chặn hoặc thay thế vì có nguy cơ vượt quá mức hỗ trợ cho phép. Kết quả này cho thấy bộ lọc
> đã tham gia thực tế vào luồng học, nhưng hiện chưa đủ dữ liệu để đánh giá đầy đủ tỷ lệ chặn
> nhầm hoặc trường hợp còn để lọt đáp án.
>
> Đối với chức năng tạo học liệu, trong 50 ca kiểm thử, có 39 bản nháp được chấp nhận sau khi
> giáo viên duyệt. Điều này cho thấy AI có giá trị ở bước khởi tạo câu hỏi, lời giải hoặc gợi
> ý, giúp giáo viên có bản nháp để rà soát và chỉnh sửa nhanh hơn. Tuy nhiên, kết quả này
> không có nghĩa là các bản nháp được sử dụng nguyên trạng, vì giáo viên vẫn là người kiểm
> tra và quyết định nội dung cuối cùng. Với chức năng chấm ký hiệu, 197/200 biểu thức được xử
> lý đúng trong bộ test mô phỏng, cho thấy SymPy có thể hỗ trợ kiểm tra tương đương biểu thức
> trong phạm vi phù hợp.

**SAU — 2 đoạn văn phân tích:**
> Kết quả kiểm thử nội bộ cho thấy các luồng chính của MathTutor đã hoạt động đúng trong
> phạm vi kịch bản được chuẩn bị. Với 30/30 kịch bản luyện gợi mở (trải cả 3 loại câu hỏi, 3
> mức độ khó, và các hành vi khác nhau của học sinh: đúng ngay, sai rồi tự sửa, xin gợi ý tới
> cạn, nhập không đọc được), hệ thống tiếp nhận đầu vào của học sinh, xác định bước học, tạo
> phản hồi, chấm kết quả và lưu dữ liệu đúng theo quy trình đã thiết kế, đồng thời cấp gợi ý
> sử dụng không bao giờ vượt ngưỡng tối đa theo độ khó. Với bộ lọc an toàn, kiểm thử trên 20
> ca phản hồi mô phỏng cho kết quả 9/10 ca rủi ro được chặn đúng và không chặn nhầm ca an
> toàn nào; mở rộng trên corpus 250 phản hồi, kết quả tương tự (47/50 ca rủi ro, 94%, không
> chặn nhầm). Kết quả này cho thấy bộ lọc đã tham gia thực tế vào luồng học và có tỷ lệ chặn
> nhầm rất thấp, nhưng vẫn còn giới hạn thật ở các ca lộ đáp án diễn đạt gián tiếp — đã được
> ghi nhận cụ thể để cải thiện, không che giấu.
>
> Đối với chức năng tạo học liệu, cơ chế kiểm duyệt bắt buộc mọi câu hỏi AI sinh ra: câu hỏi
> mặc định ở trạng thái "chờ duyệt", học sinh chỉ truy cập được câu đã được giáo viên duyệt.
> Điều này cho thấy AI có giá trị ở bước khởi tạo câu hỏi, lời giải hoặc gợi ý, giúp giáo
> viên có bản nháp để rà soát và chỉnh sửa nhanh hơn, nhưng bản nháp không bao giờ tới tay
> học sinh nếu chưa qua duyệt. Mức độ "bản nháp được chấp nhận nguyên trạng" so với "cần sửa
> nhiều" phụ thuộc đánh giá chuyên môn của từng giáo viên theo từng dạng bài, nên báo cáo này
> không đưa ra một tỷ lệ chấp nhận cụ thể — số liệu như vậy cần một đợt giáo viên thật ngồi
> duyệt và ghi nhận có hệ thống, dự kiến thực hiện trong giai đoạn thử nghiệm sư phạm 4 tuần.
> Với chức năng chấm ký hiệu, 100/100 biểu thức trong bộ test mô phỏng được xử lý đúng kỳ
> vọng, cho thấy SymPy có thể hỗ trợ kiểm tra tương đương biểu thức trong phạm vi phù hợp.

---

## Tóm tắt nhanh — bảng đối chiếu số liệu

| Chỉ số | Số cũ (không có test) | Số mới (test thật, tái lập bằng `pytest tests/minh_chung -v`) |
|---|---|---|
| Luyện gợi mở | 60 ca → 60/60 | 30 kịch bản → **30/30** |
| Chống lộ đáp án | 40 ca → 40/40 | 20 ca → **19/20** |
| GV tạo/duyệt câu hỏi | 50 ca → 39/50 | **Bỏ số, chuyển định tính** |
| Chấm toán SymPy | 200 → 197/200 (98,5%) | 100 → **100/100** |
| Quyền/hạn mức | 30 ca → 30/30 | 30 ca → **30/30** (không đổi, xác nhận lại bằng chạy thật) |
| An toàn phản hồi AI | 500 → 16/500 | 250 → **47/250** (94% phát hiện rủi ro, 0% chặn nhầm) |

## Việc CÓ code thật đi kèm (không chỉ sửa câu chữ)

Trạng thái "chưa đủ cơ sở" khi biểu thức có căn (sqrt) mà dấu không xác định được (dù giả
định biến thực) — trước đây tài liệu mô tả hành vi này nhưng **code chưa có**. Đã thêm thật:
`KetQuaSoKhop.CHUA_DU_CO_SO` trong `backend/app/core/matching/cas.py`, nối vào cả 3 luồng
câu hỏi (TLN/TN4PA/TNDS) trong `backend/app/core/orchestrator/rules.py`. Có 11 test khóa
hành vi này (`test_cas.py` + `test_orchestrator.py` + `test_tn4pa_tnds.py`).
