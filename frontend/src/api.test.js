import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { api } from './api'
import { dangKyPhienHetHan } from './auth'

function jsonResponse(body, status = 200) {
  return { ok: status >= 200 && status < 300, status, json: async () => body }
}

describe('api request()', () => {
  beforeEach(() => {
    sessionStorage.clear()
    globalThis.fetch = vi.fn()
    // auth.js giữ handler ở biến module-level (sống chung cả tiến trình vitest) — phải xóa
    // trước mỗi test để test này không đăng ký "leak" sang test khác chạy sau nó.
    dangKyPhienHetHan(null)
  })

  afterEach(() => {
    vi.restoreAllMocks()
    vi.useRealTimers()
  })

  it('gắn Authorization header khi có token', async () => {
    sessionStorage.setItem('token', 'abc123')
    globalThis.fetch.mockResolvedValue(jsonResponse({ ok: true }))
    await api.health()
    const [, opts] = globalThis.fetch.mock.calls[0]
    expect(opts.headers.Authorization).toBe('Bearer abc123')
  })

  it('không gắn Authorization header khi không có token', async () => {
    globalThis.fetch.mockResolvedValue(jsonResponse({ ok: true }))
    await api.health()
    const [, opts] = globalThis.fetch.mock.calls[0]
    expect(opts.headers.Authorization).toBeUndefined()
  })

  it('trả về dữ liệu JSON khi request thành công', async () => {
    globalThis.fetch.mockResolvedValue(jsonResponse({ hello: 'world' }))
    const data = await api.health()
    expect(data).toEqual({ hello: 'world' })
  })

  it('ném lỗi kèm message từ server khi response lỗi', async () => {
    globalThis.fetch.mockResolvedValue(jsonResponse({ detail: 'Không hợp lệ' }, 400))
    await expect(api.health()).rejects.toThrow('Không hợp lệ')
  })

  it('ném lỗi mặc định theo mã HTTP khi server không trả detail', async () => {
    globalThis.fetch.mockResolvedValue(jsonResponse({}, 500))
    await expect(api.health()).rejects.toThrow('Lỗi 500')
  })

  it('ném lỗi "không kết nối được" khi fetch reject vì lỗi mạng', async () => {
    globalThis.fetch.mockRejectedValue(new TypeError('Failed to fetch'))
    await expect(api.health()).rejects.toThrow('Không kết nối được máy chủ')
  })

  it('ném lỗi "phản hồi quá lâu" khi hết timeout', async () => {
    vi.useFakeTimers()
    globalThis.fetch.mockImplementation(
      (_url, opts) =>
        new Promise((_resolve, reject) => {
          opts.signal.addEventListener('abort', () => {
            const err = new Error('aborted')
            err.name = 'AbortError'
            reject(err)
          })
        })
    )
    const promise = api.health()
    const assertion = expect(promise).rejects.toThrow('Máy chủ phản hồi quá lâu')
    await vi.advanceTimersByTimeAsync(30000)
    await assertion
  })

  it('xóa session và gọi handler phiên hết hạn (chuyển mềm về đăng nhập) khi status 401', async () => {
    sessionStorage.setItem('token', 'abc123')
    sessionStorage.setItem('vai_tro', 'hs')
    sessionStorage.setItem('ho_ten', 'Nguyễn Văn A')
    sessionStorage.setItem('la_quan_ly', '1')
    const handler = vi.fn()
    dangKyPhienHetHan(handler)
    // jsdom không cho redefine window.location.reload trực tiếp — thay cả object location.
    const originalLocation = window.location
    const reload = vi.fn()
    Object.defineProperty(window, 'location', {
      configurable: true,
      value: { ...originalLocation, reload },
    })
    globalThis.fetch.mockResolvedValue(jsonResponse({}, 401))

    try {
      await expect(api.health()).rejects.toThrow('Phiên đăng nhập hết hạn')

      expect(sessionStorage.getItem('token')).toBeNull()
      expect(sessionStorage.getItem('vai_tro')).toBeNull()
      expect(sessionStorage.getItem('ho_ten')).toBeNull()
      expect(sessionStorage.getItem('la_quan_ly')).toBeNull()
      expect(handler).toHaveBeenCalled()
      // Có handler đăng ký rồi thì KHÔNG reload cứng cả trang — tránh mất dữ liệu HS/GV
      // đang nhập dở ở những phần khác của trang chưa kịp lưu.
      expect(reload).not.toHaveBeenCalled()
    } finally {
      Object.defineProperty(window, 'location', { configurable: true, value: originalLocation })
    }
  })

  it('lưới an toàn: reload cứng nếu 401 xảy ra mà CHƯA có handler đăng ký', async () => {
    const originalLocation = window.location
    const reload = vi.fn()
    Object.defineProperty(window, 'location', {
      configurable: true,
      value: { ...originalLocation, reload },
    })
    globalThis.fetch.mockResolvedValue(jsonResponse({}, 401))

    try {
      await expect(api.health()).rejects.toThrow('Phiên đăng nhập hết hạn')
      expect(reload).toHaveBeenCalled()
    } finally {
      Object.defineProperty(window, 'location', { configurable: true, value: originalLocation })
    }
  })
})
