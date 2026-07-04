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

  // Trộn tự động (GĐ2)
  const [tronMo, setTronMo] = useState(false)
  const [soCau, setSoCau] = useState({ I: 12, II: 4, III: 6 })
  const [tyLe, setTyLe] = useState({ de: 30, tb: 40, kho: 30 })
  const [cdChon, setCdChon] = useState([]) // [] = mọi chuyên đề
  const [dangTron, setDangTron] = useState(false)
  const [canhBao, setCanhBao] = useState([])

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
      const kq = await api.deThiTron({
        so_cau: { I: Number(soCau.I) || 0, II: Number(soCau.II) || 0, III: Number(soCau.III) || 0 },
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
    setDangLuu(true)
    try {
      await api.deThiTao({ ten, thoi_gian_phut: Number(phut) || 90, cau_theo_phan: chon })
      onXong()
    } catch (e) { setError(e.message) }
    finally { setDangLuu(false) }
  }

  const tongCau = chon.I.length + chon.II.length + chon.III.length

  return (
    <Card>
      <CardHeader title="Tạo đề mới"
        subtitle="Chọn câu ĐÃ DUYỆT từ ngân hàng của thầy/cô cho từng phần. Chuẩn 2025: 12 + 4 + 6 câu = 10 điểm, 90 phút."
        action={<Button variant="secondary" size="sm" onClick={onDong}>✕ Đóng</Button>} />
      <CardBody className="flex flex-col gap-4">
        <div className="grid sm:grid-cols-2 gap-4">
          <Input label="Tên đề" value={ten} onChange={(e) => setTen(e.target.value)}
            placeholder="VD: Đề thi thử số 1 — Khảo sát hàm số" />
          <Input label="Thời gian (phút)" type="number" min={10} max={180}
            value={phut} onChange={(e) => setPhut(e.target.value)} className="max-w-40" />
        </div>

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
                    label={`Phần ${p.ma} (${p.loai})`}
                    value={soCau[p.ma]}
                    onChange={(e) => setSoCau((s) => ({ ...s, [p.ma]: e.target.value }))} />
                ))}
                <span className="text-xs text-muted pb-2">chuẩn 2025: 12 + 4 + 6</span>
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

        {/* Tab 3 phần */}
        <div className="flex gap-2 flex-wrap">
          {PHAN.map((p) => (
            <button key={p.ma} onClick={() => setPhanMo(p.ma)}
              className={`px-3 py-1.5 rounded-md text-sm font-medium border ${
                phanMo === p.ma
                  ? 'border-primary bg-primary-soft text-primary'
                  : 'border-border text-muted hover:bg-surface-2'
              }`}>
              Phần {p.ma} · {chon[p.ma].length}/{p.chuan} câu
            </button>
          ))}
        </div>

        {PHAN.filter((p) => p.ma === phanMo).map((p) => (
          <div key={p.ma} className="flex flex-col gap-2">
            <p className="text-sm text-muted">{p.ten} ({p.diem}) — chuẩn {p.chuan} câu,
              đang chọn <b className="text-ink">{chon[p.ma].length}</b></p>
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

  useEffect(() => {
    api.deThiKetQuaLop(deId).then(setDs).catch((e) => setError(e.message))
  }, [deId])

  return (
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
                <th className="py-2 text-right font-medium">Nộp lúc</th>
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
                  <td className="py-2 text-right text-muted">
                    {r.nop_luc ? new Date(r.nop_luc + 'Z').toLocaleString('vi-VN') : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
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
  const [error, setError] = useState('')
  const [thongBao, setThongBao] = useState('')

  function tai() {
    api.deThiDs().then(setDs).catch((e) => setError(e.message))
  }
  useEffect(tai, [])

  async function doiPhatHanh(de) {
    setError('')
    try {
      await api.deThiPhatHanh(de.id, !de.phat_hanh)
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
        onXong={() => { setTaoMo(false); setThongBao('Đã tạo đề (đang ở trạng thái nháp).'); setTimeout(() => setThongBao(''), 4000); tai() }} />}

      {ketQua && <KetQuaLop deId={ketQua.id} ten={ketQua.ten} onDong={() => setKetQua(null)} />}

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
                </div>
                <div className="flex gap-2 mt-1 flex-wrap">
                  <Button size="sm" variant={de.phat_hanh ? 'warning' : 'success'}
                    onClick={() => doiPhatHanh(de)}>
                    {de.phat_hanh ? 'Thu hồi' : 'Phát hành'}
                  </Button>
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
