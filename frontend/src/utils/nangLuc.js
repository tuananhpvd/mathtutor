// Tone/màu cho từng mức "nhan" (manh/kha/can_cai_thien/chua_du_lieu). Nhãn TIẾNG VIỆT hiển
// thị (nhan_hien_thi) do BACKEND trả về — nguồn duy nhất, xem NHAN_HIEN_THI trong
// backend/app/services/phan_tich_service.py — FE chỉ quyết định MÀU SẮC ở đây.
//
// Chỉ mức "Cần luyện thêm" (can_cai_thien) mới dùng màu cảnh báo/nguy hiểm: đây là mức DUY
// NHẤT cần hành động. Mức "Ổn" (kha) dùng tone trung tính-tích cực (primary), KHÔNG dùng màu
// warning — vì không có hành động nào cần làm ngay ở mức này, tô vàng dễ khiến GV/HS hiểu
// nhầm là đang có vấn đề.
export const TONE_NHAN = {
  manh: 'success',
  kha: 'primary',
  can_cai_thien: 'danger',
  chua_du_lieu: 'neutral',
}

export const BAR_NHAN = {
  manh: 'bg-success',
  kha: 'bg-primary',
  can_cai_thien: 'bg-danger',
  chua_du_lieu: 'bg-surface-2',
}
