import { describe, expect, it } from 'vitest'
import { dinhDangThoiGian, phanTachTg } from './format'

describe('phanTachTg', () => {
  it('trả về null khi không có giá trị hoặc không parse được', () => {
    expect(phanTachTg(null)).toBeNull()
    expect(phanTachTg(undefined)).toBeNull()
    expect(phanTachTg('')).toBeNull()
    expect(phanTachTg('không-phải-ngày')).toBeNull()
  })

  it('tách được giờ và ngày từ ISO timestamp hợp lệ', () => {
    const result = phanTachTg('2026-07-12T08:30:00Z')
    expect(result).toHaveProperty('gio')
    expect(result).toHaveProperty('ngay')
    expect(typeof result.gio).toBe('string')
    expect(typeof result.ngay).toBe('string')
  })
})

describe('dinhDangThoiGian', () => {
  it('trả về — khi không có giá trị', () => {
    expect(dinhDangThoiGian(null)).toBe('—')
    expect(dinhDangThoiGian(undefined)).toBe('—')
  })

  it('định dạng dưới 60 giây', () => {
    expect(dinhDangThoiGian(0)).toBe('0 giây')
    expect(dinhDangThoiGian(45)).toBe('45 giây')
    expect(dinhDangThoiGian(-5)).toBe('0 giây')
  })

  it('định dạng từ 1 phút trở lên, có làm tròn', () => {
    expect(dinhDangThoiGian(60)).toBe('1 phút')
    expect(dinhDangThoiGian(90)).toBe('1 phút 30 giây')
    expect(dinhDangThoiGian(125.6)).toBe('2 phút 6 giây')
  })
})
