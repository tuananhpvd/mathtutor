const pct = (n, t) => (t > 0 ? Math.round((n / t) * 100) : 0)

// Vòng tròn tiến độ tổng (SVG) — tách dùng chung giữa TongQuanTienDo và nơi khác nếu cần.
function VongTienDo({ percent, size = 132, stroke = 13 }) {
  const r = (size - stroke) / 2
  const c = 2 * Math.PI * r
  const off = c * (1 - percent / 100)
  return (
    <div className="relative shrink-0 w-full mx-auto" style={{ maxWidth: size }}>
      <svg viewBox={`0 0 ${size} ${size}`} className="w-full h-auto -rotate-90">
        <circle cx={size / 2} cy={size / 2} r={r} fill="none"
          stroke="var(--color-surface-2)" strokeWidth={stroke} />
        <circle cx={size / 2} cy={size / 2} r={r} fill="none"
          stroke="var(--color-success)" strokeWidth={stroke} strokeLinecap="round"
          strokeDasharray={c} strokeDashoffset={off}
          style={{ transition: 'stroke-dashoffset .6s ease' }} />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-3xl font-bold text-ink">{percent}%</span>
        <span className="text-xs text-muted">hoàn thành</span>
      </div>
    </div>
  )
}

// Vòng tròn % hoàn thành (trái) + 4 ô Tổng/Hoàn thành/Đang dở/Chưa làm dạng lưới 2x2 (phải).
// Dùng chung ở "Tiến độ của em" (trang chủ HS) và hero ThongKeTienDo (GV xem HS / HS chi tiết).
// tq: {tong, hoan_thanh, dang_lam, chua_lam}.
export default function TongQuanTienDo({ tq }) {
  return (
    <div className="flex flex-col sm:flex-row items-center gap-6">
      <VongTienDo percent={pct(tq.hoan_thanh, tq.tong)} />
      <div className="flex-1 w-full grid grid-cols-2 gap-3">
        <div className="rounded-lg bg-surface-2 px-4 py-3">
          <p className="text-xs text-muted">Tổng số bài</p>
          <p className="text-2xl font-bold text-ink tabular-nums">{tq.tong}</p>
        </div>
        <div className="rounded-lg bg-success-soft px-4 py-3">
          <p className="text-xs text-success">Đã hoàn thành</p>
          <p className="text-2xl font-bold text-success tabular-nums">
            {tq.hoan_thanh} <span className="text-base font-semibold">({pct(tq.hoan_thanh, tq.tong)}%)</span>
          </p>
        </div>
        {/* "Đang làm dở" — vàng cảnh báo trung tính (KHÔNG đỏ, không phải lỗi). */}
        <div className="rounded-lg bg-warning-soft px-4 py-3">
          <p className="text-xs text-warning">Đang làm dở</p>
          <p className="text-2xl font-bold text-warning tabular-nums">
            {tq.dang_lam} <span className="text-base font-semibold">({pct(tq.dang_lam, tq.tong)}%)</span>
          </p>
        </div>
        {/* "Chưa làm" — xám trung tính (KHÔNG đỏ, tránh cảm giác "đang thất bại"). */}
        <div className="rounded-lg bg-idle-soft px-4 py-3">
          <p className="text-xs text-idle">Chưa làm</p>
          <p className="text-2xl font-bold text-idle tabular-nums">
            {tq.chua_lam} <span className="text-base font-semibold">({pct(tq.chua_lam, tq.tong)}%)</span>
          </p>
        </div>
      </div>
    </div>
  )
}
