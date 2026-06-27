import { useState } from 'react'
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

export default function HocSinhApp({ onLogout }) {
  const { ho_ten } = getSession() || {}
  const [page, setPage] = useState('trang_chu')
  const [phongHoc, setPhongHoc] = useState(null) // {problemId} | {sessionId}
  const [locBai, setLocBai] = useState(null) // bộ lọc ban đầu cho ChonBai

  function moBaiMoi(problemId) {
    setPhongHoc({ problemId })
    setPage('phong_hoc')
  }
  function lamTiep(sessionId) {
    setPhongHoc({ sessionId })
    setPage('phong_hoc')
  }
  function luyenDang(r) {
    // r: {chuyen_de, dang_id, ten} từ phân tích năng lực
    setLocBai({ chuyen_de: r.chuyen_de, dang_id: r.dang_id })
    setPage('chon_bai')
  }
  function dieuHuong(key) {
    setLocBai(null) // chọn menu thường → bỏ bộ lọc ép
    setPage(key)
  }

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
          onTrangChu={() => setPage('trang_chu')}
          onChonBai={() => setPage('chon_bai')}
        />
      )}
      {page === 'tien_do' && <TienDo onLuyenDang={luyenDang} />}
      {page === 'tai_khoan' && <TaiKhoanCaNhan />}
    </RoleLayout>
  )
}
