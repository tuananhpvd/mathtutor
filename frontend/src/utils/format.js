// Tách ISO timestamp → { gio: "HH:MM:SS", ngay: "DD/MM/YYYY" }
export function phanTachTg(iso) {
  if (!iso) return null
  const d = new Date(iso)
  if (isNaN(d)) return null
  return {
    gio: d.toLocaleTimeString('vi-VN'),
    ngay: d.toLocaleDateString('vi-VN'),
  }
}

// Định dạng thời gian giây → "Xs" / "Xm Ys".
export function dinhDangThoiGian(giay) {
  if (giay == null) return '—'
  const s = Math.max(0, Math.round(giay))
  if (s < 60) return `${s} giây`
  const phut = Math.floor(s / 60)
  const con = s % 60
  return con ? `${phut} phút ${con} giây` : `${phut} phút`
}

// Nhãn loại câu hiển thị cho học sinh.
export const NHAN_LOAI_CAU = {
  TLN: 'TRẢ LỜI NGẮN',
  TNDS: 'ĐÚNG/SAI',
  TN4PA: 'TRẮC NGHIỆM',
}

// Nhãn loại câu đầy đủ — dùng ở các bảng "mất nhiều thời gian" (Tổng quan GV, Tiến độ chi tiết).
export const NHAN_LOAI_MAT_THOI_GIAN = {
  TN4PA: 'Trắc nghiệm ABCD',
  TNDS: 'Đúng/Sai 4 ý',
  TLN: 'Trả lời ngắn',
}
