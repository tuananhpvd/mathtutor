/*
 * QuanLyDeThi — GV ghép đề ôn thi THPT (C1): tạo đề từ ngân hàng câu của mình,
 * phát hành/thu hồi, xem kết quả lớp. Cấu trúc chuẩn 2025: I = 12 TN4PA (0,25đ),
 * II = 4 TNDS (bậc thang tối đa 1đ), III = 6 TLN (0,5đ) — GV được ghép khác chuẩn,
 * hệ thống hiện gợi ý số câu chuẩn để đối chiếu.
 */

import { useEffect, useMemo, useState } from 'react'
import { api } from '../../api'
import { Badge, Button, Card, CardBody, CardHeader, Input } from '../../components/ui'
import Formula from '../../components/Formula'

/* ─────────────── Chọn đối tượng phát hành (Tất cả / Tùy chọn lớp+HS) ─────────────── */

function ChonDoiTuongPhatHanh({ de, onDong, onXong }) {
  const [hocSinhs, setHocSinhs] = useState([])
  const [lops, setLops] = useState([])
  const [phamVi, setPhamVi] = useState(de.pham_vi || 'tat_ca')
  const [chonHs, setChonHs] = useState(() => new Set(de.hoc_sinh_duoc_giao_ids || []))
  const [fLop, setFLop] = useState('')
  const [error, setError] = useState('')
  const [dangLuu, setDangLuu] = useState(false)

  useEffect(() => {
    api.gvHocSinh().then(setHocSinhs).catch(() => {})
    api.gvLop().then(setLops).catch(() => {})
  }, [])

  const lopOptions = useMemo(
    () => [{ value: '', label: 'Tất cả lớp' }, ...lops.map((l) => ({ value: String(l.id), label: l.ten }))],
    [lops]
  )
  const hsLoc = useMemo(
    () => (fLop ? hocSinhs.filter((h) => String(h.lop_id) === fLop) : hocSinhs),
    [hocSinhs, fLop]
  )

  function toggleHs(id) {
    setChonHs((s) => {
      const next = new Set(s)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
  }
  function chonCaLop() {
    setChonHs((s) => {
      const next = new Set(s)
      hsLoc.forEach((h) => next.add(h.id))
      return next
    })
  }

  async function luu() {
    setError('')
    if (phamVi === 'tuy_chon' && chonHs.size === 0) {
      setError('Cần chọn ít nhất 1 học sinh hoặc 1 lớp')
      return
    }
    setDangLuu(true)
    try {
      await api.deThiPhatHanh(de.id, true, phamVi, [], phamVi === 'tuy_chon' ? [...chonHs] : [])
      onXong()
    } catch (e) { setError(e.message) }
    finally { setDangLuu(false) }
  }

  return (
    <Card>
      <CardHeader title={`Phát hành: ${de.ten}`}
        subtitle="Chọn đối tượng nhận đề — mặc định phát hành cho tất cả học sinh thầy/cô chủ nhiệm."
        action={<Button variant="secondary" size="sm" onClick={onDong}>✕ Đóng</Button>} />
      <CardBody className="flex flex-col gap-3">
        <div className="flex gap-2">
          {[['tat_ca', 'Tất cả học sinh'], ['tuy_chon', 'Tùy chọn lớp / học sinh']].map(([v, nhan]) => (
            <button key={v} onClick={() => setPhamVi(v)}
              className={`px-3 py-1.5 rounded-md text-sm font-medium border ${
                phamVi === v
                  ? 'border-primary bg-primary-soft text-primary'
                  : 'border-border text-muted hover:bg-surface-2'
              }`}>
              {nhan}
            </button>
          ))}
        </div>

        {phamVi === 'tuy_chon' && (
          <div className="flex flex-col gap-2">
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
            <div className="overflow-y-auto max-h-64 rounded-lg border border-border divide-y divide-border">
              {hsLoc.length === 0 ? (
                <p className="text-sm text-muted px-3 py-4">Không có học sinh.</p>
              ) : hsLoc.map((h) => (
                <label key={h.id}
                  className="flex items-center gap-2 px-3 py-2 hover:bg-surface-2 cursor-pointer">
                  <input type="checkbox" checked={chonHs.has(h.id)} onChange={() => toggleHs(h.id)} />
                  <span className="text-sm text-ink flex-1">{h.ho_ten}</span>
                  {h.trang_thai === 'khoa' && <Badge tone="danger">Khóa</Badge>}
                </label>
              ))}
            </div>
          </div>
        )}

        {error && <p className="text-sm text-danger bg-danger-soft rounded-md px-3 py-2">{error}</p>}
        <div>
          <Button onClick={luu} disabled={dangLuu}>
            {dangLuu ? 'Đang phát hành...' : 'Phát hành'}
          </Button>
        </div>
      </CardBody>
    </Card>
  )
}

const PHAN = [
  { ma: 'I', loai: 'TN4PA', ten: 'Phần I — Trắc nghiệm ABCD', chuan: 12, diem: '0,25đ/câu' },
  { ma: 'II', loai: 'TNDS', ten: 'Phần II — Đúng/Sai 4 ý', chuan: 4, diem: 'bậc thang, tối đa 1đ/câu' },
  { ma: 'III', loai: 'TLN', ten: 'Phần III — Trả lời ngắn', chuan: 6, diem: '0,5đ/câu' },
]
const NHAN_KHO = { de: 'Dễ', tb: 'TB', kho: 'Khó' }

function renderDe(text) {
  return String(text ?? '')
    .split(/(\$[^$]+\$)/g)
    .map((p, i) =>
      p.startsWith('$') ? <Formula key={i} latex={p.slice(1, -1)} /> : <span key={i}>{p}</span>
    )
}

/* ─────────────── Form tạo đề ─────────────── */

function TaoDeForm({ onDong, onXong }) {
  const [ten, setTen] = useState('')
  const [phut, setPhut] = useState(90)
  const [nganHang, setNganHang] = useState([])
  const [chon, setChon] = useState({ I: [], II: [], III: [] })
  const [error, setError] = useState('')
  const [dangLuu, setDangLuu] = useState(false)
  const [phanMo, setPhanMo] = useState('I')

  // Chế độ Chuẩn 2025 (điểm/câu cố định) vs Tự do (GV tự bật/tắt phần + đặt điểm phần)
  const [mode, setMode] = useState('chuan') // 'chuan' | 'tu_do'
  const [phanBat, setPhanBat] = useState({ I: true, II: true, III: true })
  const [diemPhan, setDiemPhan] = useState({ I: 3, II: 4, III: 3 })

  // Trộn tự động (GĐ2)
  const [tronMo, setTronMo] = useState(false)
  const [soCau, setSoCau] = useState({ I: 12, II: 4, III: 6 })
  const [tyLe, setTyLe] = useState({ de: 30, tb: 40, kho: 30 })
  const [cdChon, setCdChon] = useState([]) // [] = mọi chuyên đề
  const [dangTron, setDangTron] = useState(false)
  const [canhBao, setCanhBao] = useState([])

  const phanHienThi = mode === 'tu_do' ? PHAN.filter((p) => phanBat[p.ma]) : PHAN
  // Nếu tab đang mở bị ẩn đi (phần vừa tắt) thì suy ra tab hiệu lực thay vì setState
  // trong effect (tránh cascading render) — click tab vẫn cập nhật phanMo bình thường.
  const phanMoHieuLuc = phanHienThi.some((p) => p.ma === phanMo)
    ? phanMo : (phanHienThi[0]?.ma ?? phanMo)

  function togglePhanBat(ma) {
    setPhanBat((s) => ({ ...s, [ma]: !s[ma] }))
    if (phanBat[ma]) setChon((c) => ({ ...c, [ma]: [] })) // tắt phần → bỏ câu đã chọn
  }

  const tongDiemTuDo = PHAN.reduce(
    (t, p) => t + (phanBat[p.ma] && chon[p.ma].length > 0 ? Number(diemPhan[p.ma]) || 0 : 0), 0
  )

  useEffect(() => {
    api.listProblems().then((ds) =>
      setNganHang(ds.filter((b) => b.trang_thai_duyet === 'da_duyet'))
    ).catch((e) => setError(e.message))
  }, [])

  const theoLoai = useMemo(() => {
    const m = { TN4PA: [], TNDS: [], TLN: [] }
    nganHang.forEach((b) => m[b.loai_cau]?.push(b))
    return m
  }, [nganHang])

  const dsChuyenDe = useMemo(
    () => [...new Set(nganHang.map((b) => b.chuyen_de).filter(Boolean))].sort(),
    [nganHang]
  )

  async function tron() {
    setError('')
    setCanhBao([])
    setDangTron(true)
    try {
      // Chế độ Tự do: phần đã TẮT luôn trộn 0 câu, dù ô nhập số câu còn giá trị cũ.
      const soCauGui = (ma) => (mode === 'tu_do' && !phanBat[ma] ? 0 : Number(soCau[ma]) || 0)
      const kq = await api.deThiTron({
        so_cau: { I: soCauGui('I'), II: soCauGui('II'), III: soCauGui('III') },
        chuyen_de: cdChon,
        ty_le_kho: { de: Number(tyLe.de) || 0, tb: Number(tyLe.tb) || 0, kho: Number(tyLe.kho) || 0 },
      })
      setChon(kq.cau_theo_phan)
      setCanhBao(kq.canh_bao || [])
    } catch (e) { setError(e.message) }
    finally { setDangTron(false) }
  }

  function doiChon(phan, id) {
    setChon((c) => {
      const co = c[phan].includes(id)
      return { ...c, [phan]: co ? c[phan].filter((x) => x !== id) : [...c[phan], id] }
    })
  }

  async function luu() {
    setError('')
    if (mode === 'tu_do') {
      if (!PHAN.some((p) => phanBat[p.ma] && chon[p.ma].length > 0)) {
        setError('Chế độ Tự do: cần bật ít nhất 1 phần và chọn câu cho phần đó')
        return
      }
      for (const p of PHAN) {
        if (phanBat[p.ma] && chon[p.ma].length > 0 && !(Number(diemPhan[p.ma]) > 0)) {
          setError(`Phần ${p.ma} đã chọn câu nhưng chưa nhập điểm hợp lệ`)
          return
        }
      }
      if (tongDiemTuDo > 10) {
        setError(`Tổng điểm các phần (${tongDiemTuDo}đ) vượt quá 10 điểm`)
        return
      }
    }
    setDangLuu(true)
    try {
      const body = { ten, thoi_gian_phut: Number(phut) || 90, cau_theo_phan: chon }
      if (mode === 'tu_do') {
        body.diem_phan = { I: Number(diemPhan.I) || 0, II: Number(diemPhan.II) || 0, III: Number(diemPhan.III) || 0 }
      }
      const r = await api.deThiTao(body)
      onXong(r.canh_bao || [])
    } catch (e) { setError(e.message) }
    finally { setDangLuu(false) }
  }

  const tongCau = chon.I.length + chon.II.length + chon.III.length

  return (
    <Card>
      <CardHeader title="Tạo đề mới"
        subtitle={mode === 'chuan'
          ? 'Chọn câu ĐÃ DUYỆT từ ngân hàng của thầy/cô cho từng phần. Chuẩn 2025: 12 + 4 + 6 câu = 10 điểm, 90 phút.'
          : 'Chế độ Tự do: chọn phần muốn đưa vào đề, tự đặt điểm mỗi phần (tổng tối đa 10 điểm).'}
        action={<Button variant="secondary" size="sm" onClick={onDong}>✕ Đóng</Button>} />
      <CardBody className="flex flex-col gap-4">
        <div className="flex gap-2">
          {[['chuan', 'Chuẩn 2025'], ['tu_do', 'Tự do']].map(([v, nhan]) => (
            <button key={v} onClick={() => setMode(v)}
              className={`px-3 py-1.5 rounded-md text-sm font-medium border ${
                mode === v
                  ? 'border-primary bg-primary-soft text-primary'
                  : 'border-border text-muted hover:bg-surface-2'
              }`}>
              {nhan}
            </button>
          ))}
        </div>

        <div className="grid sm:grid-cols-2 gap-4">
          <Input label="Tên đề" value={ten} onChange={(e) => setTen(e.target.value)}
            placeholder="VD: Đề thi thử số 1 — Khảo sát hàm số" />
          <Input label="Thời gian (phút)" type="number" min={10} max={180}
            value={phut} onChange={(e) => setPhut(e.target.value)} className="max-w-40" />
        </div>

        {mode === 'tu_do' && (
          <div className="rounded-lg border border-border bg-surface-2/60 px-4 py-3 flex flex-col gap-2.5">
            <p className="text-sm font-semibold text-ink">Chọn phần & điểm mỗi phần</p>
            {PHAN.map((p) => (
              <div key={p.ma} className="flex items-center gap-3 flex-wrap">
                <label className="inline-flex items-center gap-1.5 text-sm cursor-pointer w-48 shrink-0">
                  <input type="checkbox" className="accent-primary"
                    checked={phanBat[p.ma]} onChange={() => togglePhanBat(p.ma)} />
                  Phần {p.ma} ({p.loai})
                </label>
                <Input type="number" min={0} step={0.25} className="w-28" disabled={!phanBat[p.ma]}
                  label="Điểm phần" value={diemPhan[p.ma]}
                  onChange={(e) => setDiemPhan((d) => ({ ...d, [p.ma]: e.target.value }))} />
                <span className="text-xs text-muted">
                  {phanBat[p.ma] && chon[p.ma].length > 0
                    ? `≈ ${(Number(diemPhan[p.ma]) / chon[p.ma].length).toFixed(2)}đ/câu (${chon[p.ma].length} câu)`
                    : phanBat[p.ma] ? 'chưa chọn câu' : 'không đưa vào đề'}
                </span>
              </div>
            ))}
            <p className={`text-xs font-semibold ${tongDiemTuDo > 10 ? 'text-danger' : 'text-muted'}`}>
              Tổng điểm hiện tại: {tongDiemTuDo}đ / tối đa 10đ
              {tongDiemTuDo > 10 && ' — vượt quá, cần giảm bớt!'}
            </p>
          </div>
        )}

        {/* Trộn tự động theo ma trận (GĐ2) */}
        <div className="rounded-lg border border-border bg-surface-2/60 px-4 py-3 flex flex-col gap-3">
          <button className="flex items-center justify-between text-left"
            onClick={() => setTronMo((m) => !m)}>
            <span className="text-sm font-semibold text-ink">
              🎲 Trộn đề tự động theo ma trận
            </span>
            <span className="text-muted text-sm">{tronMo ? '▲ Thu gọn' : '▼ Mở'}</span>
          </button>
          {tronMo && (
            <>
              <div className="flex gap-3 items-end flex-wrap">
                {PHAN.map((p) => (
                  <Input key={p.ma} type="number" min={0} className="w-24"
                    disabled={mode === 'tu_do' && !phanBat[p.ma]}
                    label={`Phần ${p.ma} (${p.loai})`}
                    value={soCau[p.ma]}
                    onChange={(e) => setSoCau((s) => ({ ...s, [p.ma]: e.target.value }))} />
                ))}
                <span className="text-xs text-muted pb-2">
                  {mode === 'tu_do' ? 'phần đã tắt sẽ trộn 0 câu' : 'chuẩn 2025: 12 + 4 + 6'}
                </span>
              </div>
              <div className="flex gap-3 items-end flex-wrap">
                {[['de', 'Dễ'], ['tb', 'TB'], ['kho', 'Khó']].map(([k, nhan]) => (
                  <Input key={k} type="number" min={0} max={100} className="w-24"
                    label={`% ${nhan}`}
                    value={tyLe[k]}
                    onChange={(e) => setTyLe((t) => ({ ...t, [k]: e.target.value }))} />
                ))}
                <span className="text-xs text-muted pb-2">tỉ lệ độ khó (tương đối)</span>
              </div>
              {dsChuyenDe.length > 0 && (
                <div className="flex flex-col gap-1">
                  <p className="text-xs text-muted">
                    Giới hạn chuyên đề (không chọn gì = lấy mọi chuyên đề):
                  </p>
                  <div className="flex gap-x-4 gap-y-1 flex-wrap">
                    {dsChuyenDe.map((cd) => (
                      <label key={cd} className="inline-flex items-center gap-1.5 text-sm cursor-pointer">
                        <input type="checkbox" className="accent-primary"
                          checked={cdChon.includes(cd)}
                          onChange={() => setCdChon((c) =>
                            c.includes(cd) ? c.filter((x) => x !== cd) : [...c, cd])} />
                        {cd}
                      </label>
                    ))}
                  </div>
                </div>
              )}
              <div className="flex items-center gap-3">
                <Button size="sm" onClick={tron} disabled={dangTron}>
                  {dangTron ? 'Đang trộn...' : '🎲 Trộn ngay'}
                </Button>
                <span className="text-xs text-muted">
                  Kết quả đổ vào 3 phần bên dưới — thầy/cô xem lại, chỉnh tay từng câu rồi mới Tạo đề.
                </span>
              </div>
              {canhBao.length > 0 && (
                <div className="text-xs text-warning bg-warning-soft rounded-md px-3 py-2 flex flex-col gap-0.5">
                  {canhBao.map((c, i) => <span key={i}>⚠ {c}</span>)}
                </div>
              )}
            </>
          )}
        </div>

        {/* Tab các phần (chế độ Tự do chỉ hiện phần đã bật) */}
        {mode === 'tu_do' && phanHienThi.length === 0 && (
          <p className="text-sm text-warning bg-warning-soft rounded-md px-3 py-2">
            Chưa bật phần nào — tick chọn ít nhất 1 phần ở trên để chọn câu hỏi.
          </p>
        )}
        <div className="flex gap-2 flex-wrap">
          {phanHienThi.map((p) => (
            <button key={p.ma} onClick={() => setPhanMo(p.ma)}
              className={`px-3 py-1.5 rounded-md text-sm font-medium border ${
                phanMoHieuLuc === p.ma
                  ? 'border-primary bg-primary-soft text-primary'
                  : 'border-border text-muted hover:bg-surface-2'
              }`}>
              Phần {p.ma} · {chon[p.ma].length}{mode === 'chuan' ? `/${p.chuan}` : ''} câu
            </button>
          ))}
        </div>

        {phanHienThi.filter((p) => p.ma === phanMoHieuLuc).map((p) => (
          <div key={p.ma} className="flex flex-col gap-2">
            <p className="text-sm text-muted">
              {mode === 'chuan'
                ? <>{p.ten} ({p.diem}) — chuẩn {p.chuan} câu, đang chọn <b className="text-ink">{chon[p.ma].length}</b></>
                : <>{p.ten} — {diemPhan[p.ma]}đ/phần, đang chọn <b className="text-ink">{chon[p.ma].length}</b> câu
                    {chon[p.ma].length > 0 && <> (≈ {(Number(diemPhan[p.ma]) / chon[p.ma].length).toFixed(2)}đ/câu)</>}</>}
            </p>
            {theoLoai[p.loai].length === 0 && (
              <p className="text-sm text-warning bg-warning-soft rounded-md px-3 py-2">
                Chưa có câu {p.loai} nào đã duyệt trong ngân hàng — tạo/duyệt thêm ở mục Câu hỏi.
              </p>
            )}
            <div className="flex flex-col gap-1.5 max-h-80 overflow-y-auto pr-1">
              {theoLoai[p.loai].map((b) => (
                <label key={b.id}
                  className={`flex items-start gap-2 rounded-md border px-3 py-2 cursor-pointer text-sm ${
                    chon[p.ma].includes(b.id) ? 'border-primary bg-primary-soft' : 'border-border'
                  }`}>
                  <input type="checkbox" className="mt-1 accent-primary"
                    checked={chon[p.ma].includes(b.id)}
                    onChange={() => doiChon(p.ma, b.id)} />
                  <span className="flex-1">
                    <span className="text-xs text-muted">#{b.id} · {b.chuyen_de} ·{' '}
                      {NHAN_KHO[b.do_kho] || b.do_kho}</span>
                    <span className="block text-ink line-clamp-2">{renderDe(b.de_bai)}</span>
                  </span>
                </label>
              ))}
            </div>
          </div>
        ))}

        {error && <p className="text-sm text-danger bg-danger-soft rounded-md px-3 py-2">{error}</p>}
        <div className="flex items-center gap-3">
          <Button onClick={luu} disabled={dangLuu || !ten.trim() || tongCau === 0}>
            {dangLuu ? 'Đang lưu...' : `Tạo đề (${tongCau} câu)`}
          </Button>
          <span className="text-xs text-muted">
            Đề tạo xong ở trạng thái NHÁP — bấm "Phát hành" thì học sinh mới thấy.
          </span>
        </div>
      </CardBody>
    </Card>
  )
}

/* ─────────────── Kết quả lớp ─────────────── */

function KetQuaLop({ deId, ten, onDong }) {
  const [ds, setDs] = useState(null)
  const [error, setError] = useState('')
  const [chiTietBaiId, setChiTietBaiId] = useState(null)

  useEffect(() => {
    api.deThiKetQuaLop(deId).then(setDs).catch((e) => setError(e.message))
  }, [deId])

  return (
    <>
      <Card>
        <CardHeader title={`Kết quả: ${ten}`}
          action={<Button variant="secondary" size="sm" onClick={onDong}>✕ Đóng</Button>} />
        <CardBody>
          {error && <p className="text-sm text-danger">{error}</p>}
          {ds && ds.length === 0 && <p className="text-sm text-muted">Chưa có học sinh nào nộp bài.</p>}
          {ds && ds.length > 0 && (
            <table className="w-full text-sm border-collapse">
              <thead>
                <tr className="text-muted text-xs border-b border-border">
                  <th className="py-2 pr-3 text-left font-medium">#</th>
                  <th className="py-2 pr-3 text-left font-medium">Học sinh</th>
                  <th className="py-2 pr-3 text-right font-medium">Điểm</th>
                  <th className="py-2 pr-3 text-right font-medium">Nộp lúc</th>
                  <th className="py-2 text-right font-medium"></th>
                </tr>
              </thead>
              <tbody>
                {ds.map((r, i) => (
                  <tr key={r.bai_thi_id} className="border-b border-border/60">
                    <td className="py-2 pr-3 text-muted">{i + 1}</td>
                    <td className="py-2 pr-3 text-ink">{r.ho_ten}</td>
                    <td className="py-2 pr-3 text-right font-semibold text-ink">
                      {r.diem}/{r.diem_toi_da}
                    </td>
                    <td className="py-2 pr-3 text-right text-muted">
                      {r.nop_luc ? new Date(r.nop_luc).toLocaleString('vi-VN') : '—'}
                    </td>
                    <td className="py-2 text-right">
                      <Button size="sm" variant="ghost" onClick={() => setChiTietBaiId(r.bai_thi_id)}>
                        Xem chi tiết
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </CardBody>
      </Card>

      {chiTietBaiId && (
        <ChiTietBaiGV baiId={chiTietBaiId} onDong={() => setChiTietBaiId(null)} />
      )}
    </>
  )
}

/* ─────────────── Chi tiết bài làm của 1 HS (GV xem) ─────────────── */

function textDapAnDungGV(c) {
  const da = c.dap_an_dung || {}
  if (c.phan === 'I') return da.dap_an_dung
  if (c.phan === 'III') return da.dap_an_cuoi
  return Object.entries(da.dap_an_y || {})
    .map(([k, v]) => `${k}) ${v === 'Dung' ? 'Đ' : 'S'}`).join('  ')
}
function textDapAnNhapGV(c) {
  if (c.dap_an_nhap == null || c.dap_an_nhap === '') return '(bỏ trống)'
  if (typeof c.dap_an_nhap === 'object') {
    return Object.entries(c.dap_an_nhap)
      .map(([k, v]) => `${k}) ${v === 'Dung' ? 'Đ' : 'S'}`).join('  ') || '(bỏ trống)'
  }
  return String(c.dap_an_nhap)
}

function GoiYNhiemVu({ hocSinhId, dangId, dangTen }) {
  const [bai, setBai] = useState(null) // null = đang tải
  const [chon, setChon] = useState(() => new Set())
  const [dangGiao, setDangGiao] = useState(false)
  const [ok, setOk] = useState('')
  const [loi, setLoi] = useState('')

  useEffect(() => {
    api.gvDeXuatTheoDang(hocSinhId, dangId).then(setBai).catch((e) => { setBai([]); setLoi(e.message) })
  }, [hocSinhId, dangId])

  function toggle(id) {
    setChon((s) => {
      const next = new Set(s)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
  }

  async function giao() {
    setLoi('')
    setDangGiao(true)
    try {
      const r = await api.gvTaoNhiemVu({
        tieu_de: `Luyện lại: ${dangTen}`, mo_ta: null, han_chot: null,
        problem_ids: [...chon], hoc_sinh_ids: [hocSinhId],
      })
      setOk(`Đã giao ${r.so_bai} bài.`)
      setChon(new Set())
    } catch (e) { setLoi(e.message) }
    finally { setDangGiao(false) }
  }

  return (
    <div className="rounded-lg border border-border bg-surface-2/60 px-3 py-2.5 flex flex-col gap-2">
      {bai === null && <p className="text-xs text-muted">Đang tải bài gợi ý cùng dạng...</p>}
      {bai && bai.length === 0 && !loi && (
        <p className="text-xs text-muted">Không còn bài nào cùng dạng mà HS chưa làm để gợi ý.</p>
      )}
      {bai && bai.length > 0 && (
        <>
          <p className="text-xs font-semibold text-ink">
            Chọn bài luyện lại dạng "{dangTen}" ({chon.size} đã chọn):
          </p>
          <div className="flex flex-col gap-1 max-h-40 overflow-y-auto">
            {bai.map((b) => (
              <label key={b.problem_id} className="flex items-start gap-2 text-xs cursor-pointer">
                <input type="checkbox" className="mt-0.5 accent-primary"
                  checked={chon.has(b.problem_id)} onChange={() => toggle(b.problem_id)} />
                <span className="text-ink line-clamp-1">{b.de_bai}</span>
              </label>
            ))}
          </div>
          <div className="flex items-center gap-2 flex-wrap">
            <Button size="sm" onClick={giao} disabled={chon.size === 0 || dangGiao}>
              {dangGiao ? 'Đang giao...' : `Giao ${chon.size} bài`}
            </Button>
            {ok && <span className="text-xs text-success">✓ {ok}</span>}
          </div>
        </>
      )}
      {loi && <p className="text-xs text-danger">{loi}</p>}
    </div>
  )
}

function ChiTietBaiGV({ baiId, onDong }) {
  const [kq, setKq] = useState(null)
  const [error, setError] = useState('')
  const [goiYMo, setGoiYMo] = useState(null) // dang_id đang mở gợi ý

  useEffect(() => {
    api.deThiChiTietBaiGV(baiId).then(setKq).catch((e) => setError(e.message))
  }, [baiId])

  return (
    <Card>
      <CardHeader title={kq ? `Chi tiết bài làm: ${kq.ho_ten}` : 'Chi tiết bài làm'}
        subtitle={kq ? kq.ten_de : ''}
        action={<Button variant="secondary" size="sm" onClick={onDong}>✕ Đóng</Button>} />
      <CardBody className="flex flex-col gap-3">
        {error && <p className="text-sm text-danger bg-danger-soft rounded-md px-3 py-2">{error}</p>}
        {!kq && !error && <p className="text-sm text-muted">Đang tải...</p>}
        {kq && (
          <>
            <div className="flex items-center gap-4 flex-wrap">
              <p className="text-3xl font-bold text-primary">
                {kq.diem}<span className="text-lg text-muted">/{kq.diem_toi_da}</span>
              </p>
              {kq.nop_luc && (
                <span className="text-xs text-muted">
                  Nộp lúc {new Date(kq.nop_luc).toLocaleString('vi-VN')}
                </span>
              )}
            </div>
            <div className="flex flex-col gap-2">
              {kq.cau_list.map((c) => (
                <div key={c.de_thi_cau_id} className="rounded-lg border border-border px-4 py-3 flex flex-col gap-2">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-semibold text-ink">Câu {c.thu_tu}</span>
                    <Badge tone="neutral">Phần {c.phan}</Badge>
                    {c.dung
                      ? <Badge tone="success">✓ Đúng · +{c.diem}đ</Badge>
                      : <Badge tone="danger">
                          {c.da_tra_loi ? `✗ Sai · ${c.diem > 0 ? `+${c.diem}đ` : '0đ'}` : 'Bỏ trống · 0đ'}
                        </Badge>}
                  </div>
                  <div className="text-sm text-ink">{renderDe(c.problem.de_bai)}</div>
                  <div className="text-sm flex flex-col sm:flex-row gap-x-6 gap-y-1">
                    <span className="text-muted">HS trả lời: <b className="text-ink">{textDapAnNhapGV(c)}</b></span>
                    <span className="text-muted">Đáp án đúng: <b className="text-success">{textDapAnDungGV(c)}</b></span>
                  </div>
                  {!c.dung && c.dang_id && (
                    <div className="flex flex-col gap-2">
                      <div>
                        <Button size="sm" variant="ghost"
                          onClick={() => setGoiYMo(goiYMo === c.dang_id ? null : c.dang_id)}>
                          🎯 Giao nhiệm vụ luyện lại dạng "{c.dang_ten}"
                        </Button>
                      </div>
                      {goiYMo === c.dang_id && (
                        <GoiYNhiemVu hocSinhId={kq.hoc_sinh_id} dangId={c.dang_id} dangTen={c.dang_ten} />
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </>
        )}
      </CardBody>
    </Card>
  )
}

/* ─────────────── Trang chính ─────────────── */

export default function QuanLyDeThi() {
  const [ds, setDs] = useState(null)
  const [taoMo, setTaoMo] = useState(false)
  const [ketQua, setKetQua] = useState(null) // {id, ten}
  const [chonDoiTuong, setChonDoiTuong] = useState(null) // đề đang chọn đối tượng phát hành
  const [error, setError] = useState('')
  const [thongBao, setThongBao] = useState('')

  function tai() {
    api.deThiDs().then(setDs).catch((e) => setError(e.message))
  }
  useEffect(tai, [])

  async function thuHoi(de) {
    setError('')
    try {
      await api.deThiPhatHanh(de.id, false)
      tai()
    } catch (e) { setError(e.message) }
  }

  async function xoa(de) {
    if (!window.confirm(`Xóa đề "${de.ten}"? (Chỉ xóa được đề chưa có học sinh làm)`)) return
    setError('')
    try {
      await api.deThiXoa(de.id)
      setThongBao('Đã xóa đề.')
      setTimeout(() => setThongBao(''), 3000)
      tai()
    } catch (e) { setError(e.message) }
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <h2 className="text-2xl font-bold text-black">Đề thi thử THPT</h2>
        {!taoMo && <Button onClick={() => setTaoMo(true)}>+ Tạo đề mới</Button>}
      </div>

      {error && <p className="text-sm text-danger bg-danger-soft rounded-md px-3 py-2">{error}</p>}
      {thongBao && <p className="text-sm text-success bg-success-soft rounded-md px-3 py-2">✓ {thongBao}</p>}

      {taoMo && <TaoDeForm onDong={() => setTaoMo(false)}
        onXong={(canhBao) => {
          setTaoMo(false)
          const canhBaoText = (canhBao && canhBao.length > 0) ? ` ⚠ ${canhBao.join(' · ')}` : ''
          setThongBao(`Đã tạo đề (đang ở trạng thái nháp).${canhBaoText}`)
          setTimeout(() => setThongBao(''), canhBaoText ? 8000 : 4000)
          tai()
        }} />}

      {ketQua && <KetQuaLop deId={ketQua.id} ten={ketQua.ten} onDong={() => setKetQua(null)} />}

      {chonDoiTuong && (
        <ChonDoiTuongPhatHanh de={chonDoiTuong} onDong={() => setChonDoiTuong(null)}
          onXong={() => {
            setChonDoiTuong(null)
            setThongBao('Đã phát hành đề.')
            setTimeout(() => setThongBao(''), 3000)
            tai()
          }} />
      )}

      {!ds && <p className="text-sm text-muted">Đang tải...</p>}
      {ds && ds.length === 0 && !taoMo && (
        <Card>
          <CardBody className="py-10 text-center text-muted">
            Chưa có đề nào — bấm "Tạo đề mới" để ghép đề đầu tiên từ ngân hàng câu hỏi.
          </CardBody>
        </Card>
      )}
      {ds && ds.length > 0 && (
        <div className="grid md:grid-cols-2 gap-3">
          {ds.map((de) => (
            <Card key={de.id}>
              <CardBody className="pt-4 flex flex-col gap-2">
                <div className="flex items-center gap-2 flex-wrap">
                  <p className="font-bold text-ink flex-1">{de.ten}</p>
                  {de.phat_hanh
                    ? <Badge tone="success">Đang phát hành</Badge>
                    : <Badge tone="neutral">Nháp</Badge>}
                </div>
                <div className="flex gap-2 flex-wrap text-sm">
                  <Badge tone="primary">{de.so_cau} câu</Badge>
                  <Badge tone="neutral">{de.thoi_gian_phut} phút</Badge>
                  <Badge tone="neutral">Tối đa {de.diem_toi_da}đ</Badge>
                  <Badge tone={de.so_bai_nop > 0 ? 'warning' : 'neutral'}>
                    {de.so_bai_nop} bài nộp
                  </Badge>
                  {de.phat_hanh && de.pham_vi === 'tuy_chon' && (
                    <Badge tone="primary">
                      {(de.hoc_sinh_duoc_giao_ids || []).length} học sinh được giao
                    </Badge>
                  )}
                </div>
                <p className="text-xs text-muted">
                  Tạo: {new Date(de.tao_luc).toLocaleDateString('vi-VN')}
                  {de.phat_hanh_luc && (
                    <> · Phát hành: {new Date(de.phat_hanh_luc).toLocaleDateString('vi-VN')}</>
                  )}
                  {de.thu_hoi_luc && (
                    <> · Thu hồi: {new Date(de.thu_hoi_luc).toLocaleDateString('vi-VN')}</>
                  )}
                </p>
                <div className="flex gap-2 mt-1 flex-wrap">
                  {de.phat_hanh ? (
                    <Button size="sm" variant="warning" onClick={() => thuHoi(de)}>Thu hồi</Button>
                  ) : (
                    <Button size="sm" variant="success" onClick={() => setChonDoiTuong(de)}>
                      Phát hành
                    </Button>
                  )}
                  <Button size="sm" variant="secondary"
                    onClick={() => setKetQua({ id: de.id, ten: de.ten })}>
                    Kết quả ({de.so_bai_nop})
                  </Button>
                  {de.so_bai_nop === 0 && (
                    <Button size="sm" variant="danger" onClick={() => xoa(de)}>Xóa</Button>
                  )}
                </div>
              </CardBody>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
