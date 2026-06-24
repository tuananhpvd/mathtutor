import { useState } from 'react'
import { api } from '../../api'
import { saveSession } from '../../auth'
import { Button, Card, Input } from '../../components/ui'

export default function Login({ onLogin }) {
  const [form, setForm] = useState({ dang_nhap: '', mat_khau: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const res = await api.login(form.dang_nhap, form.mat_khau)
      saveSession(res.access_token, res.vai_tro, res.ho_ten)
      onLogin(res.vai_tro)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-bg px-4">
      <div className="w-full max-w-sm">
        <div className="flex flex-col items-center mb-6">
          <div className="h-12 w-12 rounded-lg bg-primary text-white grid place-items-center text-xl font-bold">
            M
          </div>
          <h1 className="text-2xl font-semibold text-ink mt-3">MathTutor</h1>
          <p className="text-muted text-sm">Gia sư Toán lớp 12 — học theo phương pháp gợi mở</p>
        </div>

        <Card className="p-6">
          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <Input
              id="dang_nhap"
              label="Tên đăng nhập"
              value={form.dang_nhap}
              onChange={(e) => setForm((f) => ({ ...f, dang_nhap: e.target.value }))}
              placeholder="admin / gv1 / hs1"
              required
              autoFocus
            />
            <Input
              id="mat_khau"
              label="Mật khẩu"
              type="password"
              value={form.mat_khau}
              onChange={(e) => setForm((f) => ({ ...f, mat_khau: e.target.value }))}
              required
            />
            {error && (
              <p className="text-sm text-danger bg-danger-soft rounded-md px-3 py-2">{error}</p>
            )}
            <Button type="submit" disabled={loading} className="w-full">
              {loading ? 'Đang đăng nhập...' : 'Đăng nhập'}
            </Button>
          </form>
        </Card>
        <p className="text-center text-xs text-muted mt-4">
          Tài khoản demo — đổi mật khẩu trước khi dùng thật.
        </p>
      </div>
    </div>
  )
}
