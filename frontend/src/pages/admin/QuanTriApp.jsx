import { useEffect, useState } from 'react'
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

const NAV_KEYS = NAV.map((n) => n.key)
const DEFAULT_PAGE = 'dashboard'

function pageFromHash() {
  const h = window.location.hash.slice(1)
  return NAV_KEYS.includes(h) ? h : DEFAULT_PAGE
}

export default function QuanTriApp({ onLogout }) {
  const { ho_ten } = getSession() || {}
  const [page, setPage] = useState(pageFromHash)

  function navigate(key) {
    window.location.hash = key
    setPage(key)
  }

  useEffect(() => {
    function onHashChange() {
      setPage(pageFromHash())
    }
    window.addEventListener('hashchange', onHashChange)
    return () => window.removeEventListener('hashchange', onHashChange)
  }, [])

  return (
    <RoleLayout
      vai_tro="admin"
      ho_ten={ho_ten}
      nav={NAV}
      active={page}
      onNavigate={navigate}
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
