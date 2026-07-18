import { useEffect, useState } from 'react'
import { api } from '../../api'
import { Badge, Button, Card, CardBody, CardHeader, Input } from '../../components/ui'

export default function TaiKhoanCaNhan({ onHoTenChange }) {
  const [hs, setHs] = useState(null)
  const [hoTen, setHoTen] = useState('')
  const [matKhau, setMatKhau] = useState('')
  const [msg, setMsg] = useState('')
  const [err, setErr] = useState('')

  function tai() {
    api.hsHoSo().then((d) => { setHs(d); setHoTen(d.ho_ten) }).catch(() => {})
  }
  useEffect(tai, [])

  async function luu(e) {
    e.preventDefault()
    setMsg(''); setErr('')
    try {
      await api.hsCapNhatHoSo({ ho_ten: hoTen, ...(matKhau ? { mat_khau: matKhau } : {}) })
      setMsg('Đã lưu thay đổi.')
      setMatKhau('')
      tai()
      onHoTenChange?.(hoTen.trim())
    } catch (e2) { setErr(e2.message) }
  }

  if (!hs) return <p className="text-sm text-muted">Đang tải...</p>

  return (
    <div className="max-w-lg">
      <Card>
        <CardHeader title="Tài khoản của em" subtitle="Xem và cập nhật thông tin cá nhân" />
        <CardBody>
          <form onSubmit={luu} className="flex flex-col gap-3">
            <div className="flex flex-wrap items-center gap-3 text-sm">
              <span className="text-muted">Tên đăng nhập:</span>
              <b className="text-ink">{hs.dang_nhap}</b>
              <span className="text-muted">Lớp:</span>
              <b className="text-ink">{hs.lop_ten || 'Chưa có lớp'}</b>
              <Badge tone={hs.trang_thai === 'hoat_dong' ? 'success' : 'danger'}>
                {hs.trang_thai === 'hoat_dong' ? 'Hoạt động' : 'Đã khóa'}
              </Badge>
            </div>
            <Input label="Họ và tên" value={hoTen} onChange={(e) => setHoTen(e.target.value)} required />
            <Input label="Mật khẩu mới (để trống nếu giữ nguyên, tối thiểu 6 ký tự)" type="password"
              value={matKhau} onChange={(e) => setMatKhau(e.target.value)} minLength={6} />
            <div className="flex items-center gap-3">
              <Button type="submit">Lưu thay đổi</Button>
              {msg && <span className="text-sm text-success">{msg}</span>}
              {err && <span className="text-sm text-danger">{err}</span>}
            </div>
          </form>
        </CardBody>
      </Card>
    </div>
  )
}
