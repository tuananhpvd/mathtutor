import { useEffect, useState } from 'react'
import { api } from '../../api'
import { Badge, Card, CardBody, CardHeader, StatCard } from '../../components/ui'

export default function Dashboard() {
  const [stats, setStats] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    api.adminStats().then(setStats).catch((e) => setError(e.message))
  }, [])

  if (error) return <p className="text-danger text-sm bg-danger-soft rounded-md px-3 py-2">{error}</p>
  if (!stats) return <p className="text-muted text-sm">Đang tải thống kê...</p>

  return (
    <div className="flex flex-col gap-6">
      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Người dùng" value={stats.so_nguoi_dung} accent="primary" />
        <StatCard label="Câu hỏi" value={stats.so_cau_hoi} hint={`${stats.so_cau_da_duyet} đã duyệt`} accent="primary" />
        <StatCard label="Phiên học" value={stats.so_phien} accent="success" />
        <StatCard label="Cờ chưa xử lý" value={stats.so_co_chua_xu_ly} accent="warning" />
      </div>

      <Card>
        <CardHeader title="Phân bố vai trò & LLM" />
        <CardBody className="flex flex-wrap gap-6">
          <div>
            <p className="text-sm text-muted">Giáo viên</p>
            <p className="text-2xl font-semibold text-ink">{stats.so_giao_vien}</p>
          </div>
          <div>
            <p className="text-sm text-muted">Học sinh</p>
            <p className="text-2xl font-semibold text-ink">{stats.so_hoc_sinh}</p>
          </div>
          <div>
            <p className="text-sm text-muted">Nhà cung cấp LLM</p>
            <p className="mt-1">
              <Badge tone="primary">{stats.llm_provider}</Badge>
            </p>
          </div>
        </CardBody>
      </Card>
    </div>
  )
}
