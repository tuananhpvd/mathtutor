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

  // Học sinh — bài & phiên
  listProblems: () => request('/problems'),
  getProblem: (id) => request(`/problems/${id}`),
  createSession: (problem_id) => post('/sessions', { problem_id }),
  getSession: (id) => request(`/sessions/${id}`),
  getDangDo: () => request('/sessions/dang-do'),
  sendMessage: (sessionId, body) => post(`/sessions/${sessionId}/message`, body),

  // Học sinh — tiến độ
  getProgressMe: () => request('/progress/me'),

  // Giáo viên / Admin (Phase 9–10)
  getProgressStudents: () => request('/progress/students'),
  genQuestions: (body) => post('/questions-ai/generate', body),
  listChoDuyet: () => request('/questions-ai/cho-duyet'),
  duyetCau: (id, hanh_dong) => post(`/questions-ai/${id}/duyet`, { hanh_dong }),
  updateProblem: (id, body) =>
    request(`/problems/${id}`, { method: 'PATCH', body: JSON.stringify(body) }),
  deleteProblem: (id) => request(`/problems/${id}`, { method: 'DELETE' }),
  listFlags: (trang_thai) =>
    request('/monitor/flags' + (trang_thai ? `?trang_thai=${trang_thai}` : '')),
  updateFlag: (id, trang_thai) =>
    request(`/monitor/flags/${id}?trang_thai=${trang_thai}`, { method: 'PATCH' }),
  listSessionsHoanThanh: () => request('/monitor/sessions-hoan-thanh'),

  // Danh mục chuyên đề / dạng (GV + Admin)
  getDanhMuc: () => request('/danh-muc'),
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
  adminCreateUser: (body) => post('/admin/users', body),
  adminSetUserStatus: (id, trang_thai) =>
    request(`/admin/users/${id}/trang-thai`, {
      method: 'PATCH',
      body: JSON.stringify({ trang_thai }),
    }),
  adminGetConfig: () => request('/admin/config'),
  adminSetConfig: (khoa, gia_tri) =>
    request('/admin/config', { method: 'PATCH', body: JSON.stringify({ khoa, gia_tri }) }),
}
