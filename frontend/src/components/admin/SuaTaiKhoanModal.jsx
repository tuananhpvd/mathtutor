import { useState } from 'react'
import { api } from '../../api'
import { Button, Input, Select } from '../ui'

// Modal sửa tài khoản dùng chung (admin). showRole: cho đổi vai trò; showLop: cho gán lớp.
export default function SuaTaiKhoanModal({ user, lopOptions = [], showRole, showLop, onClose, onSaved }) {
  const [hoTen, setHoTen] = useState(user.ho_ten)
  const [dangNhap, setDangNhap] = useState(user.dang_nhap)
  const [matKhau, setMatKhau] = useState('')
  const [vaiTro, setVaiTro] = useState(user.vai_tro)
  const [lopId, setLopId] = useState(user.lop_id ? String(user.lop_id) : '')
  const [err, setErr] = useState('')
  const [saving, setSaving] = useState(false)

  async function luu() {
    setSaving(true)
    setErr('')
    try {
      const body = { ho_ten: hoTen, dang_nhap: dangNhap }
      if (matKhau) body.mat_khau = matKhau
      if (showRole) body.vai_tro = vaiTro
      await api.adminUpdateUser(user.id, body)
      if (showLop) await api.adminSetUserLop(user.id, lopId ? Number(lopId) : null)
      onSaved()
    } catch (e) {
      setErr(e.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 z-30 bg-black/30 flex items-center justify-center p-4" onClick={onClose}>
      <div className="bg-surface rounded-card w-full max-w-md p-6 shadow-[var(--shadow-pop)]"
        onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-ink">Sửa tài khoản</h3>
          <button onClick={onClose} className="text-muted hover:text-ink text-lg">✕</button>
        </div>
        {err && <p className="text-danger text-sm bg-danger-soft rounded-md px-3 py-2 mb-3">{err}</p>}
        <div className="flex flex-col gap-3">
          <Input label="Họ tên" value={hoTen} onChange={(e) => setHoTen(e.target.value)} />
          <Input label="Tên đăng nhập" value={dangNhap} onChange={(e) => setDangNhap(e.target.value)} />
          <Input label="Mật khẩu mới (để trống nếu giữ nguyên)" type="password"
            value={matKhau} onChange={(e) => setMatKhau(e.target.value)} />
          {showRole && (
            <Select label="Vai trò" value={vaiTro} onChange={(e) => setVaiTro(e.target.value)}
              options={[{ value: 'hs', label: 'Học sinh' }, { value: 'gv', label: 'Giáo viên' }]} />
          )}
          {showLop && (
            <Select label="Lớp" value={lopId} onChange={(e) => setLopId(e.target.value)}
              options={lopOptions} />
          )}
        </div>
        <div className="flex gap-2 mt-5">
          <Button onClick={luu} disabled={saving}>{saving ? 'Đang lưu...' : 'Lưu'}</Button>
          <Button variant="secondary" onClick={onClose}>Hủy</Button>
        </div>
      </div>
    </div>
  )
}
