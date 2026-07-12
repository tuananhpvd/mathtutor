import { useEffect, useState } from 'react'
import { api } from '../../api'
import { Card, CardBody, CardHeader, StatCard } from '../../components/ui'
import { dinhDangThoiGian } from '../../utils/format'

const NHAN_LOAI = { TN4PA: 'Trắc nghiệm ABCD', TNDS: 'Đúng/Sai 4 ý', TLN: 'Trả lời ngắn' }

function NhomThongKe({ title, items }) {
  return (
    <Card>
      <CardHeader title={title} />
      <CardBody className="grid sm:grid-cols-3 gap-4">
        {items.map((it) => (
          <StatCard key={it.label} label={it.label} value={it.value} accent={it.accent} />
        ))}
      </CardBody>
    </Card>
  )
}

function BangXepHang({ title, subtitle, rows, nhan, empty }) {
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

export default function TongQuan() {
  const [tk, setTk] = useState(null)

  useEffect(() => {
    api.gvTongQuan().then(setTk).catch(() => {})
  }, [])

  if (!tk) return <p className="text-muted text-sm">Đang tải tổng quan...</p>

  return (
    <div className="flex flex-col gap-5">
      <div className="grid lg:grid-cols-2 gap-4 items-start">
        <NhomThongKe
          title="Lớp & học sinh"
          items={[
            { label: 'Số lớp phụ trách', value: tk.so_lop, accent: 'primary' },
            { label: 'Tổng số học sinh', value: tk.tong_hoc_sinh, accent: 'primary' },
            { label: 'Số học sinh bị khóa', value: tk.hoc_sinh_khoa, accent: 'danger' },
          ]}
        />
        <NhomThongKe
          title="Câu hỏi"
          items={[
            { label: 'Tổng số câu hỏi', value: tk.tong_cau_hoi, accent: 'primary' },
            { label: 'Số câu hỏi đã duyệt', value: tk.cau_hoi_da_duyet, accent: 'success' },
            { label: 'Số câu hỏi chờ duyệt', value: tk.cau_hoi_cho_duyet, accent: 'warning' },
          ]}
        />
      </div>
      <NhomThongKe
        title="Cờ theo dõi"
        items={[
          { label: 'Tổng số cờ theo dõi', value: tk.tong_co, accent: 'primary' },
          { label: 'Số cờ đã xử lý', value: tk.co_da_xu_ly, accent: 'success' },
          { label: 'Số cờ chưa xử lý', value: tk.co_chua_xu_ly, accent: 'warning' },
        ]}
      />

      <div className="grid lg:grid-cols-2 gap-4 items-start">
        <BangXepHang
          title="Dạng bài học sinh mất nhiều thời gian"
          subtitle="Tối đa 3 dạng — theo tổng thời gian hoàn thành"
          rows={tk.dang_mat_thoi_gian}
          nhan={(r) => r.ten}
          empty="Chưa có dữ liệu hoàn thành."
        />
        <BangXepHang
          title="Loại câu hỏi học sinh mất nhiều thời gian"
          subtitle="Theo tổng thời gian hoàn thành"
          rows={tk.loai_mat_thoi_gian}
          nhan={(r) => NHAN_LOAI[r.loai] || r.loai}
          empty="Chưa có dữ liệu hoàn thành."
        />
      </div>
    </div>
  )
}
