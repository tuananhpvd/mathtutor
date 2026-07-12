/*
 * RoleLayout — khung bố cục theo vai trò (UIUX mục 5), responsive cho mọi cỡ màn hình.
 * - HS: topbar mỏng; menu chính là thanh pill trên desktop (≥lg), thanh tab cố định đáy
 *   màn hình trên điện thoại/tablet (<lg) — luôn thấy đủ mục, bấm 1 chạm.
 * - GV/Admin: sidebar đầy đủ chữ trên desktop (≥lg), thu gọn còn icon trên tablet
 *   (md–lg), ẩn hẳn + mở bằng nút hamburger (drawer trượt) trên điện thoại (<md).
 *
 * Props: vai_tro ('hs'|'gv'|'admin'), ho_ten, nav [{key,label}],
 *        active, onNavigate(key), onLogout, title, children.
 */

import { useEffect, useRef, useState } from 'react'
import {
  BookOpen, Building2, ClipboardList, FileText, Flag, FolderKanban, GraduationCap,
  Home, LayoutDashboard, Layers, LifeBuoy, ListChecks, Menu, ScrollText, Settings,
  Sparkles, Target, TrendingUp, User, Users, X,
} from 'lucide-react'
import ChuongThongBao from './ChuongThongBao'

const ACCENT = {
  hs: { ten: 'Học sinh', mau: 'text-hs', vach: 'border-hs' },
  gv: { ten: 'Giáo viên', mau: 'text-gv', vach: 'border-gv' },
  admin: { ten: 'Quản trị', mau: 'text-admin', vach: 'border-admin' },
}

// Icon theo key mục menu — thuần trình bày, không ảnh hưởng nav/logic điều hướng.
// Cùng 1 key có thể lặp ở nhiều vai trò (vd "tai_khoan", "nhiem_vu") — dùng chung icon
// hợp lý cho cả hai là đủ, không cần tách theo vai trò.
const ICON_MAP = {
  trang_chu: Home,
  nhiem_vu: ClipboardList,
  muc_tieu: Target,
  chon_bai: BookOpen,
  thi_thu: FileText,
  tien_do: TrendingUp,
  tien_bo: TrendingUp,
  tai_khoan: User,
  tong_quan: LayoutDashboard,
  dashboard: LayoutDashboard,
  danh_muc: Layers,
  cau_hoi: ListChecks,
  ai_sinh: Sparkles,
  co: Flag,
  ho_tro: LifeBuoy,
  de_thi: FileText,
  lop: Building2,
  hoc_sinh: Users,
  giao_vien: GraduationCap,
  cau_hinh: Settings,
  nhat_ky: ScrollText,
  noi_dung_gv: FolderKanban,
}

function IconCuaMuc({ nav_key, ...props }) {
  const Icon = ICON_MAP[nav_key] || Home
  return <Icon {...props} />
}

function Brand({ vai_tro, compact = false, textClass = '' }) {
  const a = ACCENT[vai_tro] || ACCENT.hs
  return (
    <div className="flex items-center gap-2 min-w-0">
      <img src="/icon.png" alt="MathTutor"
        className={`${compact ? 'h-9 w-9' : 'h-16 w-16'} rounded-md object-cover shrink-0`} />
      <div className={`leading-tight min-w-0 ${textClass}`}>
        <p className="font-semibold text-ink truncate">MathTutor</p>
        <p className={`text-xs truncate ${a.mau}`}>{a.ten}</p>
      </div>
    </div>
  )
}

