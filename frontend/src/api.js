const BASE = '/api'

async function request(path, options = {}) {
  const token = sessionStorage.getItem('token')
  const headers = { 'Content-Type': 'application/json', ...options.headers }
  if (token) headers['Authorization'] = `Bearer ${token}`

  const res = await fetch(BASE + path, { ...options, headers })
  const data = await res.json().catch(() => ({}))
  if (res.status === 401) {
    // Token hết hạn hoặc không hợp lệ — xóa session và reload về trang đăng nhập
    sessionStorage.removeItem('token')
    sessionStorage.removeItem('vai_tro')
    sessionStorage.removeItem('ho_ten')
    window.location.reload()
    throw new Error('Phiên đăng nhập hết hạn, vui lòng đăng nhập lại')
  }
  if (!res.ok) throw new Error(data.detail || `Lỗi ${res.status}`)
  return data
}

const post = (path, body) =>
  request(path, { method: 'POST', body: JSON.stringify(body || {}) })

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
  sendMessage: (sessionId, body) => post(`/sessions/${sessionId}/message`, body),

  // Học sinh — tiến độ
  getProgressMe: () => request('/progress/me'),
  getThongKeMe: () => request('/progress/me/thong-ke'),
  getPhanTichMe: () => request('/progress/me/phan-tich'),
  capNhatPhanTichMe: () => post('/progress/me/phan-tich/cap-nhat'),

  // Học sinh — hồ sơ cá nhân
  hsHoSo: () => request('/hs/ho-so'),
  hsCapNhatHoSo: (body) => request('/hs/ho-so', { method: 'PATCH', body: JSON.stringify(body) }),

  // Giáo viên / Admin (Phase 9–10)
  getProgressStudents: () => request('/progress/students'),
  getTongHopLop: () => request('/progress/lop/tong-hop'),
  getThongKeHocSinh: (id) => request(`/progress/students/${id}/thong-ke`),
  getPhanTichHocSinh: (id) => request(`/progress/students/${id}/phan-tich`),
  capNhatPhanTichHocSinh: (id) => post(`/progress/students/${id}/phan-tich/cap-nhat`),
  genQuestions: (body) => post('/questions-ai/generate', body),
  listChoDuyet: () => request('/questions-ai/cho-duyet'),
  duyetCau: (id, hanh_dong) => post(`/questions-ai/${id}/duyet`, { hanh_dong }),
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
  adminQuetPhanTich: () => request('/admin/phan-tich/quet', { method: 'POST' }),
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
  gvNhanXetNhap: (hs_id) => request(`/gv/hoc-sinh/${hs_id}/nhan-xet-nhap`),
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
