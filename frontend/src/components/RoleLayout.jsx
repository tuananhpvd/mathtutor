/*
 * RoleLayout — khung bố cục theo vai trò (UIUX mục 5).
 * - HS: topbar mỏng, nội dung trung tâm rộng, ít menu.
 * - GV/Admin: sidebar trái điều hướng + topbar tiêu đề; nội dung thiên bảng/biểu đồ.
 *
 * Props: vai_tro ('hs'|'gv'|'admin'), ho_ten, nav [{key,label,icon?}],
 *        active, onNavigate(key), onLogout, title, children.
 */

import { useEffect, useRef, useState } from 'react'
import ChuongThongBao from './ChuongThongBao'

const ACCENT = {
  hs: { ten: 'Học sinh', mau: 'text-hs', vach: 'border-hs' },
  gv: { ten: 'Giáo viên', mau: 'text-gv', vach: 'border-gv' },
  admin: { ten: 'Quản trị', mau: 'text-admin', vach: 'border-admin' },
}

function Brand({ vai_tro, compact = false }) {
  const a = ACCENT[vai_tro] || ACCENT.hs
  return (
    <div className="flex items-center gap-2">
      <img src="/icon.png" alt="MathTutor"
        className={`${compact ? 'h-9 w-9' : 'h-16 w-16'} rounded-md object-cover shrink-0`} />
      <div className="leading-tight">
        <p className="font-semibold text-ink">MathTutor</p>
        <p className={`text-xs ${a.mau}`}>{a.ten}</p>
      </div>
    </div>
  )
}

function UserMenu({ ho_ten, onLogout }) {
  return (
    <div className="flex items-center gap-2">
      <ChuongThongBao />
      <span className="text-sm text-muted hidden sm:inline">{ho_ten}</span>
      <button
        onClick={onLogout}
        className="text-sm text-primary hover:bg-primary-soft rounded-md px-2.5 py-1 transition-colors"
      >
        Đăng xuất
      </button>
    </div>
  )
}

