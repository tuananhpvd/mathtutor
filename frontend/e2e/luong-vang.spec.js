import { test, expect } from '@playwright/test'
import { E2E_API } from '../playwright.config'

// 3 "luồng vàng" E2E — bấm xuyên luồng thật trên trình duyệt (điều 518+ test backend và
// 23 test vitest không phủ được): HS làm trọn 1 bài TLN · GV duyệt câu hỏi · GV trả lời
// nhờ trợ giúp. DB e2e seed sẵn tài khoản mẫu (SQLite path của init_db) + 12 bài mẫu.
//
// Nguyên tắc: phần "dàn cảnh" (tạo dữ liệu tiền đề) đi qua API cho nhanh/ổn định; phần
// đang kiểm chứng thì bấm thật trên UI.

async function dangNhapUI(page, dn, mk) {
  await page.goto('/')
  await page.getByLabel('Tên đăng nhập').fill(dn)
  await page.getByLabel('Mật khẩu', { exact: true }).fill(mk)
  await page.getByRole('button', { name: 'Đăng nhập' }).click()
}

async function apiToken(request, dn, mk) {
  const r = await request.post(`${E2E_API}/auth/login`, {
    data: { dang_nhap: dn, mat_khau: mk },
  })
  expect(r.ok()).toBeTruthy()
  return (await r.json()).access_token
}

// Nhập biểu thức vào <math-field> (MathLive): gán value rồi bắn event 'input' — đúng sự
// kiện FormulaEditor lắng nghe; gõ phím thật vào math-field không ổn định trên CI/headless.
async function nhapMathField(page, latex) {
  const mf = page.locator('math-field')
  await expect(mf).toBeVisible()
  await mf.evaluate((el, v) => {
    el.value = v
    el.dispatchEvent(new Event('input', { bubbles: true }))
  }, latex)
}

test('HS làm trọn vẹn 1 bài TLN: đăng nhập → chọn bài → giải 2 bước → hoàn thành', async ({ page }) => {
  await dangNhapUI(page, 'hs1', 'hs123')

  // Vào "Chọn bài", lọc loại "Trả lời ngắn"
  // Lưới bộ lọc: Nhiệm vụ, Chuyên đề, Dạng, Loại câu, Mức độ, Trạng thái (v143 thêm
  // "Nhiệm vụ" lên đầu — chỉ số dịch từ 2 → 3 cho đúng vị trí "Loại câu").
  await page.getByRole('button', { name: 'Chọn bài' }).click()
  await page.locator('select').nth(3).selectOption('TLN')

  // Bài TLN 2 bước đã biết lời giải chuẩn: f(x) = x^3 - 3x, nghịch biến trên (-a; a), a = 1
  const card = page.locator('.rounded-card').filter({ hasText: 'nghịch biến trên khoảng' })
  await card.getByRole('button', { name: 'Bắt đầu' }).click()

  // Phòng học mở, bước 1/2: tính f'(x) = 3x^2 - 3
  // Scope vào thẻ <p> (card "Bước x/y" ở Khu vực trả lời) — "dải phân cách bước" trong khung
  // chat (v159) cũng hiện cùng chữ "Bước x/y" ở thẻ <span> khi bước chuyển, nên getByText mù
  // sẽ khớp 2 phần tử (strict mode violation) từ bước 2 trở đi.
  await expect(page.locator('p', { hasText: 'Bước 1/2' })).toBeVisible()
  await nhapMathField(page, '3x^2-3')
  await page.getByRole('button', { name: 'Gửi câu trả lời' }).click()

  // Đúng bước 1 → sang bước 2/2: tìm a = 1
  await expect(page.locator('p', { hasText: 'Bước 2/2' })).toBeVisible()
  await nhapMathField(page, '1')
  await page.getByRole('button', { name: 'Gửi câu trả lời' }).click()

  // Hoàn thành bài
  await expect(page.getByText('Trả lời đúng - Hoàn thành bài!')).toBeVisible()

  // Gợi ý "Bài nên luyện tiếp" (v163): đây là phiên hoàn thành ĐẦU TIÊN của hs1 trên DB e2e
  // mới seed — chưa đủ dữ liệu (cần tối thiểu 2 bài/dạng, xem NGUONG_NHOM) nên dòng gợi ý
  // phải ẩn hẳn, KHÔNG hiện khung rỗng. Đợi phân tích năng lực tải xong (gọi ngầm khi bài
  // xong) rồi xác nhận màn hình hoàn thành vẫn nguyên vẹn, các nút vẫn dùng được.
  // Scope vào khung xanh "Hoàn thành" (.border-success) — có 2 nút "Chọn bài khác" trên
  // trang (1 ở header phòng học, 1 trong khung hoàn thành), getByRole mù sẽ khớp cả 2.
  await page.waitForTimeout(500)
  const khungHoanThanh = page.locator('.border-success')
  await expect(khungHoanThanh.getByText('Bài nên luyện tiếp')).not.toBeVisible()
  await expect(khungHoanThanh.getByRole('button', { name: 'Chọn bài khác' })).toBeVisible()
})

