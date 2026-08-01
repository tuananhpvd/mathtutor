import { test, expect } from '@playwright/test'

// Cổng chặn "không vỡ giao diện trên mobile" (UIUX mục 5, đã bị vi phạm 2 lần trước đây —
// v127/v129 phải sửa hàng loạt vì thiếu grid-cols-1 ở base). Duyệt mọi trang chính của cả 3
// vai trò ở khổ điện thoại (375px, hẹp hơn iPhone SE) và fail nếu có TRÀN NGANG
// (document.documentElement.scrollWidth > clientWidth) — dấu hiệu chuẩn của layout vỡ.
//
// KHÔNG bắt được: chữ quá nhỏ, nút bấm quá sát, layout "không tràn nhưng khó dùng" — những
// thứ đó vẫn cần mắt người. Đây chỉ là lưới an toàn máy móc cho lớp lỗi đã từng xảy ra.

test.use({ viewport: { width: 375, height: 700 } })

async function dangNhap(page, dn, mk) {
  await page.goto('/')
  await page.getByLabel('Tên đăng nhập').fill(dn)
  await page.getByLabel('Mật khẩu', { exact: true }).fill(mk)
  await page.getByRole('button', { name: 'Đăng nhập' }).click()
  await page.waitForTimeout(600)
}

async function khongTranNgang(page, ghiChu) {
  const bitran = await page.evaluate(() => {
    const el = document.documentElement
    return el.scrollWidth > el.clientWidth + 1 // +1: dung sai làm tròn subpixel
  })
  expect(bitran, `Tràn ngang (vỡ layout mobile) tại: ${ghiChu}`).toBe(false)
}

// HS: menu chính là thanh tab cố định đáy màn hình (luôn hiện, không cần mở gì) — xem
// BottomTabBar trong RoleLayout.jsx.
test('HS: không trang nào tràn ngang ở khổ điện thoại', async ({ page }) => {
  await dangNhap(page, 'hs1', 'hs123')
  await khongTranNgang(page, 'Trang chủ')

  const NHAN = ['Nhiệm vụ', 'Mục tiêu', 'Lý thuyết', 'Chọn bài', 'Thi thử', 'Tiến độ']
  for (const nhan of NHAN) {
    await page.getByRole('button', { name: nhan, exact: true }).click()
    await page.waitForTimeout(400)
    await khongTranNgang(page, `HS › ${nhan}`)
  }
})

// GV/Admin: menu ẩn sau nút hamburger, mở bằng drawer trượt (SidebarLayout, chế độ <md) —
// phải mở drawer TRƯỚC mỗi lần bấm mục vì chọn xong tự đóng lại (chonMucDrawer).
async function duyetMenuDrawer(page, nhanList, tienTo) {
  for (const nhan of nhanList) {
    await page.getByRole('button', { name: 'Mở menu' }).click()
    await page.getByRole('button', { name: nhan, exact: true }).click()
    await page.waitForTimeout(400)
    await khongTranNgang(page, `${tienTo} › ${nhan}`)
  }
}

test('GV: không trang nào tràn ngang ở khổ điện thoại', async ({ page }) => {
  await dangNhap(page, 'gv1', 'gv123')
  await khongTranNgang(page, 'GV › Tổng quan (trang mặc định)')

  const NHAN = [
    'Danh mục', 'Lý thuyết', 'Câu hỏi', 'AI sinh câu hỏi', 'Cờ theo dõi',
    'Hỗ trợ học sinh', 'Giao nhiệm vụ', 'Đề thi thử', 'Tiến bộ học sinh',
    'Quản lý lớp', 'Quản lý học sinh', 'Tài khoản cá nhân',
  ]
  await duyetMenuDrawer(page, NHAN, 'GV')
})

test('Admin: không trang nào tràn ngang ở khổ điện thoại', async ({ page }) => {
  await dangNhap(page, 'admin', 'admin123')
  await khongTranNgang(page, 'Admin › Dashboard (trang mặc định)')

  const NHAN = [
    'Quản lý tài khoản', 'Quản lý lớp', 'Quản lý giáo viên', 'Quản lý học sinh',
    'Cấu hình', 'Nhật ký', 'Tài khoản cá nhân',
  ]
  await duyetMenuDrawer(page, NHAN, 'Admin')
})