// Menu tài khoản dạng avatar + dropdown (SaaS hiện đại: gộp "Tài khoản" + "Đăng xuất"
// vào 1 điểm, giải phóng chỗ cho thanh điều hướng chính không cần cuộn ngang).
function ProfileMenu({ ho_ten, dangOTrang, onMoTaiKhoan, onLogout }) {
  const [mo, setMo] = useState(false)
  const ref = useRef(null)

  useEffect(() => {
    if (!mo) return
    function ngoaiClick(e) {
      if (ref.current && !ref.current.contains(e.target)) setMo(false)
    }
    function phimEsc(e) {
      if (e.key === 'Escape') setMo(false)
    }
    document.addEventListener('mousedown', ngoaiClick)
    document.addEventListener('keydown', phimEsc)
    return () => {
      document.removeEventListener('mousedown', ngoaiClick)
      document.removeEventListener('keydown', phimEsc)
    }
  }, [mo])

  const chuCai = (ho_ten || '?').trim().charAt(0).toUpperCase() || '?'

  return (
    <div className="flex items-center gap-1.5" ref={ref}>
      <ChuongThongBao />
      <div className="relative">
        <button
          onClick={() => setMo((m) => !m)}
          className={`flex items-center gap-2 pl-1 pr-2.5 py-1 rounded-full border transition-colors ${
            mo || dangOTrang
              ? 'border-primary/30 bg-primary-soft'
              : 'border-transparent hover:bg-surface-2'
          }`}
        >
          <span className="h-7 w-7 rounded-full bg-primary text-white text-xs font-semibold
            grid place-items-center shrink-0">
            {chuCai}
          </span>
          <span className="text-sm text-ink font-medium hidden sm:inline max-w-32 truncate">
            {ho_ten}
          </span>
          <svg width="14" height="14" viewBox="0 0 20 20" fill="none"
            className={`text-muted transition-transform hidden sm:block ${mo ? 'rotate-180' : ''}`}>
            <path d="M5 7.5L10 12.5L15 7.5" stroke="currentColor" strokeWidth="1.7"
              strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </button>

        {mo && (
          <div className="absolute right-0 mt-2 w-56 bg-surface border border-border
            rounded-lg shadow-[var(--shadow-pop)] py-1.5 z-20">
            <p className="px-3.5 py-2 text-sm font-medium text-ink truncate">{ho_ten}</p>
            <div className="h-px bg-border my-1" />
            {onMoTaiKhoan && (
              <button
                onClick={() => { setMo(false); onMoTaiKhoan() }}
                className={`w-full text-left px-3.5 py-2 text-sm transition-colors ${
                  dangOTrang ? 'text-primary font-medium bg-primary-soft' : 'text-ink hover:bg-surface-2'
                }`}
              >
                Tài khoản cá nhân
              </button>
            )}
            <button
              onClick={() => { setMo(false); onLogout() }}
              className="w-full text-left px-3.5 py-2 text-sm text-danger hover:bg-danger-soft transition-colors"
            >
              Đăng xuất
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

function HSLayout({ ho_ten, nav = [], active, onNavigate, onLogout, children }) {
  // "Tài khoản" dời vào menu avatar (dropdown) — nhường chỗ cho thanh điều hướng chính,
  // tránh phải cuộn ngang khi danh sách mục ngày càng dài.
  const taiKhoan = nav.find((n) => n.key === 'tai_khoan')
  const navChinh = nav.filter((n) => n.key !== 'tai_khoan')

  return (
    <div className="min-h-screen flex flex-col bg-bg">
      <header className="sticky top-0 z-10 bg-surface/90 backdrop-blur border-b border-border">
        <div className="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between gap-3">
          <div className="shrink-0">
            <Brand vai_tro="hs" compact />
          </div>
          <nav className="hidden lg:flex items-center gap-0.5 bg-surface-2/70 rounded-full p-1">
            {navChinh.map((n) => (
              <button
                key={n.key}
                onClick={() => onNavigate?.(n.key)}
                className={`whitespace-nowrap px-3.5 py-1.5 rounded-full text-sm transition-colors ${
                  active === n.key
                    ? 'bg-surface text-primary font-semibold shadow-sm'
                    : 'text-muted hover:text-ink'
                }`}
              >
                {n.label}
              </button>
            ))}
          </nav>
          <div className="shrink-0">
            <ProfileMenu
              ho_ten={ho_ten}
              dangOTrang={taiKhoan && active === taiKhoan.key}
              onMoTaiKhoan={taiKhoan ? () => onNavigate?.(taiKhoan.key) : null}
              onLogout={onLogout}
            />
          </div>
        </div>
      </header>
      <main className="flex-1 max-w-6xl w-full mx-auto px-4 py-6">{children}</main>
    </div>
  )
}

function SidebarLayout({ vai_tro, ho_ten, nav = [], active, onNavigate, onLogout, title, children }) {
  return (
    <div className="min-h-screen flex bg-bg">
      <aside className="w-60 shrink-0 bg-surface border-r border-border flex flex-col">
        <div className="h-14 px-4 flex items-center border-b border-border">
          <Brand vai_tro={vai_tro} />
        </div>
        <nav className="flex-1 p-3 flex flex-col gap-1">
          {nav.map((n) => (
            <button
              key={n.key}
              onClick={() => onNavigate?.(n.key)}
              className={`text-left px-3 py-2 rounded-md text-sm transition-colors ${
                active === n.key
                  ? 'bg-primary-soft text-primary font-medium'
                  : 'text-muted hover:bg-surface-2 hover:text-ink'
              }`}
            >
              {n.label}
            </button>
          ))}
        </nav>
      </aside>
      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-14 bg-surface border-b border-border flex items-center justify-between px-6">
          <h1 className="text-base font-semibold text-ink">{title}</h1>
          <UserMenu ho_ten={ho_ten} onLogout={onLogout} />
        </header>
        <main className="flex-1 p-6 overflow-x-hidden">{children}</main>
      </div>
    </div>
  )
}

export default function RoleLayout({ vai_tro = 'hs', ...props }) {
  if (vai_tro === 'hs') return <HSLayout {...props} />
  return <SidebarLayout vai_tro={vai_tro} {...props} />
}