function UserMenu({ ho_ten, onLogout, onMoLienKet }) {
  return (
    <div className="flex items-center gap-2">
      <ChuongThongBao onMoLienKet={onMoLienKet} />
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
function ProfileMenu({ ho_ten, dangOTrang, onMoTaiKhoan, onLogout, onMoLienKet }) {
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
      <ChuongThongBao onMoLienKet={onMoLienKet} />
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

// Thanh tab cố định đáy màn hình — thay thế menu chính của HS dưới lg (điện thoại/tablet
// đứng). Luôn thấy đủ mục, bấm 1 chạm, không cần mở/đóng gì thêm.
function BottomTabBar({ nav, active, onNavigate }) {
  return (
    <nav className="lg:hidden fixed bottom-0 left-0 right-0 z-20 bg-surface border-t
      border-border pb-[env(safe-area-inset-bottom)]">
      <div className="flex items-stretch">
        {nav.map((n) => {
          const dangChon = active === n.key
          return (
            <button
              key={n.key}
              onClick={() => onNavigate?.(n.key)}
              className={`flex-1 min-w-0 flex flex-col items-center justify-center gap-0.5
                px-1 py-2 text-[10.5px] leading-tight transition-colors ${
                dangChon ? 'text-primary' : 'text-muted'
              }`}
            >
              <IconCuaMuc nav_key={n.key} size={20} strokeWidth={dangChon ? 2.3 : 2} />
              <span className="truncate max-w-full font-medium">{n.label}</span>
            </button>
          )
        })}
      </div>
    </nav>
  )
}

function HSLayout({ ho_ten, nav = [], active, onNavigate, onLogout, onMoLienKet, children }) {
  // "Tài khoản" dời vào menu avatar (dropdown) — nhường chỗ cho thanh điều hướng chính,
  // tránh phải cuộn ngang khi danh sách mục ngày càng dài.
  const taiKhoan = nav.find((n) => n.key === 'tai_khoan')
  const navChinh = nav.filter((n) => n.key !== 'tai_khoan')

  return (
    <div className="min-h-screen flex flex-col bg-bg">
      <header className="sticky top-0 z-10 bg-surface/90 backdrop-blur border-b border-border">
        <div className="max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-8 h-14 flex items-center justify-between gap-3">
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
              onMoLienKet={onMoLienKet}
            />
          </div>
        </div>
      </header>
      <main className="flex-1 max-w-[1400px] w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 pb-24 lg:pb-6">
        {children}
      </main>
      <BottomTabBar nav={navChinh} active={active} onNavigate={onNavigate} />
    </div>
  )
}

// modo="sidebar": cột thường trực — icon-only ở md (tablet), icon+chữ ở lg+ (desktop),
//   thuần CSS responsive (cùng 1 DOM, không phụ thuộc JS đo breakpoint).
// modo="drawer": trong drawer trượt mobile — luôn hiện đủ chữ (drawer chỉ hiện <md).
function SidebarNavList({ nav, active, onChon, modo }) {
  const laSidebar = modo === 'sidebar'
  return (
    <nav className="flex-1 p-2 lg:p-3 flex flex-col gap-1 overflow-y-auto">
      {nav.map((n) => (
        <button
          key={n.key}
          onClick={() => onChon(n.key)}
          title={n.label}
          className={`flex items-center gap-3 px-2.5 lg:px-3 py-2.5 rounded-md text-sm
            transition-colors ${laSidebar ? 'justify-center lg:justify-start' : ''} ${
            active === n.key
              ? 'bg-primary-soft text-primary font-medium'
              : 'text-muted hover:bg-surface-2 hover:text-ink'
          }`}
        >
          <IconCuaMuc nav_key={n.key} size={19} strokeWidth={2} className="shrink-0" />
          <span className={laSidebar ? 'hidden lg:inline truncate' : 'truncate'}>{n.label}</span>
        </button>
      ))}
    </nav>
  )
}

function SidebarLayout({ vai_tro, ho_ten, nav = [], active, onNavigate, onLogout, title, onMoLienKet, children }) {
  const [drawerMo, setDrawerMo] = useState(false)

  // Khóa cuộn nền khi drawer mobile đang mở, tránh cuộn "xuyên" ra nội dung phía sau.
  useEffect(() => {
    if (!drawerMo) return
    const truoc = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => { document.body.style.overflow = truoc }
  }, [drawerMo])

  function chonMucDrawer(key) {
    onNavigate?.(key)
    setDrawerMo(false)
  }

  return (
    <div className="min-h-screen flex bg-bg">
      {/* Sidebar: ẩn hẳn dưới md (thay bằng drawer), thu gọn còn icon ở md–lg, đầy đủ ở lg+ */}
      <aside className="hidden md:flex md:w-16 lg:w-60 shrink-0 bg-surface border-r
        border-border flex-col transition-[width]">
        <div className="h-14 px-2 lg:px-4 flex items-center justify-center lg:justify-start border-b border-border">
          <Brand vai_tro={vai_tro} compact textClass="hidden lg:block" />
        </div>
        <SidebarNavList nav={nav} active={active} onChon={onNavigate} modo="sidebar" />
      </aside>

      {/* Drawer trượt cho điện thoại (<md) */}
      {drawerMo && (
        <div className="fixed inset-0 z-40 md:hidden">
          <button
            className="absolute inset-0 bg-black/40"
            aria-label="Đóng menu"
            onClick={() => setDrawerMo(false)}
          />
          <aside className="absolute left-0 top-0 bottom-0 w-72 max-w-[82vw] bg-surface
            border-r border-border flex flex-col shadow-[var(--shadow-pop)]">
            <div className="h-14 px-4 flex items-center justify-between border-b border-border">
              <Brand vai_tro={vai_tro} compact />
              <button
                onClick={() => setDrawerMo(false)}
                className="p-1.5 rounded-md hover:bg-surface-2 text-muted"
                aria-label="Đóng menu"
              >
                <X size={20} />
              </button>
            </div>
            <SidebarNavList nav={nav} active={active} onChon={chonMucDrawer} modo="drawer" />
          </aside>
        </div>
      )}

      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-14 bg-surface border-b border-border flex items-center
          justify-between gap-3 px-4 lg:px-6">
          <div className="flex items-center gap-2 min-w-0">
            <button
              onClick={() => setDrawerMo(true)}
              className="md:hidden p-1.5 -ml-1 rounded-md hover:bg-surface-2 text-ink shrink-0"
              aria-label="Mở menu"
            >
              <Menu size={22} />
            </button>
            <h1 className="text-base font-semibold text-ink truncate">{title}</h1>
          </div>
          <UserMenu ho_ten={ho_ten} onLogout={onLogout} onMoLienKet={onMoLienKet} />
        </header>
        <main className="flex-1 p-4 sm:p-6 overflow-x-hidden">{children}</main>
      </div>
    </div>
  )
}

export default function RoleLayout({ vai_tro = 'hs', ...props }) {
  if (vai_tro === 'hs') return <HSLayout {...props} />
  return <SidebarLayout vai_tro={vai_tro} {...props} />
}
