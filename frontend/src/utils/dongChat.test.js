import { describe, expect, it } from 'vitest'
import { dungDongChat, nhanPhanCach } from './dongChat'

const opts = { loaiCau: 'TLN', tongBuoc: 3, moTaCacBuoc: { 1: 'Tính y′', 2: 'Giải y′ = 0' } }

describe('dungDongChat', () => {
  it('chỉ 1 phân cách ở đầu khi mọi lượt cùng một bước — không lặp lại vì không đổi bước', () => {
    const ra = dungDongChat([
      { vai_tro: 'gia_su', noi_dung: 'a', buoc: 1 },
      { vai_tro: 'hoc_sinh', noi_dung: 'b', buoc: 1 },
    ], opts)
    expect(ra.map((r) => r.kieu)).toEqual(['phan_cach', 'turn', 'turn'])
  })

  it('CÓ chèn phân cách cho bước ĐẦU TIÊN — nhất quán với mọi bước sau, kể cả khi không có ngữ cảnh "đang ở bước mấy" nào khác cạnh khung chat (vd XemLaiBai)', () => {
    const ra = dungDongChat([{ vai_tro: 'gia_su', noi_dung: 'chào em', buoc: 1 }], opts)
    expect(ra.map((r) => r.kieu)).toEqual(['phan_cach', 'turn'])
    expect(ra[0].nhan).toBe('Bước 1/3')
    expect(ra[0].moTa).toBe('Tính y′')
  })

  it('chèn phân cách ở CẢ bước đầu lẫn khi bước chuyển', () => {
    const ra = dungDongChat([
      { vai_tro: 'gia_su', noi_dung: 'gợi ý bước 1', buoc: 1 },
      { vai_tro: 'hoc_sinh', noi_dung: 'em trả lời', buoc: 1 },
      { vai_tro: 'gia_su', noi_dung: 'đúng rồi, sang bước 2', buoc: 2 },
    ], opts)
    expect(ra.map((r) => r.kieu)).toEqual(['phan_cach', 'turn', 'turn', 'phan_cach', 'turn'])
    expect(ra[0].nhan).toBe('Bước 1/3')
    expect(ra[3].nhan).toBe('Bước 2/3')
    expect(ra[3].moTa).toBe('Giải y′ = 0')
  })

  it('bỏ qua lượt cũ không có buoc (lịch sử trước khi có cột) - không đoán bừa', () => {
    const ra = dungDongChat([
      { vai_tro: 'gia_su', noi_dung: 'lượt cũ', buoc: null },
      { vai_tro: 'hoc_sinh', noi_dung: 'lượt cũ 2' },
    ], opts)
    expect(ra.map((r) => r.kieu)).toEqual(['turn', 'turn'])
  })

  it('KHÔNG vẽ phân cách lùi bước (vd lượt GV trả lời gắn bước cũ) — mốc đầu vẫn có, chỉ lượt lùi sau đó không thêm mốc mới', () => {
    const ra = dungDongChat([
      { vai_tro: 'gia_su', noi_dung: 'bước 2', buoc: 2 },
      { vai_tro: 'giao_vien', noi_dung: 'thầy trả lời', buoc: 1 },
    ], opts)
    const mocs = ra.filter((r) => r.kieu === 'phan_cach')
    expect(mocs).toHaveLength(1)
    expect(mocs[0].nhan).toBe('Bước 2/3')
  })

  // Dữ liệu THẬT của TNDS: mọi bước đều thu_tu = 1, chỉ khác pham_vi (a/b/c/d) — nên "buoc"
  // KHÔNG đổi khi sang ý mới. Bản test đầu tiên bịa buoc 1→2 nên PASS giả, che mất lỗi thật.
  it('TNDS: phân cách theo Ý dù buoc KHÔNG đổi (thu_tu luôn = 1), kể cả mốc Ý đầu tiên', () => {
    const ra = dungDongChat([
      { vai_tro: 'gia_su', noi_dung: 'ý a', buoc: 1, y: 'a' },
      { vai_tro: 'hoc_sinh', noi_dung: 'em chọn Đúng', buoc: 1, y: 'a' },
      { vai_tro: 'gia_su', noi_dung: 'sang ý b', buoc: 1, y: 'b' },
    ], { loaiCau: 'TNDS', tongBuoc: 4, moTaCacBuoc: { a: 'Xét a', b: 'Xét b' } })
    expect(ra.map((r) => r.kieu)).toEqual(['phan_cach', 'turn', 'turn', 'phan_cach', 'turn'])
    expect(ra[0].nhan).toBe('Ý a)')
    expect(ra[0].moTa).toBe('Xét a')
    expect(ra[3].nhan).toBe('Ý b)')
    expect(ra[3].moTa).toBe('Xét b')
  })

  it('TNDS: đi hết a→b→c→d thì có đúng 4 mốc (gồm cả mốc Ý a ban đầu)', () => {
    const turns = ['a', 'b', 'c', 'd'].map((y) => ({ vai_tro: 'gia_su', noi_dung: y, buoc: 1, y }))
    const ra = dungDongChat(turns, { loaiCau: 'TNDS', tongBuoc: 4, moTaCacBuoc: {} })
    expect(ra.filter((r) => r.kieu === 'phan_cach')).toHaveLength(4)
  })

  it('TNDS: chỉ 1 mốc Ý a ban đầu, KHÔNG vẽ thêm khi vẫn ở cùng 1 ý (pha suy luận → pha chốt Đúng/Sai)', () => {
    const ra = dungDongChat([
      { vai_tro: 'gia_su', noi_dung: 'gợi ý ý a', buoc: 1, y: 'a' },
      { vai_tro: 'hoc_sinh', noi_dung: 'biểu thức', buoc: 1, y: 'a' },
      { vai_tro: 'gia_su', noi_dung: 'giờ chốt Đúng/Sai', buoc: 1, y: 'a' },
    ], { loaiCau: 'TNDS', tongBuoc: 4, moTaCacBuoc: { a: 'Xét a' } })
    const mocs = ra.filter((r) => r.kieu === 'phan_cach')
    expect(mocs).toHaveLength(1)
    expect(mocs[0].nhan).toBe('Ý a)')
  })
})

describe('nhanPhanCach', () => {
  it('mô tả rỗng → chỉ còn nhãn bước, không trả chuỗi rác', () => {
    const r = nhanPhanCach({ buoc: 2, loaiCau: 'TLN', tongBuoc: 3, moTaCacBuoc: {} })
    expect(r.nhan).toBe('Bước 2/3')
    expect(r.moTa).toBe('')
  })

  it('mô tả chỉ có khoảng trắng cũng coi như rỗng', () => {
    const r = nhanPhanCach({ buoc: 2, loaiCau: 'TLN', tongBuoc: 3, moTaCacBuoc: { 2: '   ' } })
    expect(r.moTa).toBe('')
  })

  it('không biết tổng số bước thì bỏ phần "/n"', () => {
    expect(nhanPhanCach({ buoc: 2, loaiCau: 'TLN', tongBuoc: null }).nhan).toBe('Bước 2')
  })
})
