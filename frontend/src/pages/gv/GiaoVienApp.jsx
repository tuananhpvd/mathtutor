import { useState } from 'react'
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

const NAV = [
  { key: 'tong_quan', label: 'Tổng quan' },
  { key: 'danh_muc', label: 'Danh mục' },
  { key: 'cau_hoi', label: 'Câu hỏi' },
  { key: 'ai_sinh', label: 'AI sinh câu hỏi' },
  { key: 'co', label: 'Cờ theo dõi' },
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
  tien_bo: 'Theo dõi tiến bộ học sinh',
  lop: 'Quản lý lớp',
  hoc_sinh: 'Quản lý học sinh',
  tai_khoan: 'Tài khoản cá nhân',
}

export default function GiaoVienApp({ onLogout }) {
  const { ho_ten } = getSession() || {}
  const [page, setPage] = useState('tong_quan')

  return (
    <RoleLayout
      vai_tro="gv"
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
      {page === 'tong_quan' && <TongQuan onNavigate={setPage} />}
      {page === 'danh_muc' && <QuanLyDanhMuc />}
      {page === 'cau_hoi' && <QuanLyCauHoi />}
      {page === 'ai_sinh' && <AISinhCauHoi />}
      {page === 'co' && <QuanLyCo />}
      {page === 'tien_bo' && <TheoDoiTienBo />}
      {page === 'lop' && <QuanLyLopGV />}
      {page === 'hoc_sinh' && <QuanLyHocSinhGV />}
      {page === 'tai_khoan' && <TaiKhoanCaNhan />}
    </RoleLayout>
  )
}
