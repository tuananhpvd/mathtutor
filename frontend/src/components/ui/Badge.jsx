// Badge trạng thái — nhãn nghiệp vụ tiếng Việt (UIUX mục 3).
const TRANG_THAI = {
  dang_lam: { label: 'Đang làm', cls: 'bg-primary-soft text-primary' },
  hoan_thanh: { label: 'Hoàn thành', cls: 'bg-success-soft text-success' },
  bo_do: { label: 'Bỏ dở', cls: 'bg-surface-2 text-muted' },
  cho_duyet: { label: 'Chờ duyệt', cls: 'bg-warning-soft text-warning' },
  da_duyet: { label: 'Đã duyệt', cls: 'bg-success-soft text-success' },
  loai: { label: 'Đã loại', cls: 'bg-danger-soft text-danger' },
}

const TONE = {
  primary: 'bg-primary-soft text-primary',
  success: 'bg-success-soft text-success',
  warning: 'bg-warning-soft text-warning',
  danger: 'bg-danger-soft text-danger',
  neutral: 'bg-surface-2 text-muted',
}

export default function Badge({ trang_thai, tone, children, className = '' }) {
  const preset = trang_thai ? TRANG_THAI[trang_thai] : null
  const cls = preset ? preset.cls : TONE[tone || 'neutral']
  const text = children ?? preset?.label ?? trang_thai
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium
        ${cls} ${className}`}
    >
      {text}
    </span>
  )
}
