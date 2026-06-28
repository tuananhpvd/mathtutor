import { useEffect, useState } from 'react'
import RoleLayout from '../../components/RoleLayout'
import { getSession, clearSession } from '../../auth'
import TrangChu from './TrangChu'
import ChonBai from './ChonBai'
import PhongHoc from './PhongHoc'
import TienDo from './TienDo'
import TaiKhoanCaNhan from './TaiKhoanCaNhan'

const NAV = [
  { key: 'trang_chu', label: 'Trang chủ' },
  { key: 'chon_bai', label: 'Chọn bài' },
  { key: 'tien_do', label: 'Tiến độ' },
  { key: 'tai_khoan', label: 'Tài khoản' },
]

const NAV_KEYS = NAV.map((n) => n.key)
const DEFAULT_PAGE = 'trang_chu'

function pageFromHash() {
  const h = window.location.hash.slice(1)
  return NAV_KEYS.includes(h) ? h : DEFAULT_PAGE
}

export default function HocSinhApp({ onLogout }) {
  const { ho_ten } = getSession() || {}
  const [page, setPage] = useState(pageFromHash)
  const [phongHoc, setPhongHoc] = useState(null) // {problemId} | {sessionId}
  const [locBai, setLocBai] = useState(null) // bộ lọc ban đầu cho ChonBai

  function moBaiMoi(problemId) {
    setPhongHoc({ problemId })
    setPage('phong_hoc') // không cập nhật hash — phòng học là trang tạm thời
  }
  function lamTiep(sessionId) {
    setPhongHoc({ sessionId })
    setPage('phong_hoc')
  }
  function luyenDang(r) {
    setLocBai({ chuyen_de: r.chuyen_de, dang_id: r.dang_id })
    window.location.hash = 'chon_bai'
    setPage('chon_bai')
  }
  function dieuHuong(key) {
    setLocBai(null)
    window.location.hash = key
    setPage(key)
  }

  useEffect(() => {
    function onHashChange() {
      const newPage = pageFromHash()
      setLocBai(null)
      setPage(newPage)
    }
    window.addEventListener('hashchange', onHashChange)
    return () => window.removeEventListener('hashchange', onHashChange)
  }, [])

  return (
    <RoleLayout
      vai_tro="hs"
      ho_ten={ho_ten}
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
      {page === 'tien_do' && <TienDo onLuyenDang={luyenDang} />}
      {page === 'tai_khoan' && <TaiKhoanCaNhan />}
    </RoleLayout>
  )
}
