import { useEffect, useMemo, useState } from 'react'
import { api } from '../../api'
import { Badge, Button, Card, CardBody, CardHeader, Input, Select, useConfirm } from '../../components/ui'
import Formula from '../../components/Formula'

const NHAN_LOAI = { TN4PA: 'Trắc nghiệm', TNDS: 'Đúng/Sai', TLN: 'Tự luận' }
const DO_KHO_LABEL = { de: 'Dễ', tb: 'Trung bình', kho: 'Khó' }
const DO_KHO_TONE = { de: 'success', tb: 'warning', kho: 'danger' }

const LOAI_FILTER = [
  { value: '', label: 'Tất cả loại' },
  { value: 'TN4PA', label: 'Trắc nghiệm' },
  { value: 'TNDS', label: 'Đúng/Sai' },
  { value: 'TLN', label: 'Tự luận' },
]
const DO_KHO_FILTER = [
  { value: '', label: 'Mọi độ khó' },
  { value: 'de', label: 'Dễ' },
  { value: 'tb', label: 'Trung bình' },
  { value: 'kho', label: 'Khó' },
]

function renderDeBai(text) {
  if (text == null) return null
  return String(text)
    .split(/(\$[^$]+\$)/g)
    .map((p, i) =>
      p.startsWith('$') && p.endsWith('$') ? (
        <Formula key={i} latex={p.slice(1, -1)} />
      ) : (
        <span key={i}>{p}</span>
      )
    )
}

