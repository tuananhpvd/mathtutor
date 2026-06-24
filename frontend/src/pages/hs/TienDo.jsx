import { useEffect, useState } from 'react'
import { api } from '../../api'
import { Card, CardBody, CardHeader, ProgressChart, StatCard } from '../../components/ui'
import { dinhDangThoiGian } from '../../utils/format'

export default function TienDo() {
  const [rows, setRows] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api
      .getProgressMe()
      .then(setRows)
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  const tongLam = rows.reduce((s, r) => s + r.so_bai_lam, 0)
  const tongXong = rows.reduce((s, r) => s + r.so_bai_hoan_thanh, 0)
  const tbDung =
    rows.length > 0
      ? Math.round(
          (rows.reduce((s, r) => s + r.ty_le_dung_trung_binh, 0) / rows.length) * 100
        )
      : 0
  const tongThoiGian = rows.reduce((s, r) => s + (r.tong_thoi_gian_giay || 0), 0)

  const chart = rows.map((r) => ({
    nhan: r.chuyen_de,
    gia_tri: r.ty_le_dung_trung_binh,
    phu: `${r.so_bai_hoan_thanh}/${r.so_bai_lam} bài · ${dinhDangThoiGian(r.tong_thoi_gian_giay)}`,
  }))

  return (
    <div className="flex flex-col gap-6">
      <h2 className="text-xl font-semibold text-ink">Tiến độ học tập</h2>

      <div className="grid sm:grid-cols-4 gap-4">
        <StatCard label="Bài đã hoàn thành" value={tongXong} accent="success" />
        <StatCard label="Tổng bài đã làm" value={tongLam} accent="primary" />
        <StatCard label="Tỉ lệ đúng TB" value={`${tbDung}%`} accent="warning" />
        <StatCard label="Tổng thời gian" value={dinhDangThoiGian(tongThoiGian)} accent="primary" />
      </div>

      <Card>
        <CardHeader title="Theo chuyên đề" subtitle="Tỉ lệ đúng trung bình" />
        <CardBody>
          {loading ? (
            <p className="text-sm text-muted">Đang tải...</p>
          ) : (
            <ProgressChart data={chart} />
          )}
        </CardBody>
      </Card>
    </div>
  )
}
