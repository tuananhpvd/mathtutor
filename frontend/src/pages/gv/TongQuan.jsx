import { useEffect, useState } from 'react'
import { api } from '../../api'
import { Badge, Button, Card, CardBody, CardHeader, ProgressChart, StatCard } from '../../components/ui'

// Tổng hợp client-side từ các endpoint sẵn có (chưa có endpoint thống kê riêng).
export default function TongQuan({ onNavigate }) {
  const [problems, setProblems] = useState([])
  const [flags, setFlags] = useState([])
  const [students, setStudents] = useState([])

  useEffect(() => {
    Promise.all([api.listProblems(), api.listFlags(), api.getProgressStudents()])
      .then(([p, f, s]) => {
        setProblems(p)
        setFlags(f)
        setStudents(s)
      })
      .catch(() => {})
  }, [])

  const daDuyet = problems.filter((p) => p.trang_thai_duyet === 'da_duyet').length
  const choDuyet = problems.filter((p) => p.trang_thai_duyet === 'cho_duyet').length
  const coChuaXuLy = flags.filter((f) => f.trang_thai === 'cho_xu_ly').length

  // Chuyên đề yếu: gộp tỉ lệ đúng trung bình theo chuyên đề toàn lớp.
  const gop = {}
  students.forEach((hs) =>
    (hs.tien_do || []).forEach((t) => {
      if (!gop[t.chuyen_de]) gop[t.chuyen_de] = []
      gop[t.chuyen_de].push(t.ty_le_dung_trung_binh)
    })
  )
  const yeu = Object.entries(gop)
    .map(([chuyen_de, arr]) => ({
      nhan: chuyen_de,
      gia_tri: arr.reduce((s, x) => s + x, 0) / arr.length,
    }))
    .sort((a, b) => a.gia_tri - b.gia_tri)

  return (
    <div className="flex flex-col gap-6">
      <div className="grid sm:grid-cols-4 gap-4">
        <StatCard label="Học sinh" value={students.length} accent="primary" />
        <StatCard label="Câu hỏi đã duyệt" value={daDuyet} accent="success" />
        <StatCard label="Chờ duyệt" value={choDuyet} accent="warning" />
        <StatCard label="Cờ chưa xử lý" value={coChuaXuLy} accent="warning" />
      </div>

      <div className="grid lg:grid-cols-2 gap-4">
        <Card>
          <CardHeader
            title="Chuyên đề lớp còn yếu"
            subtitle="Tỉ lệ đúng trung bình toàn lớp"
            action={<Button size="sm" variant="ghost" onClick={() => onNavigate('tien_bo')}>Chi tiết</Button>}
          />
          <CardBody>
            <ProgressChart data={yeu} />
          </CardBody>
        </Card>

        <Card>
          <CardHeader
            title="Cờ cần xử lý"
            subtitle="Phiên học có dấu hiệu cần chú ý"
            action={<Button size="sm" variant="ghost" onClick={() => onNavigate('co')}>Xem tất cả</Button>}
          />
          <CardBody className="flex flex-col gap-2">
            {flags.filter((f) => f.trang_thai === 'cho_xu_ly').length === 0 ? (
              <p className="text-sm text-muted">Không có cờ nào đang chờ. 👍</p>
            ) : (
              flags
                .filter((f) => f.trang_thai === 'cho_xu_ly')
                .slice(0, 5)
                .map((f) => (
                  <div key={f.id} className="flex items-center justify-between rounded-md border border-border px-3 py-2">
                    <span className="text-sm text-ink">Phiên #{f.session_id}</span>
                    <Badge tone="warning">{f.loai_co}</Badge>
                  </div>
                ))
            )}
          </CardBody>
        </Card>
      </div>
    </div>
  )
}
