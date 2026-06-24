/*
 * Biểu đồ tiến độ đơn giản (thuần CSS, không thêm thư viện).
 * data: [{ nhan, gia_tri (0..1), phu? }]
 */
export default function ProgressChart({ data = [], title }) {
  return (
    <div>
      {title && <p className="text-sm font-medium text-ink mb-3">{title}</p>}
      {data.length === 0 ? (
        <p className="text-sm text-muted">Chưa có dữ liệu tiến độ.</p>
      ) : (
        <div className="flex flex-col gap-3">
          {data.map((d, i) => {
            const pct = Math.round((d.gia_tri || 0) * 100)
            const color =
              pct >= 70 ? 'bg-success' : pct >= 40 ? 'bg-primary' : 'bg-warning'
            return (
              <div key={i}>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-ink">{d.nhan}</span>
                  <span className="text-muted">{d.phu ?? `${pct}%`}</span>
                </div>
                <div className="h-2.5 w-full rounded-full bg-surface-2 overflow-hidden">
                  <div
                    className={`h-full rounded-full ${color} transition-all`}
                    style={{ width: `${pct}%` }}
                  />
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
