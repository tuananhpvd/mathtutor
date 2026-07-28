import { describe, expect, it } from 'vitest'
import { baiNenLuyenTiep } from './goiYTiepTheo'

describe('baiNenLuyenTiep', () => {
  it('trả null khi pt là null (chưa tải xong / lỗi)', () => {
    expect(baiNenLuyenTiep(null)).toBeNull()
  })

  it('trả null khi diem_yeu rỗng (HS mới, chưa đủ dữ liệu)', () => {
    expect(baiNenLuyenTiep({ diem_yeu: [] })).toBeNull()
  })

  it('trả null khi dòng đầu tiên không có dang_id (không điều hướng được)', () => {
    const pt = { diem_yeu: [{ ten: 'Tìm cực trị', chuyen_de: 'Đạo hàm', dang_id: null, diem_thanh_thao: 40 }] }
    expect(baiNenLuyenTiep(pt)).toBeNull()
  })

  it('trả về dòng diem_yeu đầu tiên khi đủ dữ liệu', () => {
    const pt = {
      diem_yeu: [
        { ten: 'Tìm cực trị', chuyen_de: 'Đạo hàm', dang_id: 2, diem_thanh_thao: 52 },
        { ten: 'Tích phân', chuyen_de: 'Nguyên hàm', dang_id: 5, diem_thanh_thao: 60 },
      ],
    }
    expect(baiNenLuyenTiep(pt)).toEqual(pt.diem_yeu[0])
  })
})
