import { useEffect, useMemo, useState } from 'react'
import { api } from '../api'
import { Badge, Button, Card, CardBody, CardHeader, Input, useConfirm } from './ui'

const NHAN_LOAI = { tuan: 'Theo tuần', chu_de: 'Theo chủ đề', nhieu: 'Kế hoạch' }
const NHAN_NGUON = { hs: 'Em tự đặt', gv: 'Thầy/cô đặt', he_thong: 'Gợi ý' }
const NHAN_LOAI_CAU = { TN4PA: 'Trắc nghiệm', TNDS: 'Đúng/Sai', TLN: 'Trả lời ngắn' }
const NHAN_DO_KHO = { de: 'Dễ', tb: 'Trung bình', kho: 'Khó' }
const LOAI_FILTER = [
  { value: '', label: 'Tất cả loại' }, { value: 'TN4PA', label: 'Trắc nghiệm' },
  { value: 'TNDS', label: 'Đúng/Sai' }, { value: 'TLN', label: 'Trả lời ngắn' },
]
const DO_KHO_FILTER = [
  { value: '', label: 'Mọi mức' }, { value: 'de', label: 'Dễ' },
  { value: 'tb', label: 'Trung bình' }, { value: 'kho', label: 'Khó' },
]

// Nhãn 1 dòng con: "N bài · Khó · loại · «dạng» / chuyên đề».
function nhanDong(d) {
  const p = [`${d.chi_tieu_so} bài`]
  if (d.do_kho) p.push(NHAN_DO_KHO[d.do_kho] || d.do_kho)
  if (d.loai_cau) p.push(NHAN_LOAI_CAU[d.loai_cau] || d.loai_cau)
  if (d.dang_ten) p.push(`«${d.dang_ten}»`)
  else if (d.chuyen_de) p.push(`CĐ «${d.chuyen_de}»`)
  return p.join(' · ')
}

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
 * Props: taiDs(), taiDeXuat(), taoMt(body), xoaMt(id), tieuDe, phụ đề, choPhepThem, haiCot.
 * Mục tiêu kiểu 'nhieu' gồm nhiều DÒNG con, mỗi dòng là 1 bộ lọc (dạng/loại/mức) + số lượng —
 * HS duyệt theo Chuyên đề → Dạng (thấy số câu có sẵn, KHÔNG hiện nội dung câu) rồi nhập số.
 */
