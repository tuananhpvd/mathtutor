import { useState } from 'react'
import { Check, Eye, EyeOff, Loader2 } from 'lucide-react'
import { api } from '../../api'
import { saveSession } from '../../auth'
import { Button, Input } from '../../components/ui'
import ThuongHieu from '../../components/ThuongHieu'

const DIEM_MANH = [
  'Dẫn dắt tự tìm đáp án, không đưa lời giải sẵn',
  'Chấm chính xác từng bước làm',
  'Bám sát nội dung chương trình',
]

// Panel thương hiệu bên trái (chỉ hiện từ lg trở lên — điện thoại dùng header gọn phía trên form).
function PanelThuongHieu() {
  return (
    <div className="relative hidden lg:flex flex-col justify-center overflow-hidden
      bg-gradient-to-br from-primary to-primary-hover px-8 py-12 text-white">
      {/* Hoạ tiết toán mờ trang trí — thuần chữ, không ảnh, không thư viện */}
      <div aria-hidden className="pointer-events-none absolute inset-0 select-none opacity-[0.07]
        font-serif text-[8rem] leading-none">
        <span className="absolute left-6 top-6">∫</span>
        <span className="absolute right-8 top-28">∑</span>
        <span className="absolute bottom-16 left-10">√</span>
        <span className="absolute bottom-6 right-14">π</span>
      </div>

      <div className="relative flex flex-col gap-6">
        <ThuongHieu size="lg" onDark />
        <h1 className="text-2xl font-bold leading-tight">Gia sư Toán 12</h1>
        <ul className="mt-1 flex flex-col gap-3">
          {DIEM_MANH.map((d) => (
            <li key={d} className="flex items-start gap-3">
              <span className="mt-0.5 grid h-6 w-6 shrink-0 place-items-center rounded-full bg-white/15">
                <Check size={15} strokeWidth={3} />
              </span>
              <span className="text-white/90">{d}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}

export default function Login({ onLogin }) {
  const [form, setForm] = useState({ dang_nhap: '', mat_khau: '' })
  const [hienMk, setHienMk] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const res = await api.login(form.dang_nhap, form.mat_khau)
      saveSession(res.access_token, res.vai_tro, res.ho_ten, res.la_quan_ly)
      onLogin(res.vai_tro)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-bg p-4 sm:p-6">
      <div className="grid grid-cols-1 w-full max-w-5xl overflow-hidden rounded-2xl bg-surface
        shadow-[var(--shadow-pop)] lg:grid-cols-2">
        <PanelThuongHieu />

        {/* Cột form */}
        <div className="flex flex-col justify-center px-6 py-10 sm:px-10">
          <div className="mx-auto w-full max-w-sm">
            {/* Header thương hiệu gọn — chỉ hiện trên điện thoại (panel trái bị ẩn) */}
            <div className="mb-8 flex justify-center lg:hidden">
              <ThuongHieu size="md" onDark={false} />
            </div>

            <div className="mb-6">
              <h2 className="text-2xl font-bold text-ink">Đăng nhập</h2>
              <p className="mt-1 text-sm text-muted">Nhập tài khoản được cấp để tiếp tục.</p>
            </div>

            <form onSubmit={handleSubmit} className="flex flex-col gap-4">
              <Input
                id="dang_nhap"
                label="Tên đăng nhập"
                value={form.dang_nhap}
                onChange={(e) => setForm((f) => ({ ...f, dang_nhap: e.target.value }))}
                autoComplete="username"
                required
                autoFocus
              />

              {/* Ô mật khẩu + nút hiện/ẩn — dựng inline (không đụng primitive Input dùng chung
                  toàn app) để tránh rủi ro hồi quy ở các màn khác. */}
              <div>
                <label htmlFor="mat_khau" className="mb-1 block text-sm font-medium text-ink">
                  Mật khẩu
                </label>
                <div className="relative">
                  <input
                    id="mat_khau"
                    type={hienMk ? 'text' : 'password'}
                    value={form.mat_khau}
                    onChange={(e) => setForm((f) => ({ ...f, mat_khau: e.target.value }))}
                    autoComplete="current-password"
                    required
                    className="w-full rounded-lg border border-border bg-surface px-3.5 py-2.5 pr-11 text-sm
                      text-ink placeholder:text-muted transition-colors focus:border-primary
                      focus:outline-none focus:ring-2 focus:ring-primary/40"
                  />
                  <button
                    type="button"
                    onClick={() => setHienMk((v) => !v)}
                    aria-label={hienMk ? 'Ẩn mật khẩu' : 'Hiện mật khẩu'}
                    className="absolute right-2 top-1/2 grid h-7 w-7 -translate-y-1/2 place-items-center
                      rounded-md text-muted transition-colors hover:bg-surface-2 hover:text-ink"
                  >
                    {hienMk ? <EyeOff size={18} /> : <Eye size={18} />}
                  </button>
                </div>
              </div>

              {error && (
                <p className="rounded-md bg-danger-soft px-3 py-2 text-sm text-danger">{error}</p>
              )}

              <Button type="submit" disabled={loading} className="w-full">
                {loading ? (
                  <>
                    <Loader2 size={18} className="animate-spin" />
                    Đang đăng nhập...
                  </>
                ) : (
                  'Đăng nhập'
                )}
              </Button>

              <p className="text-center text-xs text-muted">
                Quên mật khẩu? Liên hệ giáo viên hoặc quản trị viên.
              </p>
            </form>
          </div>
        </div>
      </div>
    </div>
  )
}
