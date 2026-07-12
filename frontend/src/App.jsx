import { lazy, Suspense, useEffect, useState } from 'react'
import Login from './pages/auth/Login'
import { dangKyPhienHetHan, getSession } from './auth'
import { ConfirmProvider } from './components/ui'
import { api } from './api'

// Tách riêng theo vai trò (code-splitting) — HS không tải code của GV/Admin và ngược lại,
// giảm đáng kể dung lượng tải lần đầu (mỗi vai trò chỉ tải đúng phần mình dùng).
const HocSinhApp = lazy(() => import('./pages/hs/HocSinhApp'))
const GiaoVienApp = lazy(() => import('./pages/gv/GiaoVienApp'))
const QuanTriApp = lazy(() => import('./pages/admin/QuanTriApp'))

const KHOA_XEM_TRUOC = 'mt_xem_truoc'

function DangTaiToanTrang() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-bg">
      <p className="text-muted text-sm">Đang tải...</p>
    </div>
  )
}

function getPage(vai_tro) {
  if (vai_tro === 'admin') return 'admin'
  if (vai_tro === 'gv') return 'gv'
  if (vai_tro === 'hs') return 'hs'
  return 'login'
}

function TrangBaoTri({ noiDung }) {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-white p-8">
      <img src="/logomt.png" alt="MathTutor" className="h-40 w-40 rounded-lg object-cover" />
      <p className="max-w-3xl whitespace-pre-wrap text-center text-2xl font-bold text-gray-800 md:text-3xl mt-6">
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

  useEffect(() => {
    dangKyPhienHetHan(() => setPage('login'))
  }, [])

  if (dangKiemTra) return null
  if (baoTri) return <TrangBaoTri noiDung={noiDungBaoTri} />

  return (
    <ConfirmProvider>
      {page === 'login' && <Login onLogin={handleLogin} />}
      <Suspense fallback={<DangTaiToanTrang />}>
        {page === 'hs' && <HocSinhApp onLogout={handleLogout} />}
        {page === 'gv' && <GiaoVienApp onLogout={handleLogout} />}
        {page === 'admin' && <QuanTriApp onLogout={handleLogout} />}
      </Suspense>
    </ConfirmProvider>
  )
}
