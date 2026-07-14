import { baoPhienHetHan } from './auth'

const BASE = '/api'
// Request thường (CRUD) — mạng chập chờn lúc thi không nên treo vô hạn.
const TIMEOUT_MAC_DINH_MS = 30000
// Lệnh gọi có LLM (chat, sinh câu hỏi, đọc ảnh đề, phân tích năng lực...) — LLM tự thử
// lại vài lần khi lỗi tạm thời nên cần nhiều thời gian hơn hẳn 1 request CRUD thường.
const TIMEOUT_AI_MS = 90000

async function request(path, { timeoutMs = TIMEOUT_MAC_DINH_MS, ...options } = {}) {
  const token = sessionStorage.getItem('token')
  const headers = { 'Content-Type': 'application/json', ...options.headers }
  if (token) headers['Authorization'] = `Bearer ${token}`

  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), timeoutMs)
  let res
  try {
    res = await fetch(BASE + path, { ...options, headers, signal: controller.signal })
  } catch (err) {
    if (err.name === 'AbortError') {
      throw new Error('Máy chủ phản hồi quá lâu, vui lòng thử lại.', { cause: err })
    }
    throw new Error('Không kết nối được máy chủ, kiểm tra mạng và thử lại.', { cause: err })
  } finally {
    clearTimeout(timer)
  }

  const data = await res.json().catch(() => ({}))
  if (res.status === 401) {
    // Token hết hạn hoặc không hợp lệ — chuyển mềm về màn đăng nhập (setPage('login') ở
    // App.jsx) thay vì reload cứng cả trang, tránh xóa sạch dữ liệu đang nhập dở ở những
    // phần KHÁC của trang chưa kịp lưu (vd GV đang soạn dở 1 câu hỏi dài ở dialog khác).
    baoPhienHetHan()
    throw new Error('Phiên đăng nhập hết hạn, vui lòng đăng nhập lại')
  }
  if (!res.ok) throw new Error(data.detail || `Lỗi ${res.status}`)
  return data
}

const post = (path, body, timeoutMs) =>
  request(path, { method: 'POST', body: JSON.stringify(body || {}), timeoutMs })

// Query string cho khoảng thời gian báo cáo (bỏ tham số rỗng).
function _qsKhoang(tuNgay, denNgay) {
  const p = new URLSearchParams()
  if (tuNgay) p.set('tu_ngay', tuNgay)
  if (denNgay) p.set('den_ngay', denNgay)
  const s = p.toString()
  return s ? `?${s}` : ''
}

