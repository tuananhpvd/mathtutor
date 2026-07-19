import { Card, CardBody, CardHeader } from './ui'
import { dinhDangThoiGian } from '../utils/format'

/* Bảng xếp hạng dạng/loại câu tốn nhiều thời gian nhất (top 3) — dùng chung ở trang Tổng quan
   (GV, theo MỘT lớp) và ở ThongKeTienDo (1 HS cụ thể / HS xem chính mình).

   Nhận CẢ HAI dạng dữ liệu: `thoi_gian_tb_giay` + `so_luot` (Tổng quan GV — TRUNG BÌNH mỗi
   lượt) và `thoi_gian_giay` (màn HS — thời gian của chính em đó). Trước đây Tổng quan cộng dồn
   TỔNG thời gian nên dạng được GIAO NHIỀU NHẤT luôn đứng đầu chứ không phải dạng KHÓ nhất;
   nay dùng trung bình + hiện số lượt để đọc đúng bản chất. */
function _giay(r) {
  return r.thoi_gian_tb_giay ?? r.thoi_gian_giay ?? 0
}

export default function BangXepHangThoiGian({ title, subtitle, rows, nhan, empty }) {
  const max = Math.max(1, ...rows.map(_giay))
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
                <span className="text-sm text-ink font-medium truncate min-w-0">
                  <span className="text-muted">{i + 1}. </span>{nhan(r)}
                </span>
                <span className="text-sm font-bold text-primary shrink-0 tabular-nums">
                  {dinhDangThoiGian(_giay(r))}
                  {r.so_luot != null && (
                    <span className="ml-1.5 font-normal text-xs text-muted">
                      · {r.so_luot} lượt
                    </span>
                  )}
                </span>
              </div>
              <div className="h-2 w-full rounded-full bg-surface-2 overflow-hidden">
                <div className="h-full bg-primary"
                  style={{ width: `${(_giay(r) / max) * 100}%` }} />
              </div>
            </div>
          ))
        )}
      </CardBody>
    </Card>
  )
}
