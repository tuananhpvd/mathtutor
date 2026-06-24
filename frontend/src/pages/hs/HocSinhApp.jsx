import { useState } from 'react'
import RoleLayout from '../../components/RoleLayout'
import { getSession, clearSession } from '../../auth'
import TrangChu from './TrangChu'
import ChonBai from './ChonBai'
import PhongHoc from './PhongHoc'
import TienDo from './TienDo'

const NAV = [
  { key: 'trang_chu', label: 'Trang chủ' },
  { key: 'chon_bai', label: 'Chọn bài' },
  { key: 'tien_do', label: 'Tiến độ' },
]

export default function HocSinhApp({ onLogout }) {
  const { ho_ten } = getSession() || {}
  const [page, setPage] = useState('trang_chu')
  const [phongHoc, setPhongHoc] = useState(null) // {problemId} | {sessionId}

  function moBaiMoi(problemId) {
    setPhongHoc({ problemId })
    setPage('phong_hoc')
  }
  function lamTiep(sessionId) {
    setPhongHoc({ sessionId })
    setPage('phong_hoc')
  }

  return (
    <RoleLayout
      vai_tro="hs"
      ho_ten={ho_ten}
      nav={NAV}
      active={page === 'phong_hoc' ? 'chon_bai' : page}
      onNavigate={setPage}
      onLogout={() => {
        clearSession()
        onLogout()
      }}
    >
      {page === 'trang_chu' && (
        <TrangChu onChonBai={() => setPage('chon_bai')} onLamTiep={lamTiep} />
      )}
      {page === 'chon_bai' && <ChonBai onChon={moBaiMoi} />}
      {page === 'phong_hoc' && phongHoc && (
        <PhongHoc
          problemId={phongHoc.problemId}
          sessionId={phongHoc.sessionId}
          onTrangChu={() => setPage('trang_chu')}
          onChonBai={() => setPage('chon_bai')}
        />
      )}
      {page === 'tien_do' && <TienDo />}
    </RoleLayout>
  )
}
