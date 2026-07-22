import { useEffect, useState } from 'react'
import {
  AlertTriangle, Building2, CheckCircle2, Clock, Flag, LifeBuoy, ListChecks, Lock, Users,
} from 'lucide-react'
import { api } from '../../api'
import { getSession } from '../../auth'
import { Button, Card, CardBody, CardHeader, StatCard } from '../../components/ui'
import BangXepHangThoiGian from '../../components/BangXepHangThoiGian'
import ChonLop from '../../components/gv/ChonLop'
import BieuDoVung from '../../components/BieuDoVung'
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
      <CardBody className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {items.map((it) => (
          <StatCard key={it.label} icon={it.icon} label={it.label} value={it.value} accent={it.accent} />
        ))}
      </CardBody>
    </Card>
  )
}

// 3 mini-card việc cần xử lý trong hero — số lớn (tông vàng "cần chú ý", nhất quán với badge
// "Chờ duyệt"/"Cờ chưa xử lý" đã dùng sẵn ở NhomThongKe bên dưới) + CTA điều hướng thẳng tới
// đúng trang xử lý.
function MiniHeroGV({ icon: Icon, value, cap, nhan, onClick }) {
  return (
    <div className="bg-surface border border-border rounded-card shadow-[var(--shadow-card)]
      p-4 flex flex-col gap-2.5">
      <div className="flex items-center gap-2.5">
        <div className="h-9 w-9 rounded-[10px] bg-warning-soft grid place-items-center shrink-0">
          <Icon size={18} strokeWidth={2.2} className="text-warning" />
        </div>
        <div>
          <p className="text-3xl font-semibold leading-none tabular-nums text-warning-ink">{value}</p>
          <p className="text-xs text-muted mt-1">{cap}</p>
        </div>
      </div>
      <Button variant="primary" size="sm" className="w-full" onClick={onClick}>{nhan}</Button>
    </div>
  )
}

export default function TongQuan({ onNavigate }) {
  const { ho_ten } = getSession() || {}
  const [tk, setTk] = useState(null)
  const [soHoTro, setSoHoTro] = useState(0)
  const [nhipLop, setNhipLop] = useState(null)
  const [khoKhan, setKhoKhan] = useState(null)
  // Đơn vị thống kê là MỘT lớp. Riêng sĩ số HS / HS bị khóa / cờ theo dõi vẫn gộp mọi lớp
  // (yêu cầu nghiệp vụ) — backend tự xử, không phụ thuộc lopId này.
  const [lopId, setLopId] = useState('')

  useEffect(() => {
    api.gvTroGiup(true).then((ds) => setSoHoTro((ds || []).length)).catch(() => {})
  }, [])

  useEffect(() => {
    api.gvTongQuan(lopId).then(setTk).catch(() => {})
    api.getNhipNgayLop(lopId).then(setNhipLop).catch(() => {})
    api.getKhoKhanNgayLop(lopId).then(setKhoKhan).catch(() => {})
  }, [lopId])

  if (!tk) return <p className="text-muted text-sm">Đang tải tổng quan...</p>

  return (
    <div className="flex flex-col gap-5">
      {/* ===== HERO: 1 vùng nổi bật duy nhất — việc cần xử lý hôm nay ===== */}
      <div className="rounded-card border border-border bg-gradient-to-br from-primary-soft
        to-primary-soft-2 p-6 flex flex-col gap-5">
        <h2 className="text-2xl font-semibold text-ink text-balance">
          Chào thầy/cô{ho_ten ? `, ${ho_ten}` : ''}! 👋
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3.5">
          <MiniHeroGV icon={LifeBuoy} value={soHoTro} cap="yêu cầu hỗ trợ học sinh chờ trả lời"
            nhan="Trả lời ngay" onClick={() => onNavigate?.('ho_tro')} />
          <MiniHeroGV icon={Clock} value={tk.cau_hoi_cho_duyet} cap="câu hỏi chưa duyệt"
            nhan="Duyệt ngay" onClick={() => onNavigate?.('cau_hoi')} />
          <MiniHeroGV icon={Flag} value={tk.co_chua_xu_ly} cap="cờ chưa xử lý"
            nhan="Xử lý ngay" onClick={() => onNavigate?.('co')} />
        </div>
      </div>

      {/* Nhịp học của lớp (teal GV) + nhiệt kế khó khăn (vàng cần-chú-ý) — 30 ngày */}
      {(nhipLop || khoKhan) && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 items-start">
          {nhipLop && (
            <BieuDoVung
              ds={nhipLop.map((d) => ({ ...d, so: d.so_bai }))}
              mau="var(--color-gv)"
              donVi="bài cả lớp hoàn thành"
              tieu_de="Nhịp học của lớp"
              phu_de="Tổng bài hoàn thành mỗi ngày (lớp đang chọn) · 30 ngày"
            />
          )}
          {khoKhan && (
            <BieuDoVung
              ds={khoKhan.map((d) => ({ ...d, so: d.tong }))}
              mau="var(--color-warning)"
              donVi="tín hiệu khó khăn"
              tieu_de="Nhiệt kế khó khăn của lớp"
              phu_de="Cờ + yêu cầu Nhờ thầy/cô mỗi ngày · đỉnh nhọn = giai đoạn HS gặp khó"
              tach={(d) => (
                <span className="inline-flex items-center gap-2.5">
                  <span className="inline-flex items-center gap-1">
                    <Flag size={11} strokeWidth={2.2} /> cờ: {d.so_co}
                  </span>
                  <span className="inline-flex items-center gap-1">
                    <LifeBuoy size={11} strokeWidth={2.2} /> nhờ thầy/cô: {d.so_nho}
                  </span>
                </span>
              )}
            />
          )}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 items-start">
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

      <div className="flex items-center justify-end">
        <ChonLop value={lopId} onChange={setLopId} nhan="Số liệu theo lớp" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 items-start">
        <BangXepHangThoiGian
          title="Dạng bài học sinh mất nhiều thời gian"
          subtitle={`Tối đa 3 dạng — thời gian TRUNG BÌNH mỗi lượt (chỉ nhóm có từ ${tk.nguong_luot ?? 5} lượt)`}
          rows={tk.dang_mat_thoi_gian}
          nhan={(r) => r.ten}
          empty="Chưa đủ dữ liệu để xếp hạng."
        />
        <BangXepHangThoiGian
          title="Loại câu hỏi học sinh mất nhiều thời gian"
          subtitle={`Thời gian TRUNG BÌNH mỗi lượt (chỉ nhóm có từ ${tk.nguong_luot ?? 5} lượt)`}
          rows={tk.loai_mat_thoi_gian}
          nhan={(r) => NHAN_LOAI_MAT_THOI_GIAN[r.loai] || r.loai}
          empty="Chưa đủ dữ liệu để xếp hạng."
        />
      </div>
    </div>
  )
}
