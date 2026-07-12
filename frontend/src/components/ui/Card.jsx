export default function Card({ className = '', children, ...props }) {
  return (
    <div
      className={`bg-surface rounded-card border border-border shadow-[var(--shadow-card)]
        ${className}`}
      {...props}
    >
      {children}
    </div>
  )
}

export function CardHeader({ title, subtitle, action }) {
  return (
    <div className="flex items-start justify-between gap-3 px-5 pt-5 pb-3">
      <div className="min-w-0">
        <h3 className="text-base font-semibold text-ink">{title}</h3>
        {subtitle && <p className="text-sm text-muted mt-0.5">{subtitle}</p>}
      </div>
      {action}
    </div>
  )
}

export function CardBody({ className = '', children }) {
  return <div className={`px-5 pb-5 ${className}`}>{children}</div>
}

const STAT_TEXT = { primary: 'text-primary', success: 'text-success', warning: 'text-warning', danger: 'text-danger', accent: 'text-accent' }
const STAT_BG = { primary: 'bg-primary-soft', success: 'bg-success-soft', warning: 'bg-warning-soft', danger: 'bg-danger-soft', accent: 'bg-accent-soft' }

// icon (tùy chọn): component icon (vd từ lucide-react) — đặt trong khối màu theo accent,
// mang màu sắc thay cho chữ số (số liệu luôn giữ màu chữ trung tính, đúng quy ước "màu theo
// icon/nhãn, không theo chữ số" dùng nhất quán trong toàn app).
export function StatCard({ label, value, hint, accent = 'primary', icon: Icon }) {
  return (
    <Card className="px-5 py-4">
      <div className="flex items-center gap-3">
        {Icon && (
          <div className={`h-11 w-11 rounded-lg grid place-items-center shrink-0
            ${STAT_TEXT[accent]} ${STAT_BG[accent]}`}>
            <Icon size={22} strokeWidth={2} />
          </div>
        )}
        <div className="min-w-0">
          <p className="text-3xl font-bold text-ink leading-tight">{value}</p>
          <p className="text-sm text-muted truncate mt-0.5">{label}</p>
        </div>
      </div>
      {hint && <p className="text-xs text-muted mt-1">{hint}</p>}
    </Card>
  )
}
