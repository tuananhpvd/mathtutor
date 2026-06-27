import { useEffect, useMemo, useState } from 'react'
import { api } from '../../api'
import { Badge, Button, Card, CardBody, CardHeader, Select, Table } from '../../components/ui'
import { dinhDangThoiGian } from '../../utils/format'
import ThongKeTienDo from '../../components/ThongKeTienDo'
import PhanTichNangLuc from '../../components/PhanTichNangLuc'

function PhanTrang({ trang, tong, onLui, onToi }) {
  if (tong <= 1) return null
  return (
    <div className="flex items-center justify-end gap-2 pt-2">
      <Button size="sm" variant="secondary" disabled={trang <= 1} onClick={onLui}>Trước</Button>
      <span className="text-sm text-muted">Trang {trang}/{tong}</span>
      <Button size="sm" variant="secondary" disabled={trang >= tong} onClick={onToi}>Sau</Button>
    </div>
  )
}

export default function TheoDoiTienBo() {
  const [students, setStudents] = useState([])
  const [loading, setLoading] = useState(true)
  const [chon, setChon] = useState(null)
  const [tkChon, setTkChon] = useState(null)
  const [ptChon, setPtChon] = useState(null)
  const [dangTaiTk, setDangTaiTk] = useState(false)
  const [dangCapNhatAi, setDangCapNhatAi] = useState(false)
  const [nhatKy, setNhatKy] = useState([])
  const [fLop, setFLop] = useState('')
  const [tongHop, setTongHop] = useState(null)
  const [trangHs, setTrangHs] = useState(1)
  const [trangNk, setTrangNk] = useState(1)
  const MOI_TRANG = 5

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
    api.getTongHopLop().then(setTongHop).catch(() => {})
  }, [])

  function xemHs(id) {
    setChon(id)
    setTkChon(null)
    setPtChon(null)
    setDangTaiTk(true)
    Promise.all([api.getThongKeHocSinh(id), api.getPhanTichHocSinh(id)])
      .then(([tk, pt]) => { setTkChon(tk); setPtChon(pt) })
      .catch(() => {})
      .finally(() => setDangTaiTk(false))
  }

  async function capNhatAi() {
    if (!chon) return
    setDangCapNhatAi(true)
    try { setPtChon(await api.capNhatPhanTichHocSinh(chon)) } catch { /* giữ nguyên */ }
    finally { setDangCapNhatAi(false) }
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

  // Danh sách lớp (để lọc) + danh sách HS đã lọc
  const lopOptions = useMemo(() => {
    const ten = [...new Set(students.map((s) => s.lop_ten).filter(Boolean))].sort()
    return ten.map((t) => ({ value: t, label: t }))
  }, [students])
  const dsLoc = useMemo(
    () => (fLop ? students.filter((s) => s.lop_ten === fLop) : students),
    [students, fLop]
  )

  // Phân trang (5/trang) cho bảng học sinh và nhật ký
  const tongTrangHs = Math.max(1, Math.ceil(dsLoc.length / MOI_TRANG))
  const trangHsAt = Math.min(trangHs, tongTrangHs)
  const hsTrang = dsLoc.slice((trangHsAt - 1) * MOI_TRANG, trangHsAt * MOI_TRANG)
  const tongTrangNk = Math.max(1, Math.ceil(nhatKy.length / MOI_TRANG))
  const trangNkAt = Math.min(trangNk, tongTrangNk)
  const nkTrang = nhatKy.slice((trangNkAt - 1) * MOI_TRANG, trangNkAt * MOI_TRANG)

  return (
    <div className="flex flex-col gap-4">
      {tongHop && (tongHop.dang_yeu_chung.length > 0 || tongHop.hoc_sinh_can_chu_y.length > 0) && (
        <Card>
          <CardHeader title="Tổng hợp lớp"
            subtitle={`Phân tích ${tongHop.so_hoc_sinh_co_du_lieu}/${tongHop.so_hoc_sinh} học sinh có dữ liệu`} />
          <CardBody className="grid md:grid-cols-2 gap-4">
            <div>
              <p className="text-sm font-semibold text-danger mb-2">Dạng lớp đang yếu</p>
              {tongHop.dang_yeu_chung.length === 0 ? (
                <p className="text-sm text-muted">Không có dạng chung đáng lo. 👍</p>
              ) : (
                <ul className="flex flex-col gap-1.5">
                  {tongHop.dang_yeu_chung.map((d, i) => (
                    <li key={i} className="text-sm text-ink flex items-center justify-between gap-2">
                      <span>• {d.ten}</span>
                      <span className="shrink-0">
                        <Badge tone="danger">{d.so_hs} HS</Badge>
                        {d.mastery_tb != null && (
                          <span className="text-muted text-xs ml-1">TB {d.mastery_tb}%</span>
                        )}
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
            <div>
              <p className="text-sm font-semibold text-warning mb-2">Học sinh cần chú ý</p>
              {tongHop.hoc_sinh_can_chu_y.length === 0 ? (
                <p className="text-sm text-muted">Không có học sinh nào cần lưu ý đặc biệt. 👍</p>
              ) : (
                <ul className="flex flex-col gap-1.5">
                  {tongHop.hoc_sinh_can_chu_y.map((h) => (
                    <li key={h.hoc_sinh_id} className="text-sm flex items-center justify-between gap-2">
                      <button className="text-primary hover:underline text-left"
                        onClick={() => xemHs(h.hoc_sinh_id)}>
                        {h.ho_ten}
                      </button>
                      <span className="shrink-0 flex items-center gap-1">
                        {h.so_diem_yeu > 0 && <Badge tone="danger">{h.so_diem_yeu} dạng yếu</Badge>}
                        {h.xu_huong === 'giam' && <Badge tone="warning">đang giảm</Badge>}
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </CardBody>
        </Card>
      )}

      <Card>
        <CardHeader title="Nhật ký hoàn thành"
          subtitle={`${nhatKy.length} bài đã làm xong (kèm thời gian)`} />
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
            rows={nkTrang}
            rowKey={(r) => r.session_id}
            empty="Chưa có bài nào hoàn thành."
          />
          <PhanTrang trang={trangNkAt} tong={tongTrangNk}
            onLui={() => setTrangNk((t) => Math.max(1, t - 1))}
            onToi={() => setTrangNk((t) => Math.min(tongTrangNk, t + 1))} />
        </CardBody>
      </Card>

      <Card>
        <CardHeader title="Học sinh lớp của tôi"
          subtitle={`${dsLoc.length}/${students.length} học sinh`} />
        <CardBody className="pt-0 flex flex-col gap-3">
          <div className="max-w-xs">
            <Select
              label="Lọc theo lớp"
              value={fLop}
              onChange={(e) => { setFLop(e.target.value); setTrangHs(1) }}
              options={[{ value: '', label: 'Tất cả lớp' }, ...lopOptions]}
            />
          </div>
          {loading ? (
            <p className="text-muted text-sm">Đang tải...</p>
          ) : (
            <>
              <Table
                columns={[
                  { key: 'ho_ten', header: 'Học sinh' },
                  { key: 'lop_ten', header: 'Lớp', render: (r) => r.lop_ten || '—' },
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
                rows={hsTrang}
                rowKey={(r) => r.hoc_sinh_id}
                empty="Không có học sinh phù hợp."
              />
              <PhanTrang trang={trangHsAt} tong={tongTrangHs}
                onLui={() => setTrangHs((t) => Math.max(1, t - 1))}
                onToi={() => setTrangHs((t) => Math.min(tongTrangHs, t + 1))} />
            </>
          )}
        </CardBody>
      </Card>

      {hsChon && (
        <div className="flex flex-col gap-2">
          <h3 className="text-lg font-bold text-ink">Tiến độ chi tiết: {hsChon.ho_ten}</h3>
          {dangTaiTk ? (
            <p className="text-sm text-muted">Đang tải thống kê...</p>
          ) : (
            <>
              <PhanTichNangLuc pt={ptChon} vaiTro="gv"
                onCapNhat={capNhatAi} dangCapNhat={dangCapNhatAi} />
              <ThongKeTienDo tk={tkChon} />
            </>
          )}
        </div>
      )}
    </div>
  )
}
