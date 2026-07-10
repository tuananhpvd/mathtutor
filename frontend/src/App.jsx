import { useEffect, useState } from 'react'
import Login from './pages/auth/Login'
import HocSinhApp from './pages/hs/HocSinhApp'
import GiaoVienApp from './pages/gv/GiaoVienApp'
import QuanTriApp from './pages/admin/QuanTriApp'
import { getSession } from './auth'
import { ConfirmProvider } from './components/ui'
import { api } from './api'

const KHOA_XEM_TRUOC = 'mt_xem_truoc'

function getPage(vai_tro) {
  if (vai_tro === 'admin') return 'admin'
  if (vai_tro === 'gv') return 'gv'
  if (vai_tro === 'hs') return 'hs'
  return 'login'
}

function TrangBaoTri({ noiDung }) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-white p-8">
      <p className="max-w-3xl text-center text-2xl font-bold text-gray-800 md:text-3xl">
        {noiDung || 'SẢN PHẨM ĐANG HOÀN THIỆN. HÃY QUAY LẠI SAU NGÀY 08/08/2026!'}
      </p>
    </div>
  )
}

export default function App() {
  const session = getSession()
  const [page, setPage] = useState(session ? getPage(session.vai_tro) : 'login')
  const [dangKiemTra, setDangKiemTra] = useState(true)
  const [baoTri, setBaoTri] = useState(false)
  const [noiDungBaoTri, setNoiDungBaoTri] = useState('')

  useEffect(() => {
    if (localStorage.getItem(KHOA_XEM_TRUOC) === '1') {
      setTimeout(() => setDangKiemTra(false), 0)
      return
    }
    const ma = new URLSearchParams(window.location.search).get('ma')
    api
      .trangThaiBaoTri(ma)
      .then((res) => {
        if (res.hop_le) {
          localStorage.setItem(KHOA_XEM_TRUOC, '1')
          const url = new URL(window.location.href)
          url.searchParams.delete('ma')
          window.history.replaceState({}, '', url.toString())
        } else {
          setBaoTri(!!res.bao_tri)
          setNoiDungBaoTri(res.noi_dung || '')
        }
        setDangKiemTra(false)
      })
      .catch(() => setDangKiemTra(false))
  }, [])

  function handleLogin(vai_tro) {
    setPage(getPage(vai_tro))
  }

  function handleLogout() {
    setPage('login')
  }

  if (dangKiemTra) return null
  if (baoTri) return <TrangBaoTri noiDung={noiDungBaoTri} />

  return (
    <ConfirmProvider>
      {page === 'login' && <Login onLogin={handleLogin} />}
      {page === 'hs' && <HocSinhApp onLogout={handleLogout} />}
      {page === 'gv' && <GiaoVienApp onLogout={handleLogout} />}
      {page === 'admin' && <QuanTriApp onLogout={handleLogout} />}
    </ConfirmProvider>
  )
}
