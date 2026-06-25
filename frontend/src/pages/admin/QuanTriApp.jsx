import { useState } from 'react'
import RoleLayout from '../../components/RoleLayout'
import { getSession, clearSession } from '../../auth'
import Dashboard from './Dashboard'
import QuanLyTaiKhoan from './QuanLyTaiKhoan'
import QuanLyLop from './QuanLyLop'
import QuanLyGiaoVien from './QuanLyGiaoVien'
import QuanLyHocSinh from './QuanLyHocSinh'
import CauHinh from './CauHinh'
import NhatKy from './NhatKy'

const NAV = [
  { key: 'dashboard', label: 'Dashboard' },
  { key: 'tai_khoan', label: 'Quản lý tài khoản' },
  { key: 'lop', label: 'Quản lý lớp' },
  { key: 'giao_vien', label: 'Quản lý giáo viên' },
  { key: 'hoc_sinh', label: 'Quản lý học sinh' },
  { key: 'cau_hinh', label: 'Cấu hình' },
  { key: 'nhat_ky', label: 'Nhật ký' },
]

const TIEU_DE = {
  dashboard: 'Bảng điều khiển hệ thống',
  tai_khoan: 'Quản lý tài khoản',
  lop: 'Quản lý theo lớp',
  giao_vien: 'Quản lý theo giáo viên',
  hoc_sinh: 'Quản lý theo học sinh',
  cau_hinh: 'Cấu hình hệ thống',
  nhat_ky: 'Nhật ký hoạt động',
}

export default function QuanTriApp({ onLogout }) {
  const { ho_ten } = getSession() || {}
  const [page, setPage] = useState('dashboard')

  return (
    <RoleLayout
      vai_tro="admin"
      ho_ten={ho_ten}
      nav={NAV}
      active={page}
      onNavigate={setPage}
      onLogout={() => {
        clearSession()
        onLogout()
      }}
      title={TIEU_DE[page]}
    >
      {page === 'dashboard' && <Dashboard />}
      {page === 'tai_khoan' && <QuanLyTaiKhoan />}
      {page === 'lop' && <QuanLyLop />}
      {page === 'giao_vien' && <QuanLyGiaoVien />}
      {page === 'hoc_sinh' && <QuanLyHocSinh />}
      {page === 'cau_hinh' && <CauHinh />}
      {page === 'nhat_ky' && <NhatKy />}
    </RoleLayout>
  )
}
