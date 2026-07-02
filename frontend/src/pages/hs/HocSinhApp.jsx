import { useEffect, useState } from 'react'
import RoleLayout from '../../components/RoleLayout'
import { getSession, clearSession, updateHoTen } from '../../auth'
import TrangChu from './TrangChu'
import ChonBai from './ChonBai'
import PhongHoc from './PhongHoc'
import TienDo from './TienDo'
import NhiemVu from './NhiemVu'
import MucTieu from './MucTieu'
import TaiKhoanCaNhan from './TaiKhoanCaNhan'

const NAV = [
  { key: 'trang_chu', label: 'Trang chủ' },
  { key: 'nhiem_vu', label: 'Nhiệm vụ' },
  { key: 'muc_tieu', label: 'Mục tiêu' },
  { key: 'chon_bai', label: 'Chọn bài' },
  { key: 'tien_do', label: 'Tiến độ' },
  { key: 'tai_khoan', label: 'Tài khoản' },
]

const NAV_KEYS = NAV.map((n) => n.key)
const DEFAULT_PAGE = 'trang_chu'
const PHONG_HOC_KEY = 'hs_phong_hoc'

function pageFromHash() {
  const h = window.location.hash.slice(1)
  if (h === 'phong_hoc') return 'phong_hoc'
  return NAV_KEYS.includes(h) ? h : DEFAULT_PAGE
}

export default function HocSinhApp({ onLogout }) {
  const [hoTen, setHoTen] = useState(() => (getSession() || {}).ho_ten || '')
  const [page, setPage] = useState(pageFromHash)

  function capNhatHoTen(ten) {
    updateHoTen(ten)
    setHoTen(ten)
  }
  const [phongHoc, setPhongHoc] = useState(() => {
    // Khôi phục state phòng học khi F5 với hash #phong_hoc
    if (window.location.hash.slice(1) === 'phong_hoc') {
      try { return JSON.parse(sessionStorage.getItem(PHONG_HOC_KEY)) } catch { return null }
    }
    return null
  })
  const [locBai, setLocBai] = useState(null) // bộ lọc ban đầu cho ChonBai

  function moBaiMoi(problemId) {
    const state = { problemId }
    sessionStorage.setItem(PHONG_HOC_KEY, JSON.stringify(state))
    setPhongHoc(state)
    window.location.hash = 'phong_hoc'
    setPage('phong_hoc')
  }
  function lamTiep(sessionId) {
    const state = { sessionId }
    sessionStorage.setItem(PHONG_HOC_KEY, JSON.stringify(state))
    setPhongHoc(state)
    window.location.hash = 'phong_hoc'
    setPage('phong_hoc')
  }
  function luyenDang(r) {
    setLocBai({ chuyen_de: r.chuyen_de, dang_id: r.dang_id })
    window.location.hash = 'chon_bai'
    setPage('chon_bai')
  }
  function dieuHuong(key) {
    setLocBai(null)
    if (key !== 'phong_hoc') sessionStorage.removeItem(PHONG_HOC_KEY)
    window.location.hash = key
    setPage(key)
  }

  useEffect(() => {
    function onHashChange() {
      const newPage = pageFromHash()
      setLocBai(null)
      if (newPage !== 'phong_hoc') {
        sessionStorage.removeItem(PHONG_HOC_KEY)
        setPhongHoc(null)
      }
      setPage(newPage)
    }
    window.addEventListener('hashchange', onHashChange)
    return () => window.removeEventListener('hashchange', onHashChange)
  }, [])

  return (
    <RoleLayout
      vai_tro="hs"
      ho_ten={hoTen}
      nav={NAV}
      active={page === 'phong_hoc' ? 'chon_bai' : page}
      onNavigate={dieuHuong}
      onLogout={() => {
        clearSession()
        onLogout()
      }}
    >
      {page === 'trang_chu' && (
        <TrangChu onChonBai={() => dieuHuong('chon_bai')} onLamTiep={lamTiep} />
      )}
      {page === 'chon_bai' && (
        <ChonBai onChon={moBaiMoi} onLamTiep={lamTiep} locBanDau={locBai} />
      )}
      {page === 'phong_hoc' && phongHoc && (
        <PhongHoc
          problemId={phongHoc.problemId}
          sessionId={phongHoc.sessionId}
          onTrangChu={() => dieuHuong('trang_chu')}
          onChonBai={() => dieuHuong('chon_bai')}
        />
      )}
      {page === 'nhiem_vu' && <NhiemVu onChon={moBaiMoi} />}
      {page === 'muc_tieu' && <MucTieu />}
      {page === 'tien_do' && <TienDo onLuyenDang={luyenDang} />}
      {page === 'tai_khoan' && <TaiKhoanCaNhan onHoTenChange={capNhatHoTen} />}
    </RoleLayout>
  )
}
