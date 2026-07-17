import { useEffect, useState } from 'react'
import {
  Activity, AlertTriangle, Building2, CheckCircle2, Clock, Cpu, EyeOff, Flag, GraduationCap,
  ListChecks, Users,
} from 'lucide-react'
import { api } from '../../api'
import { Badge, Card, CardBody, CardHeader, StatCard } from '../../components/ui'
import BieuDoVung from '../../components/BieuDoVung'

const LOAI_LABEL = { TN4PA: 'Trắc nghiệm 4 PA', TNDS: 'Đúng/Sai', TLN: 'Tự luận ngắn' }
const DO_KHO_LABEL = { de: 'Dễ', tb: 'Trung bình', kho: 'Khó' }
const DO_KHO_TONE = { de: 'success', tb: 'warning', kho: 'danger' }

const TONE_TEXT = { primary: 'text-primary', success: 'text-success', warning: 'text-warning', danger: 'text-danger', accent: 'text-accent', idle: 'text-idle' }
const TONE_BG = { primary: 'bg-primary-soft', success: 'bg-success-soft', warning: 'bg-warning-soft', danger: 'bg-danger-soft', accent: 'bg-accent-soft', idle: 'bg-idle-soft' }

// Icon trong khối màu + số liệu lớn, đậm — nhấn mạnh con số thay vì chỉ chữ thường như trước.
function MiniStat({ icon: Icon, label, value, tone = 'primary' }) {
  return (
    <div className="flex items-center gap-3 rounded-lg bg-surface-2 px-4 py-3 flex-1 min-w-[140px]">
      <div className={`h-10 w-10 rounded-lg grid place-items-center shrink-0 ${TONE_TEXT[tone]} ${TONE_BG[tone]}`}>
        <Icon size={20} strokeWidth={2} />
      </div>
      <div className="min-w-0">
        <p className="text-2xl font-bold text-ink leading-tight">{value}</p>
        <p className="text-xs text-muted truncate mt-0.5">{label}</p>
      </div>
    </div>
  )
}

// Ô số liệu phụ, nhỏ gọn hơn MiniStat — dùng cho phần chi tiết (theo loại/độ khó) đứng dưới
// nhóm chỉ số chính, đúng thứ bậc "tổng quan trước, chi tiết sau".
function ONho({ label, value, tone }) {
  return (
    <div className={`rounded-lg px-3 py-2 text-center min-w-[64px] ${tone ? TONE_BG[tone] : 'bg-surface-2'}`}>
      <p className={`text-lg font-semibold ${tone ? TONE_TEXT[tone] : 'text-ink'}`}>{value}</p>
      <p className={`text-[11px] leading-tight mt-0.5 ${tone ? TONE_TEXT[tone] : 'text-muted'}`}>{label}</p>
    </div>
  )
}

function TieuDeThe({ icon: Icon, children }) {
  return (
    <span className="inline-flex items-center gap-2">
      <Icon size={18} strokeWidth={2.2} className="text-primary" />
      {children}
    </span>
  )
}

