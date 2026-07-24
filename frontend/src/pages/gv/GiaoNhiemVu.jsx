import { useEffect, useMemo, useState } from 'react'
import { api } from '../../api'
import { Badge, Button, Card, CardBody, CardHeader, Input, Select, useConfirm } from '../../components/ui'
import Formula from '../../components/Formula'
import { phanTachTg } from '../../utils/format'

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

export default function GiaoNhiemVu({ goiY, onGoiYDone }) {
  const confirm = useConfirm()
  const [bais, setBais] = useState([])
  const [hocSinhs, setHocSinhs] = useState([])
  const [lops, setLops] = useState([])
  const [nhiemVus, setNhiemVus] = useState([])

  // "goiY" (từ "Giao bài ngay" ở Tiến bộ học sinh) chỉ có giá trị ở LẦN MOUNT ĐẦU — trang này
  // unmount/remount mỗi lần chuyển trang (conditional render ở GiaoVienApp) nên khởi tạo state
  // thẳng từ prop ban đầu (lazy initializer), không dùng effect để set — tránh cascading render.
  const [tieuDe, setTieuDe] = useState(() => (goiY ? `Luyện thêm: ${goiY.dangTen}` : ''))
  const [moTa, setMoTa] = useState('')
  const [hanChot, setHanChot] = useState('')
  const [chonBai, setChonBai] = useState(() => new Set())
  const [chonHs, setChonHs] = useState(() => new Set(goiY ? [goiY.hocSinhId] : []))
  const [fLop, setFLop] = useState('')

  // Bộ lọc & tìm kiếm câu hỏi
  const [qBai, setQBai] = useState('')
  const [filterLoai, setFilterLoai] = useState('')
  const [filterDo, setFilterDo] = useState('')
  // Accordion state
  const [openCd, setOpenCd] = useState(() => new Set())
  const [openDang, setOpenDang] = useState(() => new Set())

  const [hsDeXuat, setHsDeXuat] = useState(() => (goiY ? String(goiY.hocSinhId) : ''))
  const [deXuat, setDeXuat] = useState(null)
  const [dangDeXuat, setDangDeXuat] = useState(false)
  // Khác null khi tới từ "Giao bài ngay" (Tiến bộ học sinh, 1 dạng yếu cụ thể) — khoá gợi ý
  // vào ĐÚNG dạng đó thay vì quét toàn bộ điểm yếu của HS.
  const [presetDang, setPresetDang] = useState(() => (goiY ? { id: goiY.dangId, ten: goiY.dangTen } : null)) // {id, ten} | null

  // Số em (trong tập ĐANG CHỌN) đã hoàn thành từng bài — nguồn để chặn giao trùng.
  // {so_hoc_sinh, theo_bai: {problem_id: so_em_da_lam}}
  const [daLam, setDaLam] = useState({ so_hoc_sinh: 0, theo_bai: {} })
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

  // Chọn HS đổi → tải lại bảng "ai đã làm bài nào". Chưa chọn em nào thì không có gì để lọc
  // (không setState đồng bộ ở đây — các hàm dưới đã tự trả 0 khi soHsChon = 0).
  useEffect(() => {
    const ids = [...chonHs]
    if (ids.length === 0) return
    let huy = false
    api.gvDemHoanThanh(ids)
      .then((d) => {
        if (huy) return
        const bang = d?.theo_bai || {}
        setDaLam(d || { so_hoc_sinh: 0, theo_bai: {} })
        // Bỏ tích bài vừa trở thành "cả nhóm đã làm" sau khi đổi tập HS — nếu không, bài đã
        // bị khóa trên màn hình vẫn nằm trong danh sách gửi đi và backend báo lỗi khó hiểu.
        setChonBai((truoc) => {
          const sau = new Set(
            [...truoc].filter((id) => (bang[id] ?? bang[String(id)] ?? 0) < ids.length)
          )
          return sau.size === truoc.size ? truoc : sau
        })
      })
      .catch(() => {})
    return () => { huy = true }
  }, [chonHs])

  // Bài mà MỌI em được chọn đều đã làm → giao lại là vô ích với cả nhóm, cấm tích.
  // (Chọn đúng 1 em thì đây chính là "bài em đó đã làm".) Bài mới một phần nhóm làm vẫn cho
  // tích nhưng có nhãn cảnh báo — GV tự quyết.
  const soHsChon = chonHs.size
  function soEmDaLam(id) {
    if (soHsChon === 0) return 0   // tránh dùng số liệu cũ của tập HS trước đó
    return daLam.theo_bai?.[id] ?? daLam.theo_bai?.[String(id)] ?? 0
  }
  function caNhomDaLam(id) { return soHsChon > 0 && soEmDaLam(id) >= soHsChon }

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
    const duoc = items.filter((b) => !caNhomDaLam(b.id))   // không tích hộ bài đã bị khóa
    const allSel = duoc.length > 0 && duoc.every((b) => chonBai.has(b.id))
    const next = new Set(chonBai)
    allSel ? duoc.forEach((b) => next.delete(b.id)) : duoc.forEach((b) => next.add(b.id))
    setChonBai(next)
  }
  function chonCaLop() {
    const next = new Set(chonHs)
    hsLoc.forEach((h) => next.add(h.id))
    setChonHs(next)
  }

  // hocSinhIdOverride/dangOverride: dùng khi gọi NGAY sau khi set state preset (state chưa kịp
  // áp dụng trong cùng tick) — xem effect áp dụng `goiY` bên dưới.
  async function layDeXuat(hocSinhIdOverride, dangOverride) {
    const hsId = hocSinhIdOverride ?? (hsDeXuat ? Number(hsDeXuat) : null)
    const dang = dangOverride !== undefined ? dangOverride : presetDang
    if (!hsId) return
    setDangDeXuat(true)
    setDeXuat(null)
    try {
      if (dang) {
        const bai = await api.gvDeXuatTheoDang(hsId, dang.id)
        setDeXuat({ dang_yeu: [dang.ten], bai })
      } else {
        setDeXuat(await api.gvDeXuatNhiemVu(hsId))
      }
    } catch (e) {
      setLoi(e.message)
    } finally {
      setDangDeXuat(false)
    }
  }

  // State ban đầu đã khoá theo `goiY` (xem lazy initializer ở trên) — effect này chỉ lo phần
  // THẬT SỰ là side effect: gọi API lấy gợi ý + báo cho GiaoVienApp đã tiêu thụ xong `goiY`.
  // Chạy đúng 1 lần lúc mount (trang này luôn mount MỚI mỗi khi điều hướng tới, xem ghi chú ở
  // khai báo state phía trên) nên không cần theo dõi goiY đổi giữa chừng.
  useEffect(() => {
    if (goiY) {
      // layDeXuat gọi setState ngay ở đầu thân hàm (trước await) — đẩy ra ngoài microtask để
      // effect không setState ĐỒNG BỘ (tránh cascading render, cùng lý do các setState khác
      // trong effect này đã được dời sang lazy initializer ở khai báo state phía trên).
      Promise.resolve().then(() => {
        layDeXuat(goiY.hocSinhId, { id: goiY.dangId, ten: goiY.dangTen })
      })
      onGoiYDone?.()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

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

  const [xemNv, setXemNv] = useState(null) // nv.id đang mở Xem
  // suaNv: {id, tieu_de, mo_ta, han_chot, chonBai: Set<number>, openCdSua, openDangSua}
  const [suaNv, setSuaNv] = useState(null)
  const [dangLuuSua, setDangLuuSua] = useState(false)

  function moSua(nv) {
    if (suaNv?.id === nv.id) { setSuaNv(null); return }
    setSuaNv({
      id: nv.id,
      tieu_de: nv.tieu_de,
      mo_ta: nv.mo_ta || '',
      han_chot: nv.han_chot ? nv.han_chot.slice(0, 10) : '',
      chonBai: new Set((nv.bai || []).map((b) => b.id)),
      openCd: new Set(),
      openDang: new Set(),
    })
  }

  function toggleSuaSet(key, field) {
    setSuaNv((s) => {
      const next = new Set(s[field])
      next.has(key) ? next.delete(key) : next.add(key)
      return { ...s, [field]: next }
    })
  }
  function toggleSuaBai(id) {
    setSuaNv((s) => {
      const next = new Set(s.chonBai)
      next.has(id) ? next.delete(id) : next.add(id)
      return { ...s, chonBai: next }
    })
  }
  function chonNhomSua(items) {
    setSuaNv((s) => {
      const allSel = items.every((b) => s.chonBai.has(b.id))
      const next = new Set(s.chonBai)
      allSel ? items.forEach((b) => next.delete(b.id)) : items.forEach((b) => next.add(b.id))
      return { ...s, chonBai: next }
    })
  }

  async function xoa(nv) {
    if (!await confirm(`Xóa nhiệm vụ "${nv.tieu_de}"?`)) return
    try { await api.gvXoaNhiemVu(nv.id); taiNhiemVu() } catch (e) { setLoi(e.message) }
  }

  async function luuSua() {
    if (!suaNv) return
    if (suaNv.chonBai.size === 0) { setLoi('Cần chọn ít nhất 1 bài'); return }
    setDangLuuSua(true)
    try {
      await api.gvCapNhatNhiemVu(suaNv.id, {
        tieu_de: suaNv.tieu_de,
        mo_ta: suaNv.mo_ta || null,
        han_chot: suaNv.han_chot || null,
        problem_ids: [...suaNv.chonBai],
      })
      setSuaNv(null)
      taiNhiemVu()
      setOk('Đã lưu thay đổi nhiệm vụ.')
      setTimeout(() => setOk(''), 3000)
    } catch (e) { setLoi(e.message) }
    finally { setDangLuuSua(false) }
  }

  return (
    <div className="flex flex-col gap-4">
      <Card>
        <CardHeader title="Tạo nhiệm vụ" subtitle="Giao bài cho học sinh / cả lớp, có hạn nộp" />
        <CardBody className="flex flex-col gap-4">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
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
            {presetDang && (
              <div className="rounded-md bg-primary-soft border border-primary/30 px-3 py-2 text-xs
                text-ink flex items-center justify-between gap-2 flex-wrap">
                <span>
                  🎯 Đến từ "Giao bài ngay" — đang khoá đúng dạng yếu <b>«{presetDang.ten}»</b>.
                </span>
                <button onClick={() => { setPresetDang(null); layDeXuat(undefined, null) }}
                  className="text-primary hover:underline shrink-0 font-medium">
                  Bỏ khoá, xem mọi điểm yếu
                </button>
              </div>
            )}
            <div className="flex flex-wrap items-end gap-2">
              <div className="min-w-[200px]">
                <Select label="Chọn học sinh để gợi ý" value={hsDeXuat}
                  onChange={(e) => { setHsDeXuat(e.target.value); setPresetDang(null) }}
                  options={[{ value: '', label: '— Chọn học sinh —' },
                    ...hocSinhs.map((h) => ({ value: String(h.id), label: h.ho_ten }))]} />
              </div>
              <Button size="sm" variant="secondary" onClick={() => layDeXuat()}
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

          <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
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

              {/* Chưa chọn HS thì không biết em nào đã làm bài nào → nhắc chọn HS trước */}
              {soHsChon === 0 ? (
                <p className="rounded-md bg-warning-soft border border-warning/30 px-3 py-2 text-xs text-ink">
                  Hãy <b>chọn học sinh trước</b> — khi đó hệ thống sẽ tự làm mờ những bài các em
                  đã hoàn thành để thầy/cô không giao trùng.
                </p>
              ) : (
                <p className="text-xs text-muted">
                  Bài <b>cả nhóm đã hoàn thành</b> bị làm mờ và không chọn được. Bài chỉ một số em
                  đã làm vẫn chọn được, có nhãn nhắc.
                </p>
              )}

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
                                {items.map((b) => {
                                  const nDaLam = soEmDaLam(b.id)
                                  const khoa = caNhomDaLam(b.id)
                                  return (
                                  <label key={b.id}
                                    title={khoa ? 'Cả nhóm đã hoàn thành bài này' : undefined}
                                    className={`flex gap-3 pl-8 pr-4 py-3 transition-colors ${
                                      khoa
                                        ? 'opacity-55 cursor-not-allowed bg-surface-2/40'
                                        : `cursor-pointer hover:bg-surface-2 ${chonBai.has(b.id) ? 'bg-primary-soft/20' : ''}`
                                    }`}>
                                    <input type="checkbox" checked={chonBai.has(b.id)}
                                      disabled={khoa}
                                      onChange={() => toggle(chonBai, setChonBai, b.id)}
                                      className="mt-0.5 shrink-0 accent-[var(--color-primary)]" />
                                    <div className="flex-1 min-w-0">
                                      <div className="flex flex-wrap gap-1.5 mb-1.5">
                                        <Badge tone="primary">{NHAN_LOAI[b.loai_cau] || b.loai_cau}</Badge>
                                        <Badge tone={DO_KHO_TONE[b.do_kho] || 'primary'}>
                                          {DO_KHO_LABEL[b.do_kho] || b.do_kho}
                                        </Badge>
                                        {/* Nêu RÕ LÝ DO bài bị mờ / cần cân nhắc, tránh GV tưởng bài biến mất */}
                                        {khoa ? (
                                          <Badge tone="success">
                                            {soHsChon === 1 ? 'Em này đã làm' : `Cả ${soHsChon} em đã làm`}
                                          </Badge>
                                        ) : nDaLam > 0 ? (
                                          <Badge tone="warning">{nDaLam}/{soHsChon} em đã làm</Badge>
                                        ) : null}
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
                                )})}
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
        <CardBody>
          {nhiemVus.length === 0 ? (
            <p className="text-sm text-muted">Chưa giao nhiệm vụ nào.</p>
          ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 items-start">
          {nhiemVus.map((nv) => (
            <div key={nv.id} className="rounded-xl border border-border px-4 py-3 flex flex-col gap-2">
              {/* Tiêu đề + nút */}
              <div className="flex items-center justify-between gap-2 flex-wrap">
                <span className="font-semibold text-ink">{nv.tieu_de}</span>
                <div className="flex gap-2 shrink-0">
                  <Button size="sm" variant="secondary"
                    onClick={() => { setXemNv(xemNv === nv.id ? null : nv.id); setSuaNv(null) }}>
                    {xemNv === nv.id ? 'Ẩn' : 'Xem'}
                  </Button>
                  <Button size="sm" variant="warning"
                    onClick={() => { moSua(nv); setXemNv(null) }}>
                    {suaNv?.id === nv.id ? 'Hủy sửa' : 'Sửa'}
                  </Button>
                  <Button size="sm" variant="danger" onClick={() => xoa(nv)}>Xóa</Button>
                </div>
              </div>

              {/* Tóm tắt */}
              <p className="flex items-center flex-wrap gap-x-1 text-xs text-muted">
                <span>{nv.so_bai} bài</span>
                <span className="font-bold text-ink">·</span>
                <span>{nv.so_hs} học sinh</span>
                <span className="font-bold text-ink">·</span>
                <span>{nv.so_hs_hoan_thanh}/{nv.so_hs} hoàn thành</span>
                {nv.han_chot && <><span className="font-bold text-ink">·</span><span>hạn {phanTachTg(nv.han_chot)?.ngay}</span></>}
                {nv.tao_luc && <><span className="font-bold text-ink">·</span><span>giao {phanTachTg(nv.tao_luc)?.ngay}</span></>}
              </p>

              {/* === XEM CHI TIẾT === */}
              {xemNv === nv.id && (
                <div className="flex flex-col gap-3 border-t border-border pt-3">
                  {/* Tiến độ học sinh */}
                  {nv.hoc_sinh.length > 0 && (
                    <div>
                      <p className="text-xs font-semibold text-ink mb-1.5">Tiến độ học sinh</p>
                      <div className="flex flex-wrap gap-1.5">
                        {nv.hoc_sinh.map((h, i) => {
                          const xong = h.tong_bai > 0 && h.so_hoan_thanh >= h.tong_bai
                          return (
                            <Badge key={i} tone={xong ? 'success' : 'warning'}>
                              {h.ho_ten}: {h.so_hoan_thanh}/{h.tong_bai}
                            </Badge>
                          )
                        })}
                      </div>
                    </div>
                  )}
                  {/* Danh sách câu hỏi */}
                  <div>
                    <p className="text-xs font-semibold text-ink mb-1.5">Câu hỏi trong nhiệm vụ ({nv.so_bai})</p>
                    <div className="rounded-lg border border-border overflow-hidden divide-y divide-border">
                      {(nv.bai || []).map((b) => (
                        <div key={b.id} className="px-4 py-3">
                          <div className="flex flex-wrap gap-1.5 mb-1.5">
                            <Badge tone="primary">{NHAN_LOAI[b.loai_cau] || b.loai_cau}</Badge>
                            <Badge tone={DO_KHO_TONE[b.do_kho] || 'primary'}>{DO_KHO_LABEL[b.do_kho] || b.do_kho}</Badge>
                            <span className="text-xs text-muted">{b.chuyen_de}{b.dang_ten ? ` › ${b.dang_ten}` : ''}</span>
                          </div>
                          <p className="text-sm text-ink leading-relaxed">{renderDeBai(b.de_bai)}</p>
                          {b.loai_cau === 'TN4PA' && b.meta?.phuong_an && (
                            <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1">
                              {Object.entries(b.meta.phuong_an).map(([k, v]) => (
                                <span key={k} className="text-xs text-ink">
                                  <span className="font-semibold text-primary">{k}.</span> {renderDeBai(v)}
                                </span>
                              ))}
                            </div>
                          )}
                          {b.loai_cau === 'TNDS' && b.meta?.y && (
                            <div className="mt-2 flex flex-col gap-0.5">
                              {b.meta.y.map((item) => (
                                <span key={item.ky_hieu} className="text-xs text-ink">
                                  <span className="font-semibold text-primary">{item.ky_hieu})</span> {renderDeBai(item.noi_dung_y)}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* === SỬA === */}
              {suaNv?.id === nv.id && (
                <div className="flex flex-col gap-3 border-t border-border pt-3">
                  {/* Form tiêu đề/mô tả/hạn */}
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                    <Input label="Tiêu đề" value={suaNv.tieu_de}
                      onChange={(e) => setSuaNv((s) => ({ ...s, tieu_de: e.target.value }))} />
                    <Input label="Mô tả" value={suaNv.mo_ta}
                      onChange={(e) => setSuaNv((s) => ({ ...s, mo_ta: e.target.value }))} />
                    <Input label="Hạn nộp" type="date" value={suaNv.han_chot}
                      onChange={(e) => setSuaNv((s) => ({ ...s, han_chot: e.target.value }))} />
                  </div>

                  {/* Accordion chọn bài (dùng lại grouped + baiLoc) */}
                  <div>
                    <div className="flex items-center justify-between mb-1.5">
                      <p className="text-xs font-semibold text-ink">
                        Câu hỏi <span className="text-primary">({suaNv.chonBai.size} đã chọn)</span>
                      </p>
                      <div className="flex gap-2 items-center">
                        {LOAI_FILTER.slice(1).map(({ value, label }) => (
                          <button key={value} onClick={() => setFilterLoai(filterLoai === value ? '' : value)}
                            className={`px-2 py-0.5 rounded-full text-xs font-semibold border transition-colors ${
                              filterLoai === value ? 'bg-primary text-white border-primary' : 'bg-surface text-ink border-border hover:border-primary'
                            }`}>{label}</button>
                        ))}
                        <input value={qBai} onChange={(e) => setQBai(e.target.value)}
                          placeholder="Tìm bài..."
                          className="rounded-md border border-border px-2 py-0.5 text-xs w-28 focus:outline-none focus:ring-1 focus:ring-primary/40" />
                      </div>
                    </div>
                    <div className="overflow-y-auto max-h-[40vh] rounded-lg border border-border flex flex-col divide-y divide-border">
                      {Object.keys(grouped).length === 0 ? (
                        <p className="text-sm text-muted px-3 py-4 text-center">Không tìm thấy câu hỏi.</p>
                      ) : Object.entries(grouped).map(([cd, dangs]) => {
                        const allInCd = Object.values(dangs).flat()
                        const soChon = allInCd.filter((b) => suaNv.chonBai.has(b.id)).length
                        const isOpen = suaNv.openCd.has(cd)
                        return (
                          <div key={cd}>
                            <div className="flex items-center gap-2 px-3 py-2 bg-primary-soft cursor-pointer select-none"
                              onClick={() => toggleSuaSet(cd, 'openCd')}>
                              <span className="text-[10px] text-primary">{isOpen ? '▼' : '▶'}</span>
                              <span className="text-sm font-bold text-primary flex-1 truncate">{cd}</span>
                              <span className="text-xs text-muted shrink-0">
                                {soChon > 0 ? <><b className="text-primary">{soChon}</b>/</> : ''}{allInCd.length}
                              </span>
                              <button onClick={(e) => { e.stopPropagation(); chonNhomSua(allInCd) }}
                                className="text-[11px] text-primary hover:underline px-1 font-medium shrink-0">
                                {allInCd.every((b) => suaNv.chonBai.has(b.id)) ? 'Bỏ chọn' : 'Chọn tất cả'}
                              </button>
                            </div>
                            {isOpen && Object.entries(dangs).map(([dang, items]) => {
                              const dKey = `${cd}::${dang}`
                              const isOpenD = suaNv.openDang.has(dKey)
                              const soChonD = items.filter((b) => suaNv.chonBai.has(b.id)).length
                              return (
                                <div key={dKey} className="border-t border-border/60">
                                  <div className="flex items-center gap-2 pl-6 pr-3 py-1.5 bg-surface-2 cursor-pointer select-none"
                                    onClick={() => toggleSuaSet(dKey, 'openDang')}>
                                    <span className="text-[10px] text-muted">{isOpenD ? '▼' : '▶'}</span>
                                    <span className="text-sm font-semibold text-ink flex-1 truncate">{dang}</span>
                                    <span className="text-xs text-muted shrink-0">
                                      {soChonD > 0 ? <><b className="text-primary">{soChonD}</b>/</> : ''}{items.length}
                                    </span>
                                    <button onClick={(e) => { e.stopPropagation(); chonNhomSua(items) }}
                                      className="text-[11px] text-primary hover:underline px-1 font-medium shrink-0">
                                      {items.every((b) => suaNv.chonBai.has(b.id)) ? 'Bỏ chọn' : 'Chọn tất cả'}
                                    </button>
                                  </div>
                                  {isOpenD && (
                                    <div className="divide-y divide-border/40">
                                      {items.map((b) => (
                                        <label key={b.id}
                                          className={`flex gap-3 pl-8 pr-4 py-2.5 cursor-pointer hover:bg-surface-2 ${
                                            suaNv.chonBai.has(b.id) ? 'bg-primary-soft/20' : ''
                                          }`}>
                                          <input type="checkbox" checked={suaNv.chonBai.has(b.id)}
                                            onChange={() => toggleSuaBai(b.id)}
                                            className="mt-0.5 shrink-0 accent-[var(--color-primary)]" />
                                          <div className="flex-1 min-w-0">
                                            <div className="flex flex-wrap gap-1.5 mb-1">
                                              <Badge tone="primary">{NHAN_LOAI[b.loai_cau] || b.loai_cau}</Badge>
                                              <Badge tone={DO_KHO_TONE[b.do_kho] || 'primary'}>{DO_KHO_LABEL[b.do_kho] || b.do_kho}</Badge>
                                            </div>
                                            <p className="text-sm text-ink leading-relaxed">{renderDeBai(b.de_bai)}</p>
                                            {b.loai_cau === 'TN4PA' && b.meta?.phuong_an && (
                                              <div className="mt-1.5 flex flex-wrap gap-x-4 gap-y-0.5">
                                                {Object.entries(b.meta.phuong_an).map(([k, v]) => (
                                                  <span key={k} className="text-xs text-ink">
                                                    <span className="font-semibold text-primary">{k}.</span> {renderDeBai(v)}
                                                  </span>
                                                ))}
                                              </div>
                                            )}
                                            {b.loai_cau === 'TNDS' && b.meta?.y && (
                                              <div className="mt-1.5 flex flex-col gap-0.5">
                                                {b.meta.y.map((item) => (
                                                  <span key={item.ky_hieu} className="text-xs text-ink">
                                                    <span className="font-semibold text-primary">{item.ky_hieu})</span> {renderDeBai(item.noi_dung_y)}
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

                  <div className="flex gap-2">
                    <Button size="sm" variant="primary" onClick={luuSua} disabled={dangLuuSua}>
                      {dangLuuSua ? 'Đang lưu...' : 'Lưu thay đổi'}
                    </Button>
                    <Button size="sm" variant="secondary" onClick={() => setSuaNv(null)}>Hủy</Button>
                  </div>
                </div>
              )}
            </div>
          ))}
          </div>
          )}
        </CardBody>
      </Card>
    </div>
  )
}
