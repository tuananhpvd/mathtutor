import { describe, expect, it } from 'vitest'
import { chuanHoaSteps, dungDangOptions, kiemTraDapAnTLN } from './cauHoi'

describe('kiemTraDapAnTLN', () => {
  it('báo lỗi khi để trống', () => {
    expect(kiemTraDapAnTLN('')).toMatch(/không được để trống/)
    expect(kiemTraDapAnTLN(null)).toMatch(/không được để trống/)
    expect(kiemTraDapAnTLN(undefined)).toMatch(/không được để trống/)
    expect(kiemTraDapAnTLN('   ')).toMatch(/không được để trống/)
  })

  it('báo lỗi khi quá 4 ký tự', () => {
    expect(kiemTraDapAnTLN('12345')).toMatch(/tối đa 4 ký tự/)
  })

  it('báo lỗi khi không phải số', () => {
    expect(kiemTraDapAnTLN('abc')).toMatch(/phải là số/)
    expect(kiemTraDapAnTLN('1+1')).toMatch(/phải là số/)
  })

  it('chấp nhận số nguyên và số thập phân hợp lệ', () => {
    expect(kiemTraDapAnTLN('3')).toBeNull()
    expect(kiemTraDapAnTLN('-2')).toBeNull()
    expect(kiemTraDapAnTLN('1,5')).toBeNull()
    expect(kiemTraDapAnTLN('1.5')).toBeNull()
    expect(kiemTraDapAnTLN('  3  ')).toBeNull()
  })
})

describe('dungDangOptions', () => {
  it('luôn có option rỗng đầu tiên', () => {
    const options = dungDangOptions([])
    expect(options).toEqual([{ value: '', label: '— Chưa gán dạng —' }])
  })

  it('gộp danh sách dạng từ nhiều chuyên đề', () => {
    const danhMuc = [
      { ten: 'Hàm số', dang_list: [{ id: 1, ten: 'Đơn điệu' }, { id: 2, ten: 'Cực trị' }] },
      { ten: 'Tích phân', dang_list: [{ id: 3, ten: 'Diện tích' }] },
    ]
    const options = dungDangOptions(danhMuc)
    expect(options).toHaveLength(4)
    expect(options[1]).toEqual({ value: '1', label: 'Hàm số › Đơn điệu', cd: 'Hàm số' })
    expect(options[3]).toEqual({ value: '3', label: 'Tích phân › Diện tích', cd: 'Tích phân' })
  })
})

describe('chuanHoaSteps', () => {
  it('điền giá trị mặc định khi thiếu', () => {
    const result = chuanHoaSteps([{ thu_tu: 1 }])
    expect(result).toEqual([
      { thu_tu: 1, pham_vi: 'ca_bai', mo_ta: '', bieu_thuc_ket_qua: '', danh_sach_goi_y: [] },
    ])
  })

  it('lọc bỏ gợi ý rỗng', () => {
    const result = chuanHoaSteps([
      { thu_tu: 1, danh_sach_goi_y: ['gợi ý 1', '  ', '', 'gợi ý 2'] },
    ])
    expect(result[0].danh_sach_goi_y).toEqual(['gợi ý 1', 'gợi ý 2'])
  })

  it('giữ nguyên pham_vi và mo_ta đã có', () => {
    const result = chuanHoaSteps([
      { thu_tu: 2, pham_vi: 'buoc_1', mo_ta: 'Bước 1', bieu_thuc_ket_qua: 'x=2', danh_sach_goi_y: [] },
    ])
    expect(result[0]).toEqual({
      thu_tu: 2,
      pham_vi: 'buoc_1',
      mo_ta: 'Bước 1',
      bieu_thuc_ket_qua: 'x=2',
      danh_sach_goi_y: [],
    })
  })
})
