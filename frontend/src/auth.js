export function saveSession(token, vai_tro, ho_ten, la_quan_ly = false) {
  sessionStorage.setItem('token', token)
  sessionStorage.setItem('vai_tro', vai_tro)
  sessionStorage.setItem('ho_ten', ho_ten)
  sessionStorage.setItem('la_quan_ly', la_quan_ly ? '1' : '')
}

export function updateHoTen(ho_ten) {
  sessionStorage.setItem('ho_ten', ho_ten)
}

export function clearSession() {
  sessionStorage.removeItem('token')
  sessionStorage.removeItem('vai_tro')
  sessionStorage.removeItem('ho_ten')
  sessionStorage.removeItem('la_quan_ly')
}

export function getSession() {
  const token = sessionStorage.getItem('token')
  if (!token) return null
  return {
    token,
    vai_tro: sessionStorage.getItem('vai_tro'),
    ho_ten: sessionStorage.getItem('ho_ten'),
    la_quan_ly: sessionStorage.getItem('la_quan_ly') === '1',
  }
}

let phienHetHanHandler = null

// App.jsx đăng ký hàm này 1 lần lúc mount — cho phép api.js báo "phiên hết hạn" bằng
// cách chuyển state React về màn đăng nhập (setPage('login')) thay vì window.location.reload()
// cứng, tránh xóa sạch dữ liệu HS/GV đang nhập dở ở những phần khác của trang chưa kịp lưu.
export function dangKyPhienHetHan(handler) {
  phienHetHanHandler = handler
}

export function baoPhienHetHan() {
  clearSession()
  if (phienHetHanHandler) phienHetHanHandler()
  // Lưới an toàn: nếu chưa kịp đăng ký (vd lỗi 401 xảy ra rất sớm lúc App vừa tải), vẫn
  // đảm bảo đưa được người dùng về màn đăng nhập.
  else window.location.reload()
}
