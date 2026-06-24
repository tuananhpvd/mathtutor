import { useState } from 'react'
import Login from './pages/auth/Login'
import HocSinhApp from './pages/hs/HocSinhApp'
import GiaoVienApp from './pages/gv/GiaoVienApp'
import QuanTriApp from './pages/admin/QuanTriApp'
import { getSession } from './auth'

function getPage(vai_tro) {
  if (vai_tro === 'admin') return 'admin'
  if (vai_tro === 'gv') return 'gv'
  if (vai_tro === 'hs') return 'hs'
  return 'login'
}

export default function App() {
  const session = getSession()
  const [page, setPage] = useState(session ? getPage(session.vai_tro) : 'login')

  function handleLogin(vai_tro) {
    setPage(getPage(vai_tro))
  }

  function handleLogout() {
    setPage('login')
  }

  if (page === 'login') return <Login onLogin={handleLogin} />
  if (page === 'hs') return <HocSinhApp onLogout={handleLogout} />
  if (page === 'gv') return <GiaoVienApp onLogout={handleLogout} />
  if (page === 'admin') return <QuanTriApp onLogout={handleLogout} />
}
