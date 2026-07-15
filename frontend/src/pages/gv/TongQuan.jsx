import { useEffect, useState } from 'react'
import {
  AlertTriangle, Building2, CheckCircle2, Clock, Flag, ListChecks, Lock, Users,
} from 'lucide-react'
import { api } from '../../api'
import { Card, CardBody, CardHeader, StatCard } from '../../components/ui'
import BangXepHangThoiGian from '../../components/BangXepHangThoiGian'
import { NHAN_LOAI_MAT_THOI_GIAN } from '../../utils/format'

function TieuDeThe({ icon: Icon, children }) {
  return (
    <span className="inline-flex items-center gap-2">
      <Icon size={18} strokeWidth={2.2} className="text-primary" />
      {children}
    </span>
  )
}

function NhomThongKe({ title, icon, items }) {
  return (
    <Card>
      <CardHeader title={icon ? <TieuDeThe icon={icon}>{title}</TieuDeThe> : title} />
      <CardBody className="grid sm:grid-cols-3 gap-4">
        {items.map((it) => (
          <StatCard key={it.label} icon={it.icon} label={it.label} value={it.value} accent={it.accent} />
        ))}
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
          icon={Users}
          items={[
            { label: 'Lớp phụ trách', value: tk.so_lop, accent: 'primary', icon: Building2 },
            { label: 'Học sinh', value: tk.tong_hoc_sinh, accent: 'primary', icon: Users },
            { label: 'Bị khóa', value: tk.hoc_sinh_khoa, accent: 'danger', icon: Lock },
          ]}
        />
        <NhomThongKe
          title="Câu hỏi"
          icon={ListChecks}
          items={[
            { label: 'Câu hỏi', value: tk.tong_cau_hoi, accent: 'primary', icon: ListChecks },
            { label: 'Đã duyệt', value: tk.cau_hoi_da_duyet, accent: 'success', icon: CheckCircle2 },
            { label: 'Chờ duyệt', value: tk.cau_hoi_cho_duyet, accent: 'warning', icon: Clock },
          ]}
        />
      </div>
      <NhomThongKe
        title="Cờ theo dõi"
        icon={Flag}
        items={[
          { label: 'Tổng số cờ theo dõi', value: tk.tong_co, accent: 'primary', icon: Flag },
          { label: 'Số cờ đã xử lý', value: tk.co_da_xu_ly, accent: 'success', icon: CheckCircle2 },
          { label: 'Số cờ chưa xử lý', value: tk.co_chua_xu_ly, accent: 'warning', icon: AlertTriangle },
        ]}
      />

      <div className="grid lg:grid-cols-2 gap-4 items-start">
        <BangXepHangThoiGian
          title="Dạng bài học sinh mất nhiều thời gian"
          subtitle="Tối đa 3 dạng — tổng thời gian cộng dồn CẢ LỚP"
          rows={tk.dang_mat_thoi_gian}
          nhan={(r) => r.ten}
          empty="Chưa có dữ liệu hoàn thành."
        />
        <BangXepHangThoiGian
          title="Loại câu hỏi học sinh mất nhiều thời gian"
          subtitle="Tổng thời gian cộng dồn CẢ LỚP"
          rows={tk.loai_mat_thoi_gian}
          nhan={(r) => NHAN_LOAI_MAT_THOI_GIAN[r.loai] || r.loai}
          empty="Chưa có dữ liệu hoàn thành."
        />
      </div>
    </div>
  )
}