test('GV duyệt câu hỏi: câu chờ duyệt (tạo qua import) → bấm Duyệt → thành Đã duyệt', async ({ page, request }) => {
  // Dàn cảnh: gv1 import 1 câu → trạng thái cho_duyet
  const tok = await apiToken(request, 'gv1', 'gv123')
  const r = await request.post(`${E2E_API}/problems/import-batch`, {
    headers: { Authorization: `Bearer ${tok}` },
    data: {
      items: [{
        loai_cau: 'TLN', chuyen_de: 'Khảo sát hàm số', do_kho: 'de',
        de_bai: 'Câu E2E chờ duyệt: tính 1 + 1.', meta: { dap_an_cuoi: '2' },
      }],
    },
  })
  expect(r.ok()).toBeTruthy()
  const ketQua = await r.json()
  expect(ketQua.da_tao).toBe(1)
  const idCau = ketQua.ids[0]

  await dangNhapUI(page, 'gv1', 'gv123')
  await page.getByRole('button', { name: 'Câu hỏi', exact: true }).click()

  // Bảng câu hỏi không hiện đề bài (chỉ chuyên đề/loại/trạng thái) — nhận diện hàng qua
  // cột ID (số id trả về từ import ở trên).
  const hang = page.getByRole('row').filter({
    has: page.getByRole('cell', { name: String(idCau), exact: true }),
  })
  await expect(hang.getByText('Chờ duyệt')).toBeVisible()
  await hang.getByRole('button', { name: 'Duyệt', exact: true }).click()
  await expect(hang.getByText('Đã duyệt')).toBeVisible()
})

test('GV trả lời nhờ trợ giúp: HS nhờ (qua API) → GV xem chi tiết → trả lời → Đã trả lời', async ({ page, request }) => {
  // Dàn cảnh: hs1 mở 1 phiên rồi gửi "Nhờ thầy/cô"
  const tokHS = await apiToken(request, 'hs1', 'hs123')
  const hHS = { Authorization: `Bearer ${tokHS}` }
  const bai = await (await request.get(`${E2E_API}/problems`, { headers: hHS })).json()
  const rs = await request.post(`${E2E_API}/sessions`, {
    headers: hHS, data: { problem_id: bai[0].id },
  })
  expect(rs.ok()).toBeTruthy()
  const sid = (await rs.json()).session_id
  const rt = await request.post(`${E2E_API}/tro-giup`, {
    headers: hHS, data: { session_id: sid, noi_dung: 'Em bí bước này (E2E)' },
  })
  expect(rt.ok()).toBeTruthy()

  // GV: mở Hỗ trợ học sinh → Xem chi tiết → Trả lời (nút nằm TRONG popup) → Gửi
  await dangNhapUI(page, 'gv1', 'gv123')
  await page.getByRole('button', { name: 'Hỗ trợ học sinh' }).click()

  const yeuCau = page.locator('#yc-tro-giup-1, [id^="yc-tro-giup-"]')
    .filter({ hasText: 'Em bí bước này (E2E)' })
  await yeuCau.getByRole('button', { name: 'Xem chi tiết' }).click()

  await expect(page.getByText('Chi tiết yêu cầu trợ giúp')).toBeVisible()
  await page.getByRole('button', { name: 'Trả lời', exact: true }).click()
  await page.getByPlaceholder(/Viết câu trả lời/).fill('Em thử tính đạo hàm trước nhé (E2E).')
  await page.getByRole('button', { name: 'Gửi trả lời' }).click()

  await expect(page.getByText(/Đã trả lời .*Câu trả lời đã hiện trong bài/)).toBeVisible()
})

test('GV xem lại hội thoại từ trang Cờ theo dõi (v162)', async ({ page, request }) => {
  // Dàn cảnh: hs1 làm dở 1 phiên (chưa hoàn thành) rồi gv1 tự gắn cờ thủ công cho phiên đó —
  // đúng kịch bản thật: GV thấy cờ, cần xem lại hội thoại TRƯỚC khi xử lý.
  const tokHS = await apiToken(request, 'hs1', 'hs123')
  const hHS = { Authorization: `Bearer ${tokHS}` }
  const bai = await (await request.get(`${E2E_API}/problems`, { headers: hHS })).json()
  const rs = await request.post(`${E2E_API}/sessions`, {
    headers: hHS, data: { problem_id: bai[0].id },
  })
  expect(rs.ok()).toBeTruthy()
  const sid = (await rs.json()).session_id
  await request.post(`${E2E_API}/sessions/${sid}/message`, {
    headers: hHS, data: { noi_dung: 'Đánh dấu E2E xem lại', dap_an_nhap: '3' },
  })

  const tokGV = await apiToken(request, 'gv1', 'gv123')
  const rf = await request.post(`${E2E_API}/monitor/flags`, {
    headers: { Authorization: `Bearer ${tokGV}` },
    params: { session_id: sid, ghi_chu: 'Can chu y E2E' },
  })
  expect(rf.ok()).toBeTruthy()

  await dangNhapUI(page, 'gv1', 'gv123')
  await page.getByRole('button', { name: 'Cờ theo dõi' }).click()

  const hang = page.getByRole('row').filter({ hasText: 'Can chu y E2E' })
  await hang.getByRole('button', { name: 'Xem hội thoại' }).click()

  // Overlay mở đúng phiên (đang làm dở), đổi giọng theo vai trò GV và hiện đúng lượt HS
  // vừa gửi — chứng minh không chỉ mở overlay trống mà tải đúng dữ liệu.
  await expect(page.getByText(/Xem lại bài của/)).toBeVisible()
  await expect(page.getByText('Đang làm dở')).toBeVisible()
  await expect(page.getByText('Đánh dấu E2E xem lại')).toBeVisible()
})
