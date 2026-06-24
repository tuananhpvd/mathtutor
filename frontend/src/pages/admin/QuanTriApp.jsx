import { useState } from 'react'
import RoleLayout from '../../components/RoleLayout'
import { getSession, clearSession } from '../../auth'
import Dashboard from './Dashboard'
import QuanLyTaiKhoan from './QuanLyTaiKhoan'
import CauHinh from './CauHinh'
import NhatKy from './NhatKy'

const NAV = [
  { key: 'dashboard', label: 'Dashboard' },
  { key: 'tai_khoan', label: 'Quản lý tài khoản' },
  { key: 'cau_hinh', label: 'Cấu hình' },
  { key: 'nhat_ky', label: 'Nhật ký' },
]

const TIEU_DE = {
  dashboard: 'Bảng điều khiển hệ thống',
  tai_khoan: 'Quản lý tài khoản',
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
      {page === 'cau_hinh' && <CauHinh />}
      {page === 'nhat_ky' && <NhatKy />}
    </RoleLayout>
  )
}
