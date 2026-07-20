import { useState } from 'react'
import { ArrowLeft, Eye, EyeOff, Loader2, School } from 'lucide-react'
import { api } from '../../api'
import { saveSession } from '../../auth'
import { Button, Input } from '../../components/ui'
import ThuongHieu from '../../components/ThuongHieu'

/**
 * HS tự đăng ký bằng MÃ LỚP — 2 bước.
 *
 * Bước 1 nhập mã rồi HIỆN TÊN LỚP + TÊN GV để em xác nhận trước khi tạo tài khoản. Đây không
 * phải bước thừa: mã gõ nhầm 1 ký tự vẫn có thể trúng lớp khác, mà vào nhầm lớp thì thầy cô
 * phải xử lý thủ công. Bước 2 mới nhập thông tin cá nhân.
 */
export default function DangKy({ onXong, onQuayLai }) {
  const [buoc, setBuoc] = useState(1)
  const [ma, setMa] = useState('')
  const [lop, setLop] = useState(null)          // {lop_ten, gv_ten}
  const [form, setForm] = useState({ ho_ten: '', dang_nhap: '', mat_khau: '' })
  const [hienMk, setHienMk] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function kiemTraMa(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const d = await api.lopTuMa(ma)
      setLop(d)
      setBuoc(2)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  async function taoTaiKhoan(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const res = await api.dangKyBangMa({ ma, ...form })
      saveSession(res.access_token, res.vai_tro, res.ho_ten, res.la_quan_ly)
      onXong(res.vai_tro)   // vào thẳng phòng học, không bắt đăng nhập lại
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-bg p-4 sm:p-6">
      <div className="w-full max-w-md rounded-2xl bg-surface px-6 py-8 shadow-[var(--shadow-pop)] sm:px-8">
        <div className="mb-6 flex justify-center">
          <ThuongHieu size="md" onDark={false} />
        </div>

        <div className="mb-6">
          <h2 className="text-2xl font-bold text-ink">Tạo tài khoản học sinh</h2>
          <p className="mt-1 text-sm text-muted">
            {buoc === 1
              ? 'Nhập mã lớp thầy/cô đã cho để vào đúng lớp của em.'
              : 'Bước cuối — đặt tài khoản để đăng nhập những lần sau.'}
          </p>
        </div>

        {buoc === 1 ? (
          <form onSubmit={kiemTraMa} className="flex flex-col gap-4">
            <Input
              id="ma"
              label="Mã lớp"
              value={ma}
              onChange={(e) => setMa(e.target.value)}
              placeholder="VD: A7K3-QM9X"
              autoComplete="off"
              required
              autoFocus
              className="uppercase tracking-widest"
            />
            <p className="-mt-2 text-xs text-muted">
              Gõ hoa hay thường, có gạch hay không đều được.
            </p>

            {error && (
              <p className="rounded-md bg-danger-soft px-3 py-2 text-sm text-danger">{error}</p>
            )}

            <Button type="submit" disabled={loading || !ma.trim()} className="w-full">
              {loading ? (<><Loader2 size={18} className="animate-spin" />Đang kiểm tra...</>) : 'Tiếp tục'}
            </Button>

            <button type="button" onClick={onQuayLai}
              className="mx-auto flex items-center gap-1.5 text-sm text-primary hover:underline">
              <ArrowLeft size={15} /> Quay lại đăng nhập
            </button>
          </form>
        ) : (
          <form onSubmit={taoTaiKhoan} className="flex flex-col gap-4">
            {/* Xác nhận đúng lớp trước khi tạo tài khoản */}
            <div className="flex items-start gap-3 rounded-lg border border-success/30 bg-success-soft px-3 py-2.5">
              <School size={18} className="mt-0.5 shrink-0 text-success" />
              <div className="text-sm">
                <p className="font-semibold text-ink">Lớp {lop?.lop_ten}</p>
                {lop?.gv_ten && <p className="text-muted">Giáo viên: {lop.gv_ten}</p>}
              </div>
            </div>

            <Input id="ho_ten" label="Họ và tên" value={form.ho_ten} required autoFocus
              onChange={(e) => setForm((f) => ({ ...f, ho_ten: e.target.value }))} />

            <Input id="dang_nhap" label="Tên đăng nhập" value={form.dang_nhap} required
              autoComplete="username" placeholder="không dấu, không khoảng trắng"
              onChange={(e) => setForm((f) => ({ ...f, dang_nhap: e.target.value }))} />

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
                  autoComplete="new-password"
                  minLength={6}
                  required
                  className="w-full rounded-lg border border-border bg-surface px-3.5 py-2.5 pr-11 text-sm
                    text-ink placeholder:text-muted transition-colors focus:border-primary
                    focus:outline-none focus:ring-2 focus:ring-primary/40"
                />
                <button type="button" onClick={() => setHienMk((v) => !v)}
                  aria-label={hienMk ? 'Ẩn mật khẩu' : 'Hiện mật khẩu'}
                  className="absolute right-2 top-1/2 grid h-7 w-7 -translate-y-1/2 place-items-center
                    rounded-md text-muted transition-colors hover:bg-surface-2 hover:text-ink">
                  {hienMk ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
              <p className="mt-1 text-xs text-muted">Tối thiểu 6 ký tự. Em nhớ kỹ mật khẩu này nhé.</p>
            </div>

            {error && (
              <p className="rounded-md bg-danger-soft px-3 py-2 text-sm text-danger">{error}</p>
            )}

            <Button type="submit" disabled={loading} className="w-full">
              {loading ? (<><Loader2 size={18} className="animate-spin" />Đang tạo tài khoản...</>)
                : 'Tạo tài khoản & vào học'}
            </Button>

            <button type="button" onClick={() => { setBuoc(1); setError('') }}
              className="mx-auto flex items-center gap-1.5 text-sm text-primary hover:underline">
              <ArrowLeft size={15} /> Nhập lại mã lớp
            </button>
          </form>
        )}
      </div>
    </div>
  )
}
