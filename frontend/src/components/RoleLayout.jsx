/*
 * RoleLayout — khung bố cục theo vai trò (UIUX mục 5).
 * - HS: topbar mỏng, nội dung trung tâm rộng, ít menu.
 * - GV/Admin: sidebar trái điều hướng + topbar tiêu đề; nội dung thiên bảng/biểu đồ.
 *
 * Props: vai_tro ('hs'|'gv'|'admin'), ho_ten, nav [{key,label,icon?}],
 *        active, onNavigate(key), onLogout, title, children.
 */

const ACCENT = {
  hs: { ten: 'Học sinh', mau: 'text-hs', vach: 'border-hs' },
  gv: { ten: 'Giáo viên', mau: 'text-gv', vach: 'border-gv' },
  admin: { ten: 'Quản trị', mau: 'text-admin', vach: 'border-admin' },
}

function Brand({ vai_tro }) {
  const a = ACCENT[vai_tro] || ACCENT.hs
  return (
    <div className="flex items-center gap-2">
      <div className="h-8 w-8 rounded-md bg-primary text-white grid place-items-center font-bold">
        M
      </div>
      <div className="leading-tight">
        <p className="font-semibold text-ink">MathTutor</p>
        <p className={`text-xs ${a.mau}`}>{a.ten}</p>
      </div>
    </div>
  )
}

function UserMenu({ ho_ten, onLogout }) {
  return (
    <div className="flex items-center gap-3">
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

function HSLayout({ ho_ten, nav = [], active, onNavigate, onLogout, children }) {
  return (
    <div className="min-h-screen flex flex-col bg-bg">
      <header className="sticky top-0 z-10 bg-surface/90 backdrop-blur border-b border-border">
        <div className="max-w-5xl mx-auto px-4 h-14 flex items-center justify-between">
          <Brand vai_tro="hs" />
          <nav className="hidden md:flex items-center gap-1">
            {nav.map((n) => (
              <button
                key={n.key}
                onClick={() => onNavigate?.(n.key)}
                className={`px-3 py-1.5 rounded-md text-sm transition-colors ${
                  active === n.key
                    ? 'bg-primary-soft text-primary font-medium'
                    : 'text-muted hover:text-ink'
                }`}
              >
                {n.label}
              </button>
            ))}
          </nav>
          <UserMenu ho_ten={ho_ten} onLogout={onLogout} />
        </div>
      </header>
      <main className="flex-1 max-w-5xl w-full mx-auto px-4 py-6">{children}</main>
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