export default function Dashboard() {
  const [stats, setStats] = useState(null)
  const [phienNgay, setPhienNgay] = useState(null)
  const [llmNgay, setLlmNgay] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    api.adminStats().then(setStats).catch((e) => setError(e.message))
    api.adminPhienTheoNgay().then(setPhienNgay).catch(() => {})
    api.adminLlmTheoNgay().then(setLlmNgay).catch(() => {})
  }, [])

  if (error) return <p className="text-danger text-sm bg-danger-soft rounded-md px-3 py-2">{error}</p>
  if (!stats) return <p className="text-muted text-sm">Đang tải thống kê...</p>

  // Tổng 30 ngày theo loại cho phần chú thích dưới biểu đồ LLM.
  const tongLlm = (llmNgay || []).reduce(
    (a, d) => ({ ht: a.ht + d.hoi_thoai, sinh: a.sinh + d.sinh_cau_hoi, pt: a.pt + d.phan_tich }),
    { ht: 0, sinh: 0, pt: 0 },
  )

  return (
    <div className="flex flex-col gap-5">
      {/* Hàng chỉ số tổng quan */}
      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon={Users} label="Người dùng" value={stats.so_nguoi_dung} accent="primary" />
        <StatCard icon={ListChecks} label="Câu hỏi" value={stats.so_cau_hoi} accent="primary" />
        <StatCard icon={Activity} label="Phiên học" value={stats.so_phien} accent="success" />
        <StatCard icon={AlertTriangle} label="Cờ chưa xử lý" value={stats.so_co_chua_xu_ly} accent="warning" />
      </div>

      {/* Nhịp sử dụng 30 ngày: phiên học + lượt gọi AI (tím accent = màu riêng tính năng AI) */}
      <div className="grid lg:grid-cols-2 gap-4 items-start">
        {phienNgay && (
          <BieuDoVung
            ds={phienNgay.map((d) => ({ ...d, so: d.so_phien }))}
            donVi="phiên học"
            tieu_de="Phiên học mỗi ngày"
            phu_de="Toàn hệ thống · 30 ngày gần nhất"
          />
        )}
        {llmNgay && (
          <div className="flex flex-col gap-2">
            <BieuDoVung
              ds={llmNgay.map((d) => ({ ...d, so: d.tong }))}
              mau="var(--color-accent)"
              donVi="lượt gọi AI"
              tieu_de="Lượt gọi AI (LLM) mỗi ngày"
              phu_de="Theo dõi quota · rê chuột xem tách loại"
              tach={(d) => `💬 hội thoại: ${d.hoi_thoai} · ✨ sinh câu hỏi: ${d.sinh_cau_hoi} · 📊 phân tích: ${d.phan_tich}`}
            />
            <p className="text-xs text-muted px-1">
              Tổng 30 ngày: 💬 hội thoại <b className="text-ink">{tongLlm.ht}</b> ·
              ✨ sinh câu hỏi <b className="text-ink">{tongLlm.sinh}</b> ·
              📊 phân tích <b className="text-ink">{tongLlm.pt}</b>
            </p>
          </div>
        )}
      </div>

      {/* Người dùng & Lớp + Phiên học — 2 thẻ cao xấp xỉ nhau nên ghép cùng hàng */}
      <div className="grid lg:grid-cols-2 gap-4 items-start">
        <Card>
          <CardHeader title={<TieuDeThe icon={Users}>Người dùng & Lớp học</TieuDeThe>} />
          <CardBody>
            <div className="flex gap-3 flex-wrap">
              <MiniStat icon={GraduationCap} label="Giáo viên" value={stats.so_giao_vien} />
              <MiniStat icon={Users} label="Học sinh" value={stats.so_hoc_sinh} />
              <MiniStat icon={Building2} label="Lớp học" value={stats.so_lop} />
            </div>
          </CardBody>
        </Card>

        <Card>
          <CardHeader title="Phiên học" />
          <CardBody>
            <div className="flex gap-4 flex-wrap">
              <MiniStat icon={Clock} label="Đang học" value={stats.so_phien_dang_lam} tone="success" />
              <MiniStat icon={CheckCircle2} label="Hoàn thành" value={stats.so_phien_hoan_thanh} />
            </div>
          </CardBody>
        </Card>
      </div>

      {/* Câu hỏi (trái) + Cờ theo dõi & Hệ thống (phải) */}
      <div className="grid lg:grid-cols-2 gap-4 items-start">
        <Card>
          <CardHeader title={<TieuDeThe icon={CheckCircle2}>Câu hỏi</TieuDeThe>}
            subtitle={`${stats.so_cau_hoi} đang hoạt động · ${stats.so_cau_an || 0} đã ẩn`} />
          <CardBody className="flex flex-col gap-4">
            <div className="flex gap-3 flex-wrap">
              <MiniStat icon={CheckCircle2} label="Đã duyệt" value={stats.so_cau_da_duyet} tone="success" />
              <MiniStat icon={Clock} label="Chờ duyệt" value={stats.so_cau_cho_duyet} tone="warning" />
              <MiniStat icon={EyeOff} label="Đã ẩn" value={stats.so_cau_an || 0} tone="idle" />
            </div>
            <div className="grid sm:grid-cols-2 gap-4">
              <div>
                <p className="text-xs font-medium text-muted uppercase tracking-wide mb-2">Theo loại câu</p>
                <div className="flex gap-2 flex-wrap">
                  {Object.entries(stats.cau_theo_loai || {}).map(([k, v]) => (
                    <ONho key={k} label={LOAI_LABEL[k] || k} value={v} />
                  ))}
                </div>
              </div>
              <div>
                <p className="text-xs font-medium text-muted uppercase tracking-wide mb-2">Theo độ khó</p>
                <div className="flex gap-2 flex-wrap">
                  {Object.entries(stats.cau_theo_do_kho || {}).map(([k, v]) => (
                    <ONho key={k} label={DO_KHO_LABEL[k] || k} value={v} tone={DO_KHO_TONE[k]} />
                  ))}
                </div>
              </div>
            </div>
          </CardBody>
        </Card>

        <Card>
          <CardHeader title={<TieuDeThe icon={Flag}>Cờ theo dõi & Hệ thống</TieuDeThe>} />
          <CardBody className="flex flex-col gap-4">
            <div className="flex gap-3 flex-wrap">
              <MiniStat icon={Flag} label="Tổng cờ" value={stats.so_co_tong} />
              <MiniStat icon={AlertTriangle} label="Chờ xử lý" value={stats.so_co_chua_xu_ly} tone="warning" />
            </div>
            <div className="flex items-center gap-3 rounded-lg bg-surface-2 px-4 py-3">
              <div className="h-10 w-10 rounded-lg grid place-items-center shrink-0 text-accent bg-accent-soft">
                <Cpu size={20} strokeWidth={2} />
              </div>
              <div>
                <p className="text-xs text-muted mb-1">Nhà cung cấp LLM</p>
                <Badge tone="primary">{stats.llm_provider}</Badge>
              </div>
            </div>
          </CardBody>
        </Card>
      </div>
    </div>
  )
}
