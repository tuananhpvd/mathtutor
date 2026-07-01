import { useEffect, useState } from 'react'
import RoleLayout from '../../components/RoleLayout'
import { getSession, clearSession } from '../../auth'
import TongQuan from './TongQuan'
import QuanLyCauHoi from './QuanLyCauHoi'
import QuanLyDanhMuc from './QuanLyDanhMuc'
import AISinhCauHoi from './AISinhCauHoi'
import QuanLyCo from './QuanLyCo'
import TheoDoiTienBo from './TheoDoiTienBo'
import TaiKhoanCaNhan from './TaiKhoanCaNhan'
import QuanLyLopGV from './QuanLyLopGV'
import QuanLyHocSinhGV from './QuanLyHocSinhGV'
import HoTroHocSinh from './HoTroHocSinh'
import GiaoNhiemVu from './GiaoNhiemVu'

const NAV = [
  { key: 'tong_quan', label: 'Tổng quan' },
  { key: 'danh_muc', label: 'Danh mục' },
  { key: 'cau_hoi', label: 'Câu hỏi' },
  { key: 'ai_sinh', label: 'AI sinh câu hỏi' },
  { key: 'co', label: 'Cờ theo dõi' },
  { key: 'ho_tro', label: 'Hỗ trợ học sinh' },
  { key: 'nhiem_vu', label: 'Giao nhiệm vụ' },
  { key: 'tien_bo', label: 'Tiến bộ học sinh' },
  { key: 'lop', label: 'Quản lý lớp' },
  { key: 'hoc_sinh', label: 'Quản lý học sinh' },
  { key: 'tai_khoan', label: 'Tài khoản cá nhân' },
]

const TIEU_DE = {
  tong_quan: 'Tổng quan',
  danh_muc: 'Quản lý danh mục chuyên đề / dạng',
  cau_hoi: 'Quản lý câu hỏi',
  ai_sinh: 'AI sinh câu hỏi',
  co: 'Cờ theo dõi',
  ho_tro: 'Hỗ trợ học sinh (Nhờ thầy/cô)',
  nhiem_vu: 'Giao bài / nhiệm vụ',
  tien_bo: 'Theo dõi tiến bộ học sinh',
  lop: 'Quản lý lớp',
  hoc_sinh: 'Quản lý học sinh',
  tai_khoan: 'Tài khoản cá nhân',
}

const NAV_KEYS = NAV.map((n) => n.key)
const DEFAULT_PAGE = 'tong_quan'

function pageFromHash() {
  const h = window.location.hash.slice(1)
  return NAV_KEYS.includes(h) ? h : DEFAULT_PAGE
}

export default function GiaoVienApp({ onLogout }) {
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
      vai_tro="gv"
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
      {page === 'tong_quan' && <TongQuan onNavigate={navigate} />}
      {page === 'danh_muc' && <QuanLyDanhMuc />}
      {page === 'cau_hoi' && <QuanLyCauHoi />}
      {page === 'ai_sinh' && <AISinhCauHoi />}
      {page === 'co' && <QuanLyCo />}
      {page === 'ho_tro' && <HoTroHocSinh />}
      {page === 'nhiem_vu' && <GiaoNhiemVu />}
      {page === 'tien_bo' && <TheoDoiTienBo />}
      {page === 'lop' && <QuanLyLopGV />}
      {page === 'hoc_sinh' && <QuanLyHocSinhGV />}
      {page === 'tai_khoan' && <TaiKhoanCaNhan />}
    </RoleLayout>
  )
}
