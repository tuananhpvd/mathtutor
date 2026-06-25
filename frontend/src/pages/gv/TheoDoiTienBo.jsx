import { useEffect, useState } from 'react'
import { api } from '../../api'
import { Badge, Button, Card, CardBody, CardHeader, Table } from '../../components/ui'
import { dinhDangThoiGian } from '../../utils/format'
import ThongKeTienDo from '../../components/ThongKeTienDo'

export default function TheoDoiTienBo() {
  const [students, setStudents] = useState([])
  const [loading, setLoading] = useState(true)
  const [chon, setChon] = useState(null)
  const [tkChon, setTkChon] = useState(null)
  const [dangTaiTk, setDangTaiTk] = useState(false)
  const [nhatKy, setNhatKy] = useState([])

  useEffect(() => {
    api
      .getProgressStudents()
      .then((s) => {
        setStudents(s)
        if (s.length) xemHs(s[0].hoc_sinh_id)
      })
      .catch(() => {})
      .finally(() => setLoading(false))
    api.listSessionsHoanThanh().then(setNhatKy).catch(() => {})
  }, [])

  function xemHs(id) {
    setChon(id)
    setTkChon(null)
    setDangTaiTk(true)
    api
      .getThongKeHocSinh(id)
      .then(setTkChon)
      .catch(() => {})
      .finally(() => setDangTaiTk(false))
  }

  function tongHopHs(hs) {
    const td = hs.tien_do || []
    const xong = td.reduce((s, t) => s + t.so_bai_hoan_thanh, 0)
    const lam = td.reduce((s, t) => s + t.so_bai_lam, 0)
    const tb =
      td.length > 0
        ? Math.round((td.reduce((s, t) => s + t.ty_le_dung_trung_binh, 0) / td.length) * 100)
        : 0
    return { xong, lam, tb }
  }

  const hsChon = students.find((h) => h.hoc_sinh_id === chon)

  return (
    <div className="flex flex-col gap-4">
      <Card>
        <CardHeader title="Học sinh lớp của tôi" subtitle={`${students.length} học sinh`} />
        <CardBody className="pt-0">
          {loading ? (
            <p className="text-muted text-sm">Đang tải...</p>
          ) : (
            <Table
              columns={[
                { key: 'ho_ten', header: 'Học sinh' },
                { key: 'lam', header: 'Đã làm', render: (r) => tongHopHs(r).lam },
                { key: 'xong', header: 'Hoàn thành', render: (r) => tongHopHs(r).xong },
                { key: 'tb', header: 'Tỉ lệ đúng TB', render: (r) => `${tongHopHs(r).tb}%` },
                {
                  key: 'tg',
                  header: 'Tổng thời gian',
                  render: (r) =>
                    dinhDangThoiGian(
                      (r.tien_do || []).reduce((s, t) => s + (t.tong_thoi_gian_giay || 0), 0)
                    ),
                },
                {
                  key: 'xem',
                  header: '',
                  render: (r) => (
                    <Button size="sm" variant="ghost" onClick={() => xemHs(r.hoc_sinh_id)}>
                      Xem biểu đồ
                    </Button>
                  ),
                },
              ]}
              rows={students}
              rowKey={(r) => r.hoc_sinh_id}
              empty="Lớp chưa có học sinh."
            />
          )}
        </CardBody>
      </Card>

      {hsChon && (
        <div className="flex flex-col gap-2">
          <h3 className="text-lg font-bold text-ink">Tiến độ chi tiết: {hsChon.ho_ten}</h3>
          {dangTaiTk ? (
            <p className="text-sm text-muted">Đang tải thống kê...</p>
          ) : (
            <ThongKeTienDo tk={tkChon} />
          )}
        </div>
      )}

      <Card>
        <CardHeader title="Nhật ký hoàn thành" subtitle="Các bài học sinh đã làm xong (kèm thời gian)" />
        <CardBody className="pt-0">
          <Table
            columns={[
              { key: 'ho_ten', header: 'Học sinh' },
              { key: 'chuyen_de', header: 'Chuyên đề' },
              { key: 'loai_cau', header: 'Loại', render: (r) => <Badge tone="primary">{r.loai_cau}</Badge> },
              { key: 'diem', header: 'Điểm', render: (r) => (r.diem != null ? r.diem : '—') },
              { key: 'tg', header: 'Thời gian', render: (r) => dinhDangThoiGian(r.thoi_gian_giay) },
              {
                key: 'luc',
                header: 'Hoàn thành lúc',
                render: (r) => new Date(r.hoan_thanh_luc).toLocaleString('vi-VN'),
              },
            ]}
            rows={nhatKy}
            rowKey={(r) => r.session_id}
            empty="Chưa có bài nào hoàn thành."
          />
        </CardBody>
      </Card>
    </div>
  )
}
