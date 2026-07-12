import { useEffect, useState } from 'react'
import { api } from '../../api'
import { Badge, Card, CardBody, CardHeader, StatCard } from '../../components/ui'

const LOAI_LABEL = { TN4PA: 'Trắc nghiệm 4 PA', TNDS: 'Đúng/Sai', TLN: 'Tự luận ngắn' }
const DO_KHO_LABEL = { de: 'Dễ', tb: 'Trung bình', kho: 'Khó' }

function MiniStat({ label, value, tone }) {
  const color =
    tone === 'success' ? 'text-success' :
    tone === 'warning' ? 'text-warning' :
    tone === 'danger' ? 'text-danger' : 'text-ink'
  return (
    <div className="rounded-lg bg-surface-2 px-4 py-3 min-w-[80px] text-center">
      <p className="text-xs text-muted mb-1">{label}</p>
      <p className={`text-xl font-semibold ${color}`}>{value}</p>
    </div>
  )
}

export default function Dashboard() {
  const [stats, setStats] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    api.adminStats().then(setStats).catch((e) => setError(e.message))
  }, [])

  if (error) return <p className="text-danger text-sm bg-danger-soft rounded-md px-3 py-2">{error}</p>
  if (!stats) return <p className="text-muted text-sm">Đang tải thống kê...</p>

  return (
    <div className="flex flex-col gap-5">
      {/* Hàng chỉ số tổng quan */}
      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Tổng người dùng" value={stats.so_nguoi_dung} accent="primary" />
        <StatCard label="Câu hỏi hoạt động" value={stats.so_cau_hoi} accent="primary" />
        <StatCard label="Tổng phiên học" value={stats.so_phien} accent="success" />
        <StatCard label="Cờ chưa xử lý" value={stats.so_co_chua_xu_ly} accent="warning" />
      </div>

      {/* Người dùng & Lớp + Phiên học — 2 thẻ cao xấp xỉ nhau nên ghép cùng hàng */}
      <div className="grid lg:grid-cols-2 gap-4 items-start">
        <Card>
          <CardHeader title="Người dùng & Lớp học" />
          <CardBody>
            <div className="flex gap-4 flex-wrap">
              <MiniStat label="Giáo viên" value={stats.so_giao_vien} />
              <MiniStat label="Học sinh" value={stats.so_hoc_sinh} />
              <MiniStat label="Lớp học" value={stats.so_lop} />
            </div>
          </CardBody>
        </Card>

        <Card>
          <CardHeader title="Phiên học" />
          <CardBody>
            <div className="flex gap-4 flex-wrap">
              <MiniStat label="Đang học" value={stats.so_phien_dang_lam} tone="success" />
              <MiniStat label="Hoàn thành" value={stats.so_phien_hoan_thanh} />
            </div>
          </CardBody>
        </Card>
      </div>

      {/* Câu hỏi (trái) + Cờ theo dõi & Hệ thống (phải) */}
      <div className="grid lg:grid-cols-2 gap-4 items-start">
        <Card>
          <CardHeader title="Câu hỏi" subtitle={`${stats.so_cau_hoi} đang hoạt động · ${stats.so_cau_an || 0} đã ẩn`} />
          <CardBody className="flex flex-col gap-4">
            <div className="flex gap-3 flex-wrap">
              <MiniStat label="Đã duyệt" value={stats.so_cau_da_duyet} tone="success" />
              <MiniStat label="Chờ duyệt" value={stats.so_cau_cho_duyet} tone="warning" />
              <MiniStat label="Đã ẩn" value={stats.so_cau_an || 0} tone="danger" />
            </div>
            <div className="flex flex-col gap-4">
              <div>
                <p className="text-xs font-medium text-muted uppercase tracking-wide mb-2">Theo loại câu</p>
                <div className="flex gap-2 flex-wrap">
                  {Object.entries(stats.cau_theo_loai || {}).map(([k, v]) => (
                    <div key={k} className="rounded-lg bg-surface-2 px-3 py-2 text-center">
                      <p className="text-[11px] text-muted leading-tight">{LOAI_LABEL[k] || k}</p>
                      <p className="text-lg font-semibold text-ink">{v}</p>
                    </div>
                  ))}
                </div>
              </div>
              <div>
                <p className="text-xs font-medium text-muted uppercase tracking-wide mb-2">Theo độ khó</p>
                <div className="flex gap-2 flex-wrap">
                  {Object.entries(stats.cau_theo_do_kho || {}).map(([k, v]) => (
                    <div key={k} className="rounded-lg bg-surface-2 px-3 py-2 text-center min-w-[64px]">
                      <p className="text-[11px] text-muted leading-tight">{DO_KHO_LABEL[k] || k}</p>
                      <p className="text-lg font-semibold text-ink">{v}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </CardBody>
        </Card>

        <Card>
          <CardHeader title="Cờ theo dõi & Hệ thống" />
          <CardBody className="flex flex-wrap gap-6 items-start">
            <div>
              <p className="text-sm text-muted">Tổng cờ</p>
              <p className="text-2xl font-semibold text-ink">{stats.so_co_tong}</p>
            </div>
            <div>
              <p className="text-sm text-muted">Chờ xử lý</p>
              <p className="text-2xl font-semibold text-warning">{stats.so_co_chua_xu_ly}</p>
            </div>
            <div>
              <p className="text-sm text-muted mb-1">Nhà cung cấp LLM</p>
              <Badge tone="primary">{stats.llm_provider}</Badge>
            </div>
          </CardBody>
        </Card>
      </div>
    </div>
  )
}
