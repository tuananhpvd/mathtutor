import { useState } from 'react'
import { api } from '../../api'
import { Button, Input, Select } from '../ui'

// Modal GV sửa học sinh (phạm vi lớp mình). showLop: cho gán lại lớp (trong các lớp của GV).
export default function SuaHocSinhModal({ hs, lopOptions = [], showLop, onClose, onSaved }) {
  const [hoTen, setHoTen] = useState(hs.ho_ten)
  const [dangNhap, setDangNhap] = useState(hs.dang_nhap)
  const [matKhau, setMatKhau] = useState('')
  const [lopId, setLopId] = useState(hs.lop_id ? String(hs.lop_id) : '')
  const [err, setErr] = useState('')
  const [saving, setSaving] = useState(false)

  async function luu() {
    setSaving(true)
    setErr('')
    try {
      await api.gvSuaHocSinh(hs.id, { ho_ten: hoTen, dang_nhap: dangNhap, ...(matKhau ? { mat_khau: matKhau } : {}) })
      if (showLop && lopId && Number(lopId) !== hs.lop_id) {
        await api.gvGanLopHocSinh(hs.id, Number(lopId))
      }
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
          <h3 className="font-semibold text-ink">Sửa học sinh</h3>
          <button onClick={onClose} className="text-muted hover:text-ink text-lg">✕</button>
        </div>
        {err && <p className="text-danger text-sm bg-danger-soft rounded-md px-3 py-2 mb-3">{err}</p>}
        <div className="flex flex-col gap-3">
          <Input label="Họ tên" value={hoTen} onChange={(e) => setHoTen(e.target.value)} />
          <Input label="Tên đăng nhập" value={dangNhap} onChange={(e) => setDangNhap(e.target.value)} />
          <Input label="Mật khẩu mới (để trống nếu giữ nguyên)" type="password"
            value={matKhau} onChange={(e) => setMatKhau(e.target.value)} />
          {showLop && (
            <Select label="Lớp" value={lopId} onChange={(e) => setLopId(e.target.value)} options={lopOptions} />
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
