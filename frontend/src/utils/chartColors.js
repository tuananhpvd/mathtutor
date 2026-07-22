/*
 * Thang màu tím (sequential, thương hiệu) dùng cho biểu đồ nhiệt/legend — gộp về 1 nơi
 * thay vì mỗi component tự khai báo mảng hex riêng (dễ lệch nhau qua thời gian).
 *
 * Cố ý giữ 2 hằng số RIÊNG (không ép về chung 1 mảng): mỗi ramp có số bậc và khoảng cách
 * độ sáng khác nhau, ĐÃ chạy qua validate_palette (contrast + phân tách CVD) cho đúng số
 * bậc của nó — gộp cưỡng bức về 1 mảng dùng chung cho cả 2 nơi có thể vô tình phá vỡ kết
 * quả validate đã có.
 */

// 5 bậc, nhạt→đậm KHÔNG đúng — thứ tự ĐẬM→NHẠT (80-100 → 0-19). Dùng cho bản đồ năng lực
// (BanDoNangLuc.jsx): giá trị thành thạo 0–100 là magnitude, 1 hue, lightness đơn điệu.
export const THANG_TIM = ['#4a3bc4', '#7867db', '#a294ea', '#c7bef4', '#ece9fb']

// 4 bậc, nhạt→đậm — dùng cho phân bố mức gợi ý 0/1/2/3+ (HieuQuaPhuongPhap.jsx). Thang
// THỨ BẬC riêng (không phải bản đồ năng lực), đã validate_palette PASS cho đúng 4 bậc này.
export const THANG_TIM_MUC_GOI_Y = ['#a294ea', '#8272e2', '#6353d0', '#4a3bc4']
