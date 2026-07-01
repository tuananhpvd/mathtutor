import { useEffect, useMemo, useState } from 'react'
import { api } from '../api'
import { Badge, Button, Card, CardBody, CardHeader, Input, Select, useConfirm } from './ui'

const NHAN_LOAI = { tuan: 'Theo tuần', chu_de: 'Theo chủ đề' }
const NHAN_NGUON = { hs: 'Em tự đặt', gv: 'Thầy/cô đặt', he_thong: 'Gợi ý' }

function ThanhTienDo({ hien_tai, chi_tieu_so, da_dat }) {
  const pct = chi_tieu_so > 0 ? Math.min(100, Math.round((hien_tai / chi_tieu_so) * 100)) : 0
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-2 rounded-full bg-surface-2 overflow-hidden">
        <div className={`h-full ${da_dat ? 'bg-success' : 'bg-primary'}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs font-medium text-muted shrink-0">{hien_tai}/{chi_tieu_so}</span>
    </div>
  )
}

/**
 * Panel mục tiêu dùng chung cho HS và GV.
 * Props: taiDs(), taiDeXuat(), taoMt(body), xoaMt(id), tieuDe, phụ đề.
 */
export default function MucTieuPanel({ taiDs, taiDeXuat, taoMt, xoaMt, tieuDe, phuDe, choPhepThem = true }) {
  const confirm = useConfirm()
  const [ds, setDs] = useState([])
  const [danhMuc, setDanhMuc] = useState([])
  const [deXuat, setDeXuat] = useState(null)
  const [moForm, setMoForm] = useState(false)
  const [loai, setLoai] = useState('tuan')
  const [chiTieu, setChiTieu] = useState(5)
  const [dangId, setDangId] = useState('')
  const [han, setHan] = useState('')
  const [loi, setLoi] = useState('')
  const [dangGui, setDangGui] = useState(false)

  function tai() {
    taiDs().then((rows) => setDs(rows || [])).catch(() => {})
  }
  useEffect(() => {
    tai()
    api.getDanhMuc().then(setDanhMuc).catch(() => {})
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const dsSapXep = useMemo(() => {
    const chuaDat = ds.filter((mt) => !mt.da_dat).sort((a, b) => {
      if (!a.han && !b.han) return 0
      if (!a.han) return 1
      if (!b.han) return -1
      return new Date(a.han) - new Date(b.han)
    })
    const daDat = ds.filter((mt) => mt.da_dat)
    return [...chuaDat, ...daDat]
  }, [ds])

  const dangOptions = useMemo(() => {
    const opts = [{ value: '', label: '— Chọn dạng —' }]
    danhMuc.forEach((cd) =>
      (cd.dang_list || []).forEach((d) =>
        opts.push({ value: String(d.id), label: `${cd.ten} › ${d.ten}` })))
    return opts
  }, [danhMuc])

  async function layDeXuat() {
    try { setDeXuat(await taiDeXuat()) } catch (e) { setLoi(e.message) }
  }

  async function themTuGoiY(g) {
    try {
      await taoMt({
        loai: g.loai, tieu_de: g.tieu_de, chi_tieu_so: g.chi_tieu_so,
        dang_id: g.dang_id, chuyen_de: g.chuyen_de,
      })
      setDeXuat(null)
      tai()
    } catch (e) { setLoi(e.message) }
  }

  async function gui() {
    setLoi('')
    if (loai === 'chu_de' && !dangId) { setLoi('Hãy chọn một dạng'); return }
    setDangGui(true)
    try {
      await taoMt({
        loai,
        chi_tieu_so: Number(chiTieu),
        dang_id: loai === 'chu_de' ? Number(dangId) : null,
        han: han || null,
      })
      setMoForm(false); setLoai('tuan'); setChiTieu(5); setDangId(''); setHan('')
      tai()
    } catch (e) {
      setLoi(e.message)
    } finally {
      setDangGui(false)
    }
  }

  async function xoa(mt) {
    if (!await confirm('Xóa mục tiêu này?')) return
    try { await xoaMt(mt.id); tai() } catch (e) { setLoi(e.message) }
  }

  return (
    <Card>
      <CardHeader
        title={tieuDe || '🎯 Mục tiêu học tập'}
        subtitle={phuDe}
        action={choPhepThem && (
          <div className="flex gap-2">
            <Button size="sm" variant="secondary" onClick={layDeXuat}>💡 Gợi ý</Button>
            <Button size="sm" onClick={() => setMoForm((v) => !v)}>
              {moForm ? 'Đóng' : '+ Đặt mục tiêu'}
            </Button>
          </div>
        )}
      />
      <CardBody className="flex flex-col gap-3">
        {loi && <p className="text-sm text-danger">{loi}</p>}

        {/* Gợi ý */}
        {deXuat && (
          <div className="rounded-xl border border-border bg-surface-2/40 p-3 flex flex-col gap-2">
            <p className="text-sm font-semibold text-ink">Gợi ý mục tiêu</p>
            {deXuat.length === 0 ? (
              <p className="text-xs text-muted">Chưa có gợi ý phù hợp (cần thêm dữ liệu luyện tập).</p>
            ) : deXuat.map((g, i) => (
              <div key={i} className="flex items-center justify-between gap-2">
                <span className="text-sm text-ink">{g.tieu_de}</span>
                <Button size="sm" variant="secondary" onClick={() => themTuGoiY(g)}>+ Thêm</Button>
              </div>
            ))}
          </div>
        )}

        {/* Form thêm */}
        {moForm && (
          <div className="rounded-xl border border-border p-3 grid sm:grid-cols-4 gap-3 items-end">
            <Select label="Loại" value={loai} onChange={(e) => setLoai(e.target.value)}
              options={[{ value: 'tuan', label: 'Theo tuần' }, { value: 'chu_de', label: 'Theo chủ đề' }]} />
            <Input label="Số bài" type="number" min={1} value={chiTieu}
              onChange={(e) => setChiTieu(e.target.value)} />
            {loai === 'chu_de' ? (
              <Select label="Dạng" value={dangId} onChange={(e) => setDangId(e.target.value)}
                options={dangOptions} />
            ) : (
              <Input label="Hạn (tùy chọn)" type="date" value={han}
                onChange={(e) => setHan(e.target.value)} />
            )}
            <Button onClick={gui} disabled={dangGui}>
              {dangGui ? 'Đang lưu...' : 'Lưu mục tiêu'}
            </Button>
          </div>
        )}

        {/* Danh sách */}
        {ds.length === 0 ? (
          <p className="text-sm text-muted">Chưa có mục tiêu nào.</p>
        ) : dsSapXep.map((mt) => (
          <div key={mt.id} className="rounded-xl border border-border px-4 py-3 flex flex-col gap-2">
            <div className="flex items-start justify-between gap-2">
              <div className="min-w-0">
                <p className="text-sm font-medium text-ink">{mt.tieu_de}</p>
                <p className="text-xs text-muted mt-0.5 flex items-center gap-1.5 flex-wrap">
                  <Badge tone="primary">{NHAN_LOAI[mt.loai] || mt.loai}</Badge>
                  <span>{NHAN_NGUON[mt.nguon] || mt.nguon}</span>
                  {mt.han && <span>· hạn {new Date(mt.han).toLocaleDateString('vi-VN')}</span>}
                </p>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                {mt.da_dat && <Badge tone="success">✓ Đạt</Badge>}
                <button onClick={() => xoa(mt)} className="text-xs text-danger hover:underline">Xóa</button>
              </div>
            </div>
            <ThanhTienDo hien_tai={mt.hien_tai} chi_tieu_so={mt.chi_tieu_so} da_dat={mt.da_dat} />
          </div>
        ))}
      </CardBody>
    </Card>
  )
}
