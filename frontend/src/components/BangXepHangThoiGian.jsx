import { Card, CardBody, CardHeader } from './ui'
import { dinhDangThoiGian } from '../utils/format'

/* Bảng xếp hạng dạng/loại câu tốn nhiều thời gian nhất (top 3, theo tổng thời gian hoàn
   thành) — dùng chung ở trang Tổng quan (GV, cộng dồn CẢ LỚP — góc nhìn "lớp tôi đang tắc ở
   đâu") và ở ThongKeTienDo (xem 1 HS cụ thể / HS xem chính mình — KHÔNG cộng dồn, tránh bị
   lệch bởi số lượt làm của nhiều HS khác nhau). */
export default function BangXepHangThoiGian({ title, subtitle, rows, nhan, empty }) {
  const max = Math.max(1, ...rows.map((r) => r.thoi_gian_giay || 0))
  return (
    <Card>
      <CardHeader title={title} subtitle={subtitle} />
      <CardBody className="flex flex-col gap-3">
        {rows.length === 0 ? (
          <p className="text-sm text-muted">{empty}</p>
        ) : (
          rows.map((r, i) => (
            <div key={i} className="flex flex-col gap-1">
              <div className="flex items-center justify-between gap-2">
                <span className="text-sm text-ink font-medium truncate">
                  <span className="text-muted">{i + 1}. </span>{nhan(r)}
                </span>
                <span className="text-sm font-bold text-primary shrink-0">
                  {dinhDangThoiGian(r.thoi_gian_giay)}
                </span>
              </div>
              <div className="h-2 w-full rounded-full bg-surface-2 overflow-hidden">
                <div className="h-full bg-primary"
                  style={{ width: `${((r.thoi_gian_giay || 0) / max) * 100}%` }} />
              </div>
            </div>
          ))
        )}
      </CardBody>
    </Card>
  )
}