export default function GiaoNhiemVu() {
  const confirm = useConfirm()
  const [bais, setBais] = useState([])
  const [hocSinhs, setHocSinhs] = useState([])
  const [lops, setLops] = useState([])
  const [nhiemVus, setNhiemVus] = useState([])

  const [tieuDe, setTieuDe] = useState('')
  const [moTa, setMoTa] = useState('')
  const [hanChot, setHanChot] = useState('')
  const [chonBai, setChonBai] = useState(() => new Set())
  const [chonHs, setChonHs] = useState(() => new Set())
  const [fLop, setFLop] = useState('')

  // Bộ lọc & tìm kiếm câu hỏi
  const [qBai, setQBai] = useState('')
  const [filterLoai, setFilterLoai] = useState('')
  const [filterDo, setFilterDo] = useState('')
  // Accordion state
  const [openCd, setOpenCd] = useState(() => new Set())
  const [openDang, setOpenDang] = useState(() => new Set())

  const [hsDeXuat, setHsDeXuat] = useState('')
  const [deXuat, setDeXuat] = useState(null)
  const [dangDeXuat, setDangDeXuat] = useState(false)

  const [dangGui, setDangGui] = useState(false)
  const [ok, setOk] = useState('')
  const [loi, setLoi] = useState('')

  function taiNhiemVu() {
    api.gvNhiemVu().then(setNhiemVus).catch(() => {})
  }
  useEffect(() => {
    api.listProblems()
      .then((ps) => setBais((ps || []).filter((p) => p.trang_thai_duyet === 'da_duyet' && !p.bi_an)))
      .catch(() => {})
    api.gvHocSinh().then(setHocSinhs).catch(() => {})
    api.gvLop().then(setLops).catch(() => {})
    taiNhiemVu()
  }, [])

  const lopOptions = useMemo(
    () => [{ value: '', label: 'Tất cả lớp' },
      ...lops.map((l) => ({ value: String(l.id), label: l.ten }))],
    [lops]
  )
  const hsLoc = useMemo(
    () => (fLop ? hocSinhs.filter((h) => String(h.lop_id) === fLop) : hocSinhs),
    [hocSinhs, fLop]
  )
  const baiLoc = useMemo(() => {
    let result = bais
    if (filterLoai) result = result.filter((b) => b.loai_cau === filterLoai)
    if (filterDo) result = result.filter((b) => b.do_kho === filterDo)
    const kw = qBai.trim().toLowerCase()
    if (kw) result = result.filter((b) =>
      `${b.chuyen_de} ${b.dang_ten || ''} ${b.de_bai}`.toLowerCase().includes(kw))
    return result
  }, [bais, filterLoai, filterDo, qBai])

  // Phân nhóm: Chuyên đề → Dạng bài → []Problem
  const grouped = useMemo(() => {
    const g = {}
    for (const b of baiLoc) {
      const cd = b.chuyen_de
      const dang = b.dang_ten || 'Chưa phân dạng'
      if (!g[cd]) g[cd] = {}
      if (!g[cd][dang]) g[cd][dang] = []
      g[cd][dang].push(b)
    }
    return g
  }, [baiLoc])

  function toggleSet(s, setter, key) {
    const next = new Set(s)
    next.has(key) ? next.delete(key) : next.add(key)
    setter(next)
  }
  function toggle(set, setter, id) {
    const next = new Set(set)
    next.has(id) ? next.delete(id) : next.add(id)
    setter(next)
  }
  function chonNhom(items) {
    const allSel = items.every((b) => chonBai.has(b.id))
    const next = new Set(chonBai)
    allSel ? items.forEach((b) => next.delete(b.id)) : items.forEach((b) => next.add(b.id))
    setChonBai(next)
  }
  function chonCaLop() {
    const next = new Set(chonHs)
    hsLoc.forEach((h) => next.add(h.id))
    setChonHs(next)
  }

  async function layDeXuat() {
    if (!hsDeXuat) return
    setDangDeXuat(true)
    setDeXuat(null)
    try {
      setDeXuat(await api.gvDeXuatNhiemVu(Number(hsDeXuat)))
    } catch (e) {
      setLoi(e.message)
    } finally {
      setDangDeXuat(false)
    }
  }
  function themBaiDeXuat() {
    if (!deXuat) return
    const next = new Set(chonBai)
    deXuat.bai.forEach((b) => next.add(b.problem_id))
    setChonBai(next)
  }

  async function gui() {
    setLoi('')
    if (!tieuDe.trim()) { setLoi('Cần nhập tiêu đề'); return }
    if (chonBai.size === 0) { setLoi('Cần chọn ít nhất 1 bài'); return }
    if (chonHs.size === 0) { setLoi('Cần chọn ít nhất 1 học sinh'); return }
    setDangGui(true)
    try {
      const r = await api.gvTaoNhiemVu({
        tieu_de: tieuDe.trim(),
        mo_ta: moTa.trim() || null,
        han_chot: hanChot || null,
        problem_ids: [...chonBai],
        hoc_sinh_ids: [...chonHs],
      })
      setOk(`Đã giao nhiệm vụ cho ${r.so_hs} học sinh (${r.so_bai} bài).`)
      setTimeout(() => setOk(''), 4000)
      setTieuDe(''); setMoTa(''); setHanChot('')
      setChonBai(new Set()); setChonHs(new Set()); setDeXuat(null)
      taiNhiemVu()
    } catch (e) {
      setLoi(e.message)
    } finally {
      setDangGui(false)
    }
  }

  async function xoa(nv) {
    if (!await confirm(`Xóa nhiệm vụ "${nv.tieu_de}"?`)) return
    try { await api.gvXoaNhiemVu(nv.id); taiNhiemVu() } catch (e) { setLoi(e.message) }
  }

  return (
    <div className="flex flex-col gap-4">
      <Card>
        <CardHeader title="Tạo nhiệm vụ" subtitle="Giao bài cho học sinh / cả lớp, có hạn nộp" />
        <CardBody className="flex flex-col gap-4">
          <div className="grid sm:grid-cols-3 gap-3">
            <Input label="Tiêu đề" value={tieuDe} onChange={(e) => setTieuDe(e.target.value)}
              placeholder="VD: Luyện cực trị cuối tuần" />
            <Input label="Hạn nộp (tùy chọn)" type="date" value={hanChot}
              onChange={(e) => setHanChot(e.target.value)} />
            <Input label="Mô tả (tùy chọn)" value={moTa} onChange={(e) => setMoTa(e.target.value)}
              placeholder="Ghi chú cho học sinh" />
          </div>

          {/* Gợi ý theo điểm yếu */}
          <div className="rounded-xl border border-border bg-surface-2/40 p-3 flex flex-col gap-2">
            <p className="text-sm font-semibold text-ink">💡 Gợi ý bài theo điểm yếu</p>
            <div className="flex flex-wrap items-end gap-2">
              <div className="min-w-[200px]">
                <Select label="Chọn học sinh để gợi ý" value={hsDeXuat}
                  onChange={(e) => setHsDeXuat(e.target.value)}
                  options={[{ value: '', label: '— Chọn học sinh —' },
                    ...hocSinhs.map((h) => ({ value: String(h.id), label: h.ho_ten }))]} />
              </div>
              <Button size="sm" variant="secondary" onClick={layDeXuat}
                disabled={!hsDeXuat || dangDeXuat}>
                {dangDeXuat ? 'Đang lấy...' : 'Lấy gợi ý'}
              </Button>
              {deXuat && deXuat.bai.length > 0 && (
                <Button size="sm" onClick={themBaiDeXuat}>
                  + Thêm {deXuat.bai.length} bài gợi ý
                </Button>
              )}
            </div>
            {deXuat && (
              deXuat.bai.length === 0 ? (
                <p className="text-xs text-muted">
                  Chưa có bài gợi ý phù hợp (HS chưa đủ dữ liệu điểm yếu, hoặc đã làm hết bài cùng dạng).
                </p>
              ) : (
                <p className="text-xs text-muted">
                  Dạng yếu: {deXuat.dang_yeu.join(', ') || '—'} · {deXuat.bai.length} bài đề xuất.
                </p>
              )
            )}
          </div>

          <div className="grid lg:grid-cols-5 gap-4">
            {/* ===== CHỌN BÀI ===== */}
            <div className="lg:col-span-3 flex flex-col gap-2">
              <div className="flex items-center justify-between gap-2">
                <p className="text-sm font-semibold text-ink">
                  Chọn câu hỏi
                  {chonBai.size > 0 && (
                    <span className="ml-1.5 text-primary">({chonBai.size} đã chọn)</span>
                  )}
                </p>
                {chonBai.size > 0 && (
                  <button onClick={() => setChonBai(new Set())}
                    className="text-xs text-danger hover:underline shrink-0">
                    Bỏ chọn tất cả
                  </button>
                )}
              </div>

              {/* Bộ lọc nhanh */}
              <div className="flex flex-wrap gap-1.5 items-center">
                {LOAI_FILTER.map(({ value, label }) => (
                  <button key={value} onClick={() => setFilterLoai(value)}
                    className={`px-2.5 py-0.5 rounded-full text-xs font-semibold border transition-colors ${
                      filterLoai === value
                        ? 'bg-primary text-white border-primary'
                        : 'bg-surface text-ink border-border hover:border-primary'
                    }`}>
                    {label}
                  </button>
                ))}
                <span className="text-border text-xs mx-0.5">|</span>
                {DO_KHO_FILTER.map(({ value, label }) => {
                  const active = filterDo === value
                  const tone = { de: 'text-success border-success bg-success-soft', tb: 'text-warning border-warning bg-warning-soft', kho: 'text-danger border-danger bg-danger-soft' }[value]
                  return (
                    <button key={value} onClick={() => setFilterDo(value)}
                      className={`px-2.5 py-0.5 rounded-full text-xs font-semibold border transition-colors ${
                        active ? (tone || 'bg-ink text-white border-ink') : 'bg-surface text-ink border-border hover:border-ink'
                      }`}>
                      {label}
                    </button>
                  )
                })}
                <input value={qBai} onChange={(e) => setQBai(e.target.value)}
                  placeholder="Tìm trong đề bài..."
                  className="ml-auto rounded-md border border-border px-2 py-0.5 text-xs w-36 focus:outline-none focus:ring-1 focus:ring-primary/40" />
              </div>

              {/* Accordion Chuyên đề → Dạng bài → Câu hỏi */}
              <div className="overflow-y-auto max-h-[58vh] rounded-lg border border-border flex flex-col divide-y divide-border">
                {Object.keys(grouped).length === 0 ? (
                  <p className="text-sm text-muted px-3 py-6 text-center">Không tìm thấy câu hỏi nào.</p>
                ) : Object.entries(grouped).map(([cd, dangs]) => {
                  const allInCd = Object.values(dangs).flat()
                  const soChonCd = allInCd.filter((b) => chonBai.has(b.id)).length
                  const allSelCd = soChonCd === allInCd.length
                  const isOpenCd = openCd.has(cd)

                  return (
                    <div key={cd}>
                      {/* Header chuyên đề */}
                      <div
                        className="flex items-center gap-2 px-3 py-2.5 bg-primary-soft cursor-pointer select-none hover:bg-primary-soft/80 transition-colors"
                        onClick={() => toggleSet(openCd, setOpenCd, cd)}
                      >
                        <span className="text-[10px] text-primary">{isOpenCd ? '▼' : '▶'}</span>
                        <span className="text-sm font-bold text-primary flex-1 min-w-0 truncate">{cd}</span>
                        <span className="text-xs text-muted shrink-0">
                          {soChonCd > 0 ? <><b className="text-primary">{soChonCd}</b>/</> : ''}{allInCd.length} câu
                        </span>
                        <button
                          onClick={(e) => { e.stopPropagation(); chonNhom(allInCd) }}
                          className="text-[11px] text-primary shrink-0 hover:underline px-1 font-medium">
                          {allSelCd ? 'Bỏ chọn' : 'Chọn tất cả'}
                        </button>
                      </div>

                      {isOpenCd && Object.entries(dangs).map(([dang, items]) => {
                        const key = `${cd}::${dang}`
                        const soChonDang = items.filter((b) => chonBai.has(b.id)).length
                        const allSelDang = soChonDang === items.length
                        const isOpenDang = openDang.has(key)

                        return (
                          <div key={key} className="border-t border-border/60">
                            {/* Header dạng bài */}
                            <div
                              className="flex items-center gap-2 pl-6 pr-3 py-2 bg-surface-2 cursor-pointer select-none hover:bg-surface-2/80 transition-colors"
                              onClick={() => toggleSet(openDang, setOpenDang, key)}
                            >
                              <span className="text-[10px] text-muted">{isOpenDang ? '▼' : '▶'}</span>
                              <span className="text-sm font-semibold text-ink flex-1 min-w-0 truncate">{dang}</span>
                              <span className="text-xs text-muted shrink-0">
                                {soChonDang > 0 ? <><b className="text-primary">{soChonDang}</b>/</> : ''}{items.length} câu
                              </span>
                              <button
                                onClick={(e) => { e.stopPropagation(); chonNhom(items) }}
                                className="text-[11px] text-primary shrink-0 hover:underline px-1 font-medium">
                                {allSelDang ? 'Bỏ chọn' : 'Chọn tất cả'}
                              </button>
                            </div>

                            {/* Danh sách câu hỏi đầy đủ */}
                            {isOpenDang && (
                              <div className="divide-y divide-border/40 bg-surface">
                                {items.map((b) => (
                                  <label key={b.id}
                                    className={`flex gap-3 pl-8 pr-4 py-3 cursor-pointer transition-colors hover:bg-surface-2 ${
                                      chonBai.has(b.id) ? 'bg-primary-soft/20' : ''
                                    }`}>
                                    <input type="checkbox" checked={chonBai.has(b.id)}
                                      onChange={() => toggle(chonBai, setChonBai, b.id)}
                                      className="mt-0.5 shrink-0 accent-[var(--color-primary)]" />
                                    <div className="flex-1 min-w-0">
                                      <div className="flex flex-wrap gap-1.5 mb-1.5">
                                        <Badge tone="primary">{NHAN_LOAI[b.loai_cau] || b.loai_cau}</Badge>
                                        <Badge tone={DO_KHO_TONE[b.do_kho] || 'primary'}>
                                          {DO_KHO_LABEL[b.do_kho] || b.do_kho}
                                        </Badge>
                                        {b.pham_vi === 'rieng_tu' && (
                                          <Badge tone="neutral">Riêng tư</Badge>
                                        )}
                                      </div>
                                      <p className="text-sm text-ink leading-relaxed">
                                        {renderDeBai(b.de_bai)}
                                      </p>
                                      {/* Phương án A/B/C/D cho TN4PA */}
                                      {b.loai_cau === 'TN4PA' && b.meta?.phuong_an && (
                                        <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1">
                                          {Object.entries(b.meta.phuong_an).map(([k, v]) => (
                                            <span key={k} className="text-xs text-ink">
                                              <span className="font-semibold text-primary">{k}.</span>{' '}
                                              {renderDeBai(v)}
                                            </span>
                                          ))}
                                        </div>
                                      )}
                                      {/* Các ý a/b/c/d cho TNDS */}
                                      {b.loai_cau === 'TNDS' && b.meta?.y && (
                                        <div className="mt-2 flex flex-col gap-0.5">
                                          {b.meta.y.map((item) => (
                                            <span key={item.ky_hieu} className="text-xs text-ink">
                                              <span className="font-semibold text-primary">{item.ky_hieu})</span>{' '}
                                              {renderDeBai(item.noi_dung_y)}
                                            </span>
                                          ))}
                                        </div>
                                      )}
                                    </div>
                                  </label>
                                ))}
                              </div>
                            )}
                          </div>
                        )
                      })}
                    </div>
                  )
                })}
              </div>
            </div>

            {/* ===== CHỌN HỌC SINH ===== */}
            <div className="lg:col-span-2 flex flex-col gap-2">
              <div className="flex items-center justify-between gap-2">
                <p className="text-sm font-semibold text-ink">Chọn học sinh ({chonHs.size})</p>
                <div className="flex items-center gap-2">
                  <select value={fLop} onChange={(e) => setFLop(e.target.value)}
                    className="rounded-md border border-border px-2 py-1 text-xs focus:outline-none focus:ring-1 focus:ring-primary/40">
                    {lopOptions.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
                  </select>
                  <Button size="sm" variant="secondary" onClick={chonCaLop}>Chọn cả lớp</Button>
                </div>
              </div>
              <div className="overflow-y-auto max-h-[58vh] rounded-lg border border-border divide-y divide-border">
                {hsLoc.length === 0 ? (
                  <p className="text-sm text-muted px-3 py-4">Không có học sinh.</p>
                ) : hsLoc.map((h) => (
                  <label key={h.id}
                    className="flex items-center gap-2 px-3 py-2 hover:bg-surface-2 cursor-pointer">
                    <input type="checkbox" checked={chonHs.has(h.id)}
                      onChange={() => toggle(chonHs, setChonHs, h.id)} />
                    <span className="text-sm text-ink flex-1">{h.ho_ten}</span>
                    {h.trang_thai === 'khoa' && <Badge tone="danger">Khóa</Badge>}
                  </label>
                ))}
              </div>
            </div>
          </div>

          {loi && <p className="text-sm text-danger">{loi}</p>}
          {ok && <p className="text-sm text-success">✓ {ok}</p>}
          <div>
            <Button onClick={gui} disabled={dangGui}>
              {dangGui ? 'Đang giao...' : 'Giao nhiệm vụ'}
            </Button>
          </div>
        </CardBody>
      </Card>

      <Card>
        <CardHeader title="Nhiệm vụ đã giao" subtitle={`${nhiemVus.length} nhiệm vụ`} />
        <CardBody className="flex flex-col gap-3">
          {nhiemVus.length === 0 ? (
            <p className="text-sm text-muted">Chưa giao nhiệm vụ nào.</p>
          ) : nhiemVus.map((nv) => (
            <div key={nv.id} className="rounded-xl border border-border px-4 py-3">
              <div className="flex items-center justify-between gap-2">
                <span className="font-semibold text-ink">{nv.tieu_de}</span>
                <Button size="sm" variant="danger" onClick={() => xoa(nv)}>Xóa</Button>
              </div>
              <p className="text-xs text-muted mt-0.5">
                {nv.so_bai} bài · {nv.so_hs} học sinh · {nv.so_hs_hoan_thanh}/{nv.so_hs} hoàn thành
                {nv.han_chot ? ` · hạn ${new Date(nv.han_chot).toLocaleDateString('vi-VN')}` : ''}
              </p>
              {nv.hoc_sinh.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {nv.hoc_sinh.map((h, i) => {
                    const xong = h.tong_bai > 0 && h.so_hoan_thanh >= h.tong_bai
                    return (
                      <Badge key={i} tone={xong ? 'success' : 'warning'}>
                        {h.ho_ten}: {h.so_hoan_thanh}/{h.tong_bai}
                      </Badge>
                    )
                  })}
                </div>
              )}
            </div>
          ))}
        </CardBody>
      </Card>
    </div>
  )
}