export const api = {
  // Chung
  login: (dang_nhap, mat_khau) => post('/auth/login', { dang_nhap, mat_khau }),
  health: () => request('/health'),

  // Học sinh — bài & phiên (gv_id: Quản lý/Admin lọc theo GV)
  listProblems: (gv_id) => request('/problems' + (gv_id ? `?gv_id=${gv_id}` : '')),
  getProblem: (id) => request(`/problems/${id}`),
  createSession: (problem_id) => post('/sessions', { problem_id }),
  getSession: (id) => request(`/sessions/${id}`),
  getDangDo: () => request('/sessions/dang-do'),
  getPhienCuaToi: () => request('/sessions/cua-toi'),
  sendMessage: (sessionId, body) => post(`/sessions/${sessionId}/message`, body, TIMEOUT_AI_MS),
  xemLaiPhien: (sessionId) => request(`/sessions/${sessionId}/xem-lai`),

  // Học sinh — tiến độ
  getProgressMe: () => request('/progress/me'),
  getThongKeMe: () => request('/progress/me/thong-ke'),
  getPhanTichMe: () => request('/progress/me/phan-tich'),
  capNhatPhanTichMe: () => post('/progress/me/phan-tich/cap-nhat', null, TIMEOUT_AI_MS),

  // Học sinh — hồ sơ cá nhân
  hsHoSo: () => request('/hs/ho-so'),
  hsCapNhatHoSo: (body) => request('/hs/ho-so', { method: 'PATCH', body: JSON.stringify(body) }),
  hsHuongDanPhongHoc: () => request('/hs/huong-dan-phong-hoc'),

  // Giáo viên / Admin (Phase 9–10)
  getProgressStudents: () => request('/progress/students'),
  getTongHopLop: () => request('/progress/lop/tong-hop'),
  getThongKeHocSinh: (id) => request(`/progress/students/${id}/thong-ke`),
  getPhanTichHocSinh: (id) => request(`/progress/students/${id}/phan-tich`),
  capNhatPhanTichHocSinh: (id) => post(`/progress/students/${id}/phan-tich/cap-nhat`, null, TIMEOUT_AI_MS),
  // Báo cáo kết quả cho phụ huynh (GV in ra PDF) — tuNgay/denNgay dạng 'YYYY-MM-DD' (tùy chọn).
  getBaoCaoChoPhep: () => request('/progress/bao-cao/cho-phep'),
  getBaoCaoHocSinh: (id, tuNgay, denNgay) =>
    request(`/progress/students/${id}/bao-cao${_qsKhoang(tuNgay, denNgay)}`),
  getBaoCaoLop: (lopId, tuNgay, denNgay) =>
    request(`/progress/lop/${lopId}/bao-cao${_qsKhoang(tuNgay, denNgay)}`),
  genQuestions: (body) => post('/questions-ai/generate', body, TIMEOUT_AI_MS),
  taoBuocGoiY: (body) => post('/questions-ai/tao-buoc-goi-y', body, TIMEOUT_AI_MS),
  luuBuocGoiY: (cau) => post('/questions-ai/tao-buoc-goi-y/luu', { cau }),
  docDeTuAnh: (body) => post('/questions-ai/doc-de-tu-anh', body, TIMEOUT_AI_MS),
  listChoDuyet: () => request('/questions-ai/cho-duyet'),
  duyetCau: (id, hanh_dong) => post(`/questions-ai/${id}/duyet`, { hanh_dong }),
  uploadHinh: async (file) => {
    const token = sessionStorage.getItem('token')
    const fd = new FormData()
    fd.append('file', file)
    const res = await fetch(BASE + '/problems/upload-hinh', {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: fd,
    })
    const data = await res.json().catch(() => ({}))
    if (!res.ok) throw new Error(data.detail || `Lỗi ${res.status}`)
    return data // { url }
  },
  veDoThi: (body) => post('/problems/ve-do-thi', body),
  veBBT: (body) => post('/problems/ve-bbt', body),
  latexSangSympy: (latex) => post('/problems/latex-sang-sympy', { latex }),
  createProblem: (body) => post('/problems', body),
  updateProblem: (id, body) =>
    request(`/problems/${id}`, { method: 'PATCH', body: JSON.stringify(body) }),
  deleteProblem: (id) => request(`/problems/${id}`, { method: 'DELETE' }),
  khoiPhucProblem: (id) => request(`/problems/${id}/khoi-phuc`, { method: 'PATCH' }),
  anhHuongProblem: (id) => request(`/problems/${id}/anh-huong`),
  xoaVinhVienProblem: (id) => request(`/problems/${id}/vinh-vien`, { method: 'DELETE' }),
  listFlags: (trang_thai) =>
    request('/monitor/flags' + (trang_thai ? `?trang_thai=${trang_thai}` : '')),
  updateFlag: (id, trang_thai, loi_nhan = '') =>
    request(
      `/monitor/flags/${id}?trang_thai=${trang_thai}` +
        (loi_nhan ? `&loi_nhan=${encodeURIComponent(loi_nhan)}` : ''),
      { method: 'PATCH' }
    ),
  listSessionsHoanThanh: () => request('/monitor/sessions-hoan-thanh'),
  createFlag: (session_id, ghi_chu = '') =>
    request(
      `/monitor/flags?session_id=${session_id}` +
        (ghi_chu ? `&ghi_chu=${encodeURIComponent(ghi_chu)}` : ''),
      { method: 'POST' }
    ),

  // Giáo viên — hồ sơ + quản lý lớp & học sinh của mình
  gvTongQuan: () => request('/gv/tong-quan'),
  gvHoSo: () => request('/gv/ho-so'),
  gvCapNhatHoSo: (body) => request('/gv/ho-so', { method: 'PATCH', body: JSON.stringify(body) }),
  gvLop: () => request('/gv/lop'),
  gvTaoLop: (body) => post('/gv/lop', body),
  gvKiemTraTrung: (ten_lops) => post('/gv/lop/kiem-tra-trung', { ten_lops }),
  gvKiemTraHS: (lop_id, dang_nhaps) => post(`/gv/lop/${lop_id}/kiem-tra-hs`, { dang_nhaps }),
  gvImportHSBatch: (lop_id, hoc_sinhs) => post(`/gv/lop/${lop_id}/import-hs-batch`, { hoc_sinhs }),
  gvImportLopBatch: (ten_lops) => post('/gv/lop/import-batch', { ten_lops }),
  gvSuaLop: (id, body) => request(`/gv/lop/${id}`, { method: 'PATCH', body: JSON.stringify(body) }),
  gvXoaLop: (id) => request(`/gv/lop/${id}`, { method: 'DELETE' }),
  gvHocSinh: () => request('/gv/hoc-sinh'),
  gvTaoHocSinh: (body) => post('/gv/hoc-sinh', body),
  gvSuaHocSinh: (id, body) =>
    request(`/gv/hoc-sinh/${id}`, { method: 'PATCH', body: JSON.stringify(body) }),
  gvXoaHocSinh: (id) => request(`/gv/hoc-sinh/${id}`, { method: 'DELETE' }),
  gvGanLopHocSinh: (id, lop_id) =>
    request(`/gv/hoc-sinh/${id}/lop`, { method: 'PATCH', body: JSON.stringify({ lop_id }) }),
  gvDoiTrangThaiHocSinh: (id, trang_thai) =>
    request(`/gv/hoc-sinh/${id}/trang-thai`, { method: 'PATCH', body: JSON.stringify({ trang_thai }) }),

  // Đặt lại tiến độ HS (GV thực hiện ngay)
  gvDatLaiTienDo: (hs_id) => post(`/gv/dat-lai/${hs_id}`, {}),

  // Danh mục chuyên đề / dạng (GV + Admin; gv_id: Quản lý/Admin lọc theo GV)
  getDanhMuc: (gv_id) => request('/danh-muc' + (gv_id ? `?gv_id=${gv_id}` : '')),
  // Danh sách GV để tài khoản Quản lý chọn quản lý nội dung
  listGiaoVienQuanLy: () => request('/danh-muc/giao-vien'),
  themChuyenDe: (body) => post('/danh-muc/chuyen-de', body),
  capNhatChuyenDe: (id, body) =>
    request(`/danh-muc/chuyen-de/${id}`, { method: 'PATCH', body: JSON.stringify(body) }),
  xoaChuyenDe: (id) => request(`/danh-muc/chuyen-de/${id}`, { method: 'DELETE' }),
  themDang: (body) => post('/danh-muc/dang', body),
  capNhatDang: (id, body) =>
    request(`/danh-muc/dang/${id}`, { method: 'PATCH', body: JSON.stringify(body) }),
  xoaDang: (id) => request(`/danh-muc/dang/${id}`, { method: 'DELETE' }),

  // Admin (Phase 10)
  adminStats: () => request('/admin/stats'),
  adminUsers: () => request('/admin/users'),
  adminLop: () => request('/admin/lop'),
  adminLopChiTiet: () => request('/admin/lop-chi-tiet'),
  adminGiaoVien: () => request('/admin/giao-vien'),
  adminHocSinh: () => request('/admin/hoc-sinh'),
  adminCreateUser: (body) => post('/admin/users', body),
  adminUpdateUser: (id, body) =>
    request(`/admin/users/${id}`, { method: 'PATCH', body: JSON.stringify(body) }),
  adminDeleteUser: (id) => request(`/admin/users/${id}`, { method: 'DELETE' }),
  adminSetUserLop: (id, lop_id) =>
    request(`/admin/users/${id}/lop`, { method: 'PATCH', body: JSON.stringify({ lop_id }) }),
  adminSetUserStatus: (id, trang_thai) =>
    request(`/admin/users/${id}/trang-thai`, {
      method: 'PATCH',
      body: JSON.stringify({ trang_thai }),
    }),
  adminCreateLop: (body) => post('/admin/lop', body),
  adminUpdateLop: (id, body) =>
    request(`/admin/lop/${id}`, { method: 'PATCH', body: JSON.stringify(body) }),
  adminDeleteLop: (id) => request(`/admin/lop/${id}`, { method: 'DELETE' }),
  adminGetConfig: () => request('/admin/config'),
  adminSetConfig: (khoa, gia_tri) =>
    request('/admin/config', { method: 'PATCH', body: JSON.stringify({ khoa, gia_tri }) }),
  trangThaiBaoTri: (ma) =>
    request('/trang-thai-bao-tri' + (ma ? `?ma=${encodeURIComponent(ma)}` : '')),
  adminQuetPhanTich: () => request('/admin/phan-tich/quet', { method: 'POST', timeoutMs: TIMEOUT_AI_MS }),
  adminLLMSuDung: () => request('/admin/llm-su-dung'),
  adminTuKhoaThu: (van_ban) => post('/admin/tu-khoa-thu', { van_ban }),
  // Đề ôn thi THPT (C1)
  deThiDs: () => request('/de-thi'),
  deThiTao: (body) => post('/de-thi', body),
  deThiTron: (body) => post('/de-thi/tron', body),
  deThiChiTietGV: (id) => request(`/de-thi/${id}/chi-tiet-gv`),
  deThiPhatHanh: (id, phat_hanh, pham_vi, lop_ids, hoc_sinh_ids) =>
    request(`/de-thi/${id}/phat-hanh`, {
      method: 'PATCH',
      body: JSON.stringify({ phat_hanh, pham_vi, lop_ids: lop_ids || [], hoc_sinh_ids: hoc_sinh_ids || [] }),
    }),
  deThiXoa: (id) => request(`/de-thi/${id}`, { method: 'DELETE' }),
  deThiKetQuaLop: (id) => request(`/de-thi/${id}/ket-qua-lop`),
  deThiChiTietBaiGV: (baiId) => request(`/de-thi/bai/${baiId}/chi-tiet-gv`),
  deThiBatDau: (id) => post(`/de-thi/${id}/bat-dau`),
  deThiXemBai: (baiId) => request(`/de-thi/bai/${baiId}`),
  deThiLuu: (baiId, bai_lam) =>
    request(`/de-thi/bai/${baiId}/luu`, { method: 'PATCH', body: JSON.stringify({ bai_lam }) }),
  deThiNop: (baiId, bai_lam) => post(`/de-thi/bai/${baiId}/nop`, { bai_lam }),
  getBanDoCuaToi: () => request('/progress/me/ban-do'),
  getBanDoLop: (lopId) =>
    request('/progress/ban-do/lop' + (lopId ? `?lop_id=${lopId}` : '')),
  getBanDoHocSinh: (id) => request(`/progress/students/${id}/ban-do`),
  getHieuQuaLop: () => request('/progress/hieu-qua/lop'),
  getHieuQuaHocSinh: (id) => request(`/progress/students/${id}/hieu-qua`),
  taiCsvHieuQua: async () => {
    // Tải file CSV (không phải JSON) — dùng fetch thô kèm token rồi kích hoạt tải về.
    const token = sessionStorage.getItem('token')
    const res = await fetch(BASE + '/progress/hieu-qua/lop/csv', {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })
    if (!res.ok) throw new Error(`Lỗi ${res.status}`)
    const blob = await res.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'hieu-qua-phuong-phap.csv'
    a.click()
    URL.revokeObjectURL(url)
  },
  adminKiemTraHS: (lop_id, dang_nhaps) => post(`/admin/lop/${lop_id}/kiem-tra-hs`, { dang_nhaps }),
  adminImportHSBatch: (lop_id, hoc_sinhs) => post(`/admin/lop/${lop_id}/import-hs-batch`, { hoc_sinhs }),
  adminKiemTraDangNhap: (dang_nhaps) => post('/admin/users/kiem-tra-dang-nhap', { dang_nhaps }),
  adminImportTaiKhoanBatch: (tai_khoans) => post('/admin/users/import-batch', { tai_khoans }),

  // Thông báo (đồng hành GV↔HS)
  thongBao: () => request('/thong-bao'),
  thongBaoChuaDoc: () => request('/thong-bao/chua-doc'),
  thongBaoDaDoc: (id) => post(`/thong-bao/${id}/da-doc`),
  thongBaoDocHet: () => post('/thong-bao/doc-het'),
  // GV gửi nhận xét cho HS
  gvNhanXetNhap: (hs_id) => request(`/gv/hoc-sinh/${hs_id}/nhan-xet-nhap`, { timeoutMs: TIMEOUT_AI_MS }),
  gvGuiNhanXet: (hs_id, noi_dung) => post(`/gv/hoc-sinh/${hs_id}/nhan-xet`, { noi_dung }),

  // Nhờ thầy/cô (A2)
  hsNhoThayCo: (session_id, noi_dung) => post('/tro-giup', { session_id, noi_dung }),
  gvTroGiup: (chiChoXuLy = false) =>
    request(`/tro-giup/gv${chiChoXuLy ? '?chi_cho_xu_ly=true' : ''}`),
  gvTraLoiTroGiup: (id, noi_dung) => post(`/tro-giup/${id}/tra-loi`, { noi_dung }),
  gvXoaTroGiup: (id) => request(`/tro-giup/${id}`, { method: 'DELETE' }),
  importCauHoiBatch: (items) => post('/problems/import-batch', { items }),

  // Giao bài/nhiệm vụ (A3)
  gvTaoNhiemVu: (body) => post('/nhiem-vu', body),
  gvNhiemVu: () => request('/nhiem-vu/gv'),
  gvDeXuatNhiemVu: (hoc_sinh_id) => request(`/nhiem-vu/de-xuat?hoc_sinh_id=${hoc_sinh_id}`),
  gvDeXuatTheoDang: (hoc_sinh_id, dang_id) =>
    request(`/nhiem-vu/de-xuat-dang?hoc_sinh_id=${hoc_sinh_id}&dang_id=${dang_id}`),
  gvXoaNhiemVu: (id) => request(`/nhiem-vu/${id}`, { method: 'DELETE' }),
  gvCapNhatNhiemVu: (id, body) => request(`/nhiem-vu/${id}`, { method: 'PATCH', body: JSON.stringify(body) }),
  hsNhiemVu: () => request('/nhiem-vu/hs'),

  // Chuỗi ngày học + cột mốc (C1)
  hsChuoiNgay: () => request('/hs/chuoi-ngay'),

  // Mục tiêu học tập (B1)
  hsMucTieu: () => request('/muc-tieu/hs'),
  hsMucTieuDeXuat: () => request('/muc-tieu/hs/de-xuat'),
  hsTaoMucTieu: (body) => post('/muc-tieu/hs', body),
  gvMucTieu: (hoc_sinh_id) => request(`/muc-tieu/gv/${hoc_sinh_id}`),
  gvMucTieuDeXuat: (hoc_sinh_id) => request(`/muc-tieu/gv/${hoc_sinh_id}/de-xuat`),
  gvTaoMucTieu: (hoc_sinh_id, body) => post(`/muc-tieu/gv/${hoc_sinh_id}`, body),
  xoaMucTieu: (id) => request(`/muc-tieu/${id}`, { method: 'DELETE' }),
}
