import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { api } from './api'

function jsonResponse(body, status = 200) {
  return { ok: status >= 200 && status < 300, status, json: async () => body }
}

describe('api request()', () => {
  beforeEach(() => {
    sessionStorage.clear()
    globalThis.fetch = vi.fn()
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

  it('xóa session và báo hết phiên khi status 401', async () => {
    sessionStorage.setItem('token', 'abc123')
    sessionStorage.setItem('vai_tro', 'hs')
    sessionStorage.setItem('ho_ten', 'Nguyễn Văn A')
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
      expect(reload).toHaveBeenCalled()
    } finally {
      Object.defineProperty(window, 'location', { configurable: true, value: originalLocation })
    }
  })
})
