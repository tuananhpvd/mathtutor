// Hàm dùng chung cho các màn hình soạn/nhập câu hỏi (GV thủ công, AI sinh, import Excel) —
// tách riêng khỏi các file *.jsx chứa component để tránh (1) Fast Refresh phải reload cả
// trang mỗi khi sửa các hàm này, và (2) trùng lặp logic giữa nhiều nơi (từng có 2 bản
// kiemTraDapAnTLN gần giống hệt nhau ở QuanLyCauHoi.jsx và ImportCauHoiDialog.jsx — sửa quy
// tắc ở 1 nơi rất dễ quên sửa nơi kia).

export function kiemTraDapAnTLN(v) {
  const val = String(v ?? '').trim()
  if (!val) return 'Đáp án cuối không được để trống'
  if (val.length > 4) return 'Đáp án cuối tối đa 4 ký tự (gồm dấu - và dấu ,)'
  if (!/^-?\d+([.,]\d+)?$/.test(val)) return 'Đáp án cuối phải là số nguyên hoặc số thập phân (ví dụ: 3, -2, 1,5)'
  return null
}

// Tập hợp danh sách dạng → options (dùng chung).
export function dungDangOptions(danhMuc) {
  return [
    { value: '', label: '— Chưa gán dạng —' },
    ...danhMuc.flatMap((cd) =>
      cd.dang_list.map((d) => ({ value: String(d.id), label: `${cd.ten} › ${d.ten}`, cd: cd.ten }))
    ),
  ]
}

// Chuẩn hóa payload các bước.
export function chuanHoaSteps(steps) {
  return steps.map((s) => ({
    thu_tu: s.thu_tu,
    pham_vi: s.pham_vi || 'ca_bai',
    mo_ta: s.mo_ta || '',
    bieu_thuc_ket_qua: s.bieu_thuc_ket_qua || '',
    danh_sach_goi_y: (s.danh_sach_goi_y || []).filter((g) => g.trim()),
  }))
}
