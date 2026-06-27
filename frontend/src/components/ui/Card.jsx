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
    <div className="flex items-start justify-between px-5 pt-5 pb-3">
      <div>
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

export function StatCard({ label, value, hint, accent = 'primary' }) {
  const accentColor = {
    primary: 'text-primary',
    success: 'text-success',
    warning: 'text-warning',
    danger: 'text-danger',
  }[accent]
  return (
    <Card className="px-5 py-4">
      <p className="text-sm text-muted">{label}</p>
      <p className={`text-3xl font-semibold mt-1 ${accentColor}`}>{value}</p>
      {hint && <p className="text-xs text-muted mt-1">{hint}</p>}
    </Card>
  )
}
