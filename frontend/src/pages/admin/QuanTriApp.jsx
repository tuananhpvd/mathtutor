import { lazy, Suspense, useEffect, useState } from 'react'
import RoleLayout from '../../components/RoleLayout'
import { getSession, clearSession, updateHoTen } from '../../auth'

// Mỗi trang tách riêng 1 chunk (code-splitting) — chỉ tải khi Admin thật sự mở trang đó.
const Dashboard = lazy(() => import('./Dashboard'))
const QuanLyTaiKhoan = lazy(() => import('./QuanLyTaiKhoan'))
const QuanLyLop = lazy(() => import('./QuanLyLop'))
const QuanLyGiaoVien = lazy(() => import('./QuanLyGiaoVien'))
const QuanLyHocSinh = lazy(() => import('./QuanLyHocSinh'))
const CauHinh = lazy(() => import('./CauHinh'))
const NhatKy = lazy(() => import('./NhatKy'))
const TaiKhoanCaNhan = lazy(() => import('./TaiKhoanCaNhan'))

const NAV = [
  { key: 'dashboard', label: 'Dashboard' },
  { key: 'tai_khoan', label: 'Quản lý tài khoản' },
  { key: 'lop', label: 'Quản lý lớp' },
  { key: 'giao_vien', label: 'Quản lý giáo viên' },
  { key: 'hoc_sinh', label: 'Quản lý học sinh' },
  { key: 'cau_hinh', label: 'Cấu hình' },
  { key: 'nhat_ky', label: 'Nhật ký' },
  { key: 'tai_khoan_ca_nhan', label: 'Tài khoản cá nhân' },
]

const TIEU_DE = {
  dashboard: 'Bảng điều khiển hệ thống',
  tai_khoan: 'Quản lý tài khoản',
  lop: 'Quản lý theo lớp',
  giao_vien: 'Quản lý theo giáo viên',
  hoc_sinh: 'Quản lý theo học sinh',
  cau_hinh: 'Cấu hình hệ thống',
  nhat_ky: 'Nhật ký hoạt động',
  tai_khoan_ca_nhan: 'Tài khoản cá nhân',
}

const NAV_KEYS = NAV.map((n) => n.key)
const DEFAULT_PAGE = 'dashboard'

function pageFromHash() {
  const h = window.location.hash.slice(1)
  return NAV_KEYS.includes(h) ? h : DEFAULT_PAGE
}

export default function QuanTriApp({ onLogout }) {
  const sess = getSession() || {}
  const [hoTen, setHoTen] = useState(sess.ho_ten || '')
  const [page, setPage] = useState(pageFromHash)

  function navigate(key) {
    window.location.hash = key
    setPage(key)
  }

  function capNhatHoTen(ten) {
    updateHoTen(ten)
    setHoTen(ten)
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
      ho_ten={hoTen}
      nav={NAV}
      active={page}
      onNavigate={navigate}
      onLogout={() => {
        clearSession()
        onLogout()
      }}
      title={TIEU_DE[page]}
    >
      <Suspense fallback={<p className="text-muted text-sm">Đang tải...</p>}>
        {page === 'dashboard' && <Dashboard />}
        {page === 'tai_khoan' && <QuanLyTaiKhoan />}
        {page === 'lop' && <QuanLyLop />}
        {page === 'giao_vien' && <QuanLyGiaoVien />}
        {page === 'hoc_sinh' && <QuanLyHocSinh />}
        {page === 'cau_hinh' && <CauHinh />}
        {page === 'nhat_ky' && <NhatKy />}
        {page === 'tai_khoan_ca_nhan' && <TaiKhoanCaNhan onHoTenChange={capNhatHoTen} />}
      </Suspense>
    </RoleLayout>
  )
}