export default function MucTieuPanel({
  taiDs, taiDeXuat, taoMt, xoaMt, tieuDe, phuDe, choPhepThem = true, haiCot = false,
}) {
  const confirm = useConfirm()
  const [ds, setDs] = useState([])
  const [bais, setBais] = useState([])       // ngân hàng câu (chỉ để đếm số câu mỗi nhóm)
  const [deXuat, setDeXuat] = useState(null)
  const [moForm, setMoForm] = useState(false)

  // Bộ lọc + duyệt
  const [filterLoai, setFilterLoai] = useState('')
  const [filterDo, setFilterDo] = useState('')
  const [openCd, setOpenCd] = useState(() => new Set())
  const [soNhap, setSoNhap] = useState({})   // key nhóm → số câu đang gõ
  // Các dòng đã thêm vào mục tiêu
  const [dongs, setDongs] = useState([])
  const [tenMt, setTenMt] = useState('')
  const [han, setHan] = useState('')

  const [loi, setLoi] = useState('')
  const [dangGui, setDangGui] = useState(false)

  function resetForm() {
    setDongs([]); setSoNhap({}); setTenMt(''); setHan('')
    setFilterLoai(''); setFilterDo(''); setOpenCd(new Set())
  }

  function tai() {
    taiDs().then((rows) => setDs(rows || [])).catch(() => {})
  }
  useEffect(() => {
    tai()
    // HS /problems vốn chỉ trả bài đã duyệt (không kèm trang_thai_duyet); GV /problems trả cả
    // chưa duyệt kèm trạng thái → chỉ loại bài cho_duyet/loai khi trường này CÓ mặt.
    api.listProblems()
      .then((ps) => setBais((ps || []).filter(
        (p) => (p.trang_thai_duyet == null || p.trang_thai_duyet === 'da_duyet') && !p.bi_an)))
      .catch(() => {})
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const dsSapXep = useMemo(() => {
    const chuaDat = ds.filter((mt) => !mt.da_dat).sort((a, b) => {
      if (!a.han && !b.han) return 0
      if (!a.han) return 1
      if (!b.han) return -1
      return new Date(a.han) - new Date(b.han)
    })
    return [...chuaDat, ...ds.filter((mt) => mt.da_dat)]
  }, [ds])

  // Nhóm Chuyên đề → Dạng kèm SỐ CÂU (lọc theo loại/mức đang chọn). Không hiện nội dung câu.
  const grouped = useMemo(() => {
    let bl = bais
    if (filterLoai) bl = bl.filter((b) => b.loai_cau === filterLoai)
    if (filterDo) bl = bl.filter((b) => b.do_kho === filterDo)
    const g = {}
    for (const b of bl) {
      const cd = b.chuyen_de || '(Chưa phân loại)'
      const dang = b.dang_ten || '(Chưa phân dạng)'
      g[cd] = g[cd] || {}
      g[cd][dang] = g[cd][dang] || { so: 0, dang_id: b.dang_id ?? null }
      g[cd][dang].so += 1
    }
    return g
  }, [bais, filterLoai, filterDo])

  function toggleCd(cd) {
    setOpenCd((s) => { const n = new Set(s); n.has(cd) ? n.delete(cd) : n.add(cd); return n })
  }

  // Thêm 1 dòng: gói theo dạng (dang_id) — kèm loại/mức đang lọc.
  function themDong(dang_id, dang_ten, chuyen_de) {
    const key = dang_id ? `d${dang_id}` : `c${chuyen_de}`
    const n = Number(soNhap[key] || 0)
    if (!n || n < 1) { setLoi('Nhập số câu (≥1) cho nhóm muốn thêm.'); return }
    setLoi('')
    setDongs((arr) => [...arr, {
      dang_id: dang_id || null, dang_ten: dang_id ? dang_ten : null,
      chuyen_de: dang_id ? null : chuyen_de,
      loai_cau: filterLoai || null, do_kho: filterDo || null, chi_tieu_so: n,
    }])
    setSoNhap((m) => ({ ...m, [key]: '' }))
  }
  function xoaDong(i) { setDongs((arr) => arr.filter((_, j) => j !== i)) }

  const tongBai = dongs.reduce((s, d) => s + d.chi_tieu_so, 0)

  async function layDeXuat() {
    try { setDeXuat(await taiDeXuat()) } catch (e) { setLoi(e.message) }
  }
  async function themTuGoiY(g) {
    try {
      await taoMt({ loai: g.loai, tieu_de: g.tieu_de, chi_tieu_so: g.chi_tieu_so,
        dang_id: g.dang_id, chuyen_de: g.chuyen_de })
      setDeXuat(null); tai()
    } catch (e) { setLoi(e.message) }
  }

  async function gui() {
    setLoi('')
    if (dongs.length === 0) { setLoi('Hãy thêm ít nhất một dòng mục tiêu.'); return }
    setDangGui(true)
    try {
      await taoMt({
        loai: 'nhieu', tieu_de: tenMt.trim() || null, han: han || null,
        muc: dongs.map((d) => ({
          dang_id: d.dang_id, chuyen_de: d.chuyen_de,
          loai_cau: d.loai_cau, do_kho: d.do_kho, chi_tieu_so: d.chi_tieu_so,
        })),
      })
      setMoForm(false); resetForm(); tai()
    } catch (e) { setLoi(e.message) } finally { setDangGui(false) }
  }

  // Nút tắt "Theo tuần": N bài BẤT KỲ trong 7 ngày.
  async function themTuan() {
    setDangGui(true)
    try {
      await taoMt({ loai: 'tuan', chi_tieu_so: 5 })
      setMoForm(false); resetForm(); tai()
    } catch (e) { setLoi(e.message) } finally { setDangGui(false) }
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
                <div className="flex items-center gap-2 shrink-0">
                  <Button size="sm" variant="secondary" onClick={() => themTuGoiY(g)}>+ Thêm</Button>
                  <Button size="sm" variant="secondary" onClick={() => setDeXuat(null)}>Hủy</Button>
                </div>
              </div>
            ))}
            {deXuat.length === 0 && (
              <div className="flex justify-end">
                <Button size="sm" variant="secondary" onClick={() => setDeXuat(null)}>Hủy</Button>
              </div>
            )}
          </div>
        )}

        {/* Form đặt mục tiêu nhiều dòng: duyệt Chuyên đề → Dạng, nhập số câu mỗi nhóm */}
        {moForm && (
          <div className="rounded-xl border border-border p-3 flex flex-col gap-3">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <Input label="Tên mục tiêu (tùy chọn)" value={tenMt}
                onChange={(e) => setTenMt(e.target.value)} placeholder="VD: Kế hoạch tuần này" />
              <Input label="Hạn (tùy chọn)" type="date" value={han}
                onChange={(e) => setHan(e.target.value)} />
            </div>

            {/* Bộ lọc loại câu / mức độ — áp vào số câu hiển thị + gắn vào dòng khi thêm */}
            <div className="flex flex-wrap gap-1.5 items-center">
              {LOAI_FILTER.map(({ value, label }) => (
                <button key={value} type="button" onClick={() => setFilterLoai(value)}
                  className={`px-2.5 py-0.5 rounded-full text-xs font-semibold border transition-colors ${
                    filterLoai === value ? 'bg-primary text-white border-primary'
                      : 'bg-surface text-ink border-border hover:border-primary'}`}>
                  {label}
                </button>
              ))}
              <span className="text-border text-xs mx-0.5">|</span>
              {DO_KHO_FILTER.map(({ value, label }) => (
                <button key={value} type="button" onClick={() => setFilterDo(value)}
                  className={`px-2.5 py-0.5 rounded-full text-xs font-semibold border transition-colors ${
                    filterDo === value ? 'bg-ink text-white border-ink'
                      : 'bg-surface text-ink border-border hover:border-ink'}`}>
                  {label}
                </button>
              ))}
            </div>

            {/* Accordion Chuyên đề → Dạng (hiện SỐ CÂU, không hiện nội dung) */}
            <div className="rounded-lg border border-border divide-y divide-border max-h-[46vh] overflow-y-auto">
              {Object.keys(grouped).length === 0 ? (
                <p className="text-sm text-muted px-3 py-6 text-center">Không có câu hỏi phù hợp bộ lọc.</p>
              ) : Object.entries(grouped).map(([cd, dangs]) => {
                const tongCd = Object.values(dangs).reduce((s, x) => s + x.so, 0)
                const mo = openCd.has(cd)
                return (
                  <div key={cd}>
                    <div className="flex items-center gap-2 px-3 py-2.5 bg-primary-soft cursor-pointer select-none"
                      onClick={() => toggleCd(cd)}>
                      <span className="text-[10px] text-primary">{mo ? '▼' : '▶'}</span>
                      <span className="text-sm font-bold text-primary flex-1 min-w-0 truncate">{cd}</span>
                      <span className="text-xs text-muted shrink-0">{tongCd} câu</span>
                    </div>
                    {mo && Object.entries(dangs).map(([dang, info]) => {
                      const key = info.dang_id ? `d${info.dang_id}` : `c${cd}`
                      return (
                        <div key={dang}
                          className="flex items-center gap-2 pl-7 pr-3 py-2 border-t border-border/60">
                          <span className="text-sm text-ink flex-1 min-w-0 truncate">{dang}</span>
                          <span className="text-xs text-muted shrink-0">{info.so} câu</span>
                          <input type="number" min={1} max={info.so} value={soNhap[key] || ''}
                            onChange={(e) => setSoNhap((m) => ({ ...m, [key]: e.target.value }))}
                            placeholder="số câu"
                            className="w-20 shrink-0 rounded-md border border-border px-2 py-1 text-xs focus:outline-none focus:ring-1 focus:ring-primary/40" />
                          <Button size="sm" variant="secondary"
                            onClick={() => themDong(info.dang_id, dang, cd)}>+ Thêm</Button>
                        </div>
                      )
                    })}
                  </div>
                )
              })}
            </div>

            {/* Các dòng đã thêm */}
            {dongs.length > 0 && (
              <div className="rounded-lg bg-surface-2/40 border border-border p-2.5 flex flex-col gap-1.5">
                <p className="text-xs font-semibold text-ink">
                  Dòng mục tiêu ({dongs.length}) · tổng {tongBai} bài
                </p>
                {dongs.map((d, i) => (
                  <div key={i} className="flex items-center justify-between gap-2 text-sm">
                    <span className="text-ink min-w-0 truncate">• {nhanDong(d)}</span>
                    <button onClick={() => xoaDong(i)}
                      className="text-xs text-danger hover:underline shrink-0">Xóa</button>
                  </div>
                ))}
              </div>
            )}

            <div className="flex items-center gap-2 flex-wrap">
              <Button onClick={gui} disabled={dangGui || dongs.length === 0}>
                {dangGui ? 'Đang lưu...' : 'Lưu mục tiêu'}
              </Button>
              <Button variant="secondary" onClick={themTuan} disabled={dangGui}>
                Theo tuần (7 ngày)
              </Button>
            </div>
          </div>
        )}

        {/* Danh sách mục tiêu */}
        {ds.length === 0 ? (
          <p className="text-sm text-muted">Chưa có mục tiêu nào.</p>
        ) : (
          <div className={haiCot ? 'grid grid-cols-1 lg:grid-cols-2 gap-3 items-start' : 'flex flex-col gap-3'}>
            {dsSapXep.map((mt) => (
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
                {/* Mục tiêu nhiều dòng: tiến độ từng dòng; còn lại 1 thanh tổng */}
                {mt.loai === 'nhieu' && mt.muc ? (
                  <div className="flex flex-col gap-1.5 mt-0.5">
                    {mt.muc.map((d, i) => (
                      <div key={i} className="flex items-center gap-2">
                        <span className="text-xs text-ink flex-1 min-w-0 truncate">
                          {d.da_dat ? '✅' : '•'} {nhanDong(d)}
                        </span>
                        <span className="text-xs font-medium text-muted shrink-0">
                          {d.hien_tai}/{d.chi_tieu_so}
                        </span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <ThanhTienDo hien_tai={mt.hien_tai} chi_tieu_so={mt.chi_tieu_so} da_dat={mt.da_dat} />
                )}
              </div>
            ))}
          </div>
        )}
      </CardBody>
    </Card>
  )
}
