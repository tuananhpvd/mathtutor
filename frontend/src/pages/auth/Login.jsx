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
      saveSession(res.access_token, res.vai_tro, res.ho_ten, res.la_quan_ly)
      onLogin(res.vai_tro)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-start justify-center bg-bg px-4 pt-12">
      <div className="w-full max-w-sm">
        <div className="flex flex-col items-center mb-6">
          <img src="/logomt.png" alt="MathTutor" className="h-72 w-72 rounded-lg object-cover" />
          <p className="text-primary text-[20px] font-bold mt-3">HỌC THEO PHƯƠNG PHÁP GỢI MỞ</p>
        </div>

        <Card className="p-6">
          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <Input
              id="dang_nhap"
              label="Tên đăng nhập"
              value={form.dang_nhap}
              onChange={(e) => setForm((f) => ({ ...f, dang_nhap: e.target.value }))}
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
      </div>
    </div>
  )
}
