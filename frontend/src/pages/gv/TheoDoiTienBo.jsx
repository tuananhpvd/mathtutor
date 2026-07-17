import { useEffect, useMemo, useState } from 'react'
import { api } from '../../api'
import { Badge, Button, Card, CardBody, CardHeader, Select, Table } from '../../components/ui'
import { dinhDangThoiGian } from '../../utils/format'
import { CotThoiGian } from '../../components/ThoiGianPhanCach'
import ThongKeTienDo from '../../components/ThongKeTienDo'
import BieuDoTuan from '../../components/BieuDoTuan'
import BieuDoVung from '../../components/BieuDoVung'
import PhanTichNangLuc from '../../components/PhanTichNangLuc'
import GuiNhanXetModal from '../../components/gv/GuiNhanXetModal'
import BanDoNangLuc from '../../components/BanDoNangLuc'
import HieuQuaPhuongPhap from '../../components/gv/HieuQuaPhuongPhap'
import MucTieuPanel from '../../components/MucTieuPanel'
import BaoCaoPhuHuynh from '../../components/gv/BaoCaoPhuHuynh'

/* ── Tính thống kê lớp từ danh sách HS ───────────────────────────── */
function tinhThongKeLop(hsLop) {
  const coData = hsLop.filter((h) => (h.tien_do || []).length > 0)

  // Tỉ lệ đúng TB của mỗi HS
  function tyLeTB(h) {
    const td = h.tien_do || []
    if (!td.length) return null
    const co = td.filter((t) => t.so_bai_hoan_thanh > 0)
    if (!co.length) return null
    return co.reduce((s, t) => s + t.ty_le_dung_trung_binh, 0) / co.length
  }

  const tongBaiLam = hsLop.reduce((s, h) =>
    s + (h.tien_do || []).reduce((a, t) => a + t.so_bai_lam, 0), 0)
  const tongHoanThanh = hsLop.reduce((s, h) =>
    s + (h.tien_do || []).reduce((a, t) => a + t.so_bai_hoan_thanh, 0), 0)
  const tongThoiGian = hsLop.reduce((s, h) =>
    s + (h.tien_do || []).reduce((a, t) => a + (t.tong_thoi_gian_giay || 0), 0), 0)

  // Tỉ lệ đúng TB toàn lớp
  const tlList = coData.map(tyLeTB).filter((v) => v !== null)
  const tlTB = tlList.length ? tlList.reduce((a, b) => a + b, 0) / tlList.length : null

  // Phân bố năng lực
  const phanBo = { gioi: 0, kha: 0, tb: 0, yeu: 0, chuaLam: 0 }
  for (const h of hsLop) {
    const tl = tyLeTB(h)
    if (tl === null) phanBo.chuaLam++
    else if (tl >= 0.8) phanBo.gioi++
    else if (tl >= 0.6) phanBo.kha++
    else if (tl >= 0.4) phanBo.tb++
    else phanBo.yeu++
  }

  // Mức độ hoạt động
  const baiMoiHs = hsLop.map((h) => ({
    ...h,
    tongBai: (h.tien_do || []).reduce((s, t) => s + t.so_bai_lam, 0),
  }))
  const chuaLam = baiMoiHs.filter((h) => h.tongBai === 0)
  const tichCuc = [...baiMoiHs].sort((a, b) => b.tongBai - a.tongBai).slice(0, 3).filter((h) => h.tongBai > 0)
  const dangDo = hsLop.filter((h) =>
    (h.tien_do || []).some((t) => t.so_bai_lam > t.so_bai_hoan_thanh))

  // Thống kê theo chuyên đề
  const cdMap = {}
  for (const h of hsLop) {
    for (const t of h.tien_do || []) {
      if (!cdMap[t.chuyen_de]) cdMap[t.chuyen_de] = { baiLam: 0, hoanThanh: 0, tlList: [] }
      cdMap[t.chuyen_de].baiLam += t.so_bai_lam
      cdMap[t.chuyen_de].hoanThanh += t.so_bai_hoan_thanh
      if (t.so_bai_hoan_thanh > 0)
        cdMap[t.chuyen_de].tlList.push(t.ty_le_dung_trung_binh)
    }
  }
  const cdArr = Object.entries(cdMap).map(([ten, v]) => ({
    ten,
    baiLam: v.baiLam,
    hoanThanh: v.hoanThanh,
    tlTB: v.tlList.length ? v.tlList.reduce((a, b) => a + b, 0) / v.tlList.length : null,
  }))
  const cdNhieu = [...cdArr].sort((a, b) => b.baiLam - a.baiLam).slice(0, 3)
  const cdIt = [...cdArr].sort((a, b) => a.baiLam - b.baiLam).slice(0, 3)
  const cdCoTl = cdArr.filter((c) => c.tlTB !== null)
  const cdCaoNhat = cdCoTl.length ? [...cdCoTl].sort((a, b) => b.tlTB - a.tlTB)[0] : null
  const cdThapNhat = cdCoTl.length ? [...cdCoTl].sort((a, b) => a.tlTB - b.tlTB)[0] : null

  return {
    tongHs: hsLop.length,
    coData: coData.length,
    tongBaiLam,
    tongHoanThanh,
    tongThoiGian,
    tlTB,
    phanBo,
    tichCuc,
    chuaLam,
    dangDo,
    cdNhieu,
    cdIt,
    cdCaoNhat,
    cdThapNhat,
  }
}

/* ── Dialog thống kê lớp ─────────────────────────────────────────── */
function ThongKeLopDialog({ tenLop, stats, onDong }) {
  const { tongHs, coData, tongBaiLam, tongHoanThanh, tongThoiGian, tlTB,
    phanBo, tichCuc, chuaLam, dangDo, cdNhieu, cdIt, cdCaoNhat, cdThapNhat } = stats

  const pct = (n) => tongHs ? Math.round((n / tongHs) * 100) : 0

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center px-4"
      style={{ background: 'rgba(0,0,0,0.45)' }}
      onMouseDown={(e) => { if (e.target === e.currentTarget) onDong() }}
    >
      <div className="bg-surface rounded-2xl shadow-2xl border border-border w-full max-w-7xl
        max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-4 sm:px-8 py-4 sm:py-5 border-b
          border-border shrink-0">
          <div>
            <p className="text-xl font-bold text-ink">Thống kê lớp {tenLop}</p>
            <p className="text-sm text-muted mt-0.5">{coData}/{tongHs} học sinh có dữ liệu</p>
          </div>
          <button onClick={onDong} className="text-muted hover:text-ink text-2xl leading-none">✕</button>
        </div>

        {/* Body — 2 cột (xếp chồng trên màn hình nhỏ) */}
        <div className="p-4 sm:p-8 grid grid-cols-1 lg:grid-cols-2 gap-6 lg:gap-8 overflow-y-auto flex-1">
          {/* Cột trái */}
          <div className="flex flex-col gap-7">
            {/* 1. Tổng quan */}
            <section>
              <p className="text-sm font-semibold text-muted uppercase tracking-wide mb-3">Tổng quan</p>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                {[
                  { label: 'Học sinh', val: tongHs },
                  { label: 'Bài đã làm', val: tongBaiLam },
                  { label: 'Hoàn thành', val: tongHoanThanh },
                  { label: 'Tỉ lệ đúng TB', val: tlTB !== null ? `${Math.round(tlTB * 100)}%` : '—' },
                  { label: 'TB bài/HS', val: tongHs ? (tongBaiLam / tongHs).toFixed(1) : '—' },
                  { label: 'Tổng thời gian', val: dinhDangThoiGian(tongThoiGian) },
                ].map((item) => (
                  <div key={item.label} className="rounded-xl bg-surface-2 px-4 py-4">
                    <p className="text-sm text-muted">{item.label}</p>
                    <p className="text-xl font-bold text-ink mt-1">{item.val}</p>
                  </div>
                ))}
              </div>
            </section>

            {/* 3. Mức độ hoạt động */}
            <section>
              <p className="text-sm font-semibold text-muted uppercase tracking-wide mb-3">Mức độ hoạt động</p>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div className="rounded-xl bg-surface-2 px-4 py-4">
                  <p className="text-sm text-muted mb-2">Tích cực nhất</p>
                  {tichCuc.length === 0
                    ? <p className="text-sm text-muted">Chưa có</p>
                    : tichCuc.map((h) => (
                      <p key={h.hoc_sinh_id} className="text-sm text-ink leading-relaxed">
                        {h.ho_ten} <span className="text-muted">({h.tongBai})</span>
                      </p>
                    ))}
                </div>
                <div className="rounded-xl bg-surface-2 px-4 py-4">
                  <p className="text-sm text-muted mb-2">Đang làm dở</p>
                  {dangDo.length === 0
                    ? <p className="text-sm text-muted">Không có</p>
                    : dangDo.slice(0, 3).map((h) => (
                      <p key={h.hoc_sinh_id} className="text-sm text-ink leading-relaxed">{h.ho_ten}</p>
                    ))}
                  {dangDo.length > 3 && <p className="text-xs text-muted mt-1">+{dangDo.length - 3} khác</p>}
                </div>
                <div className="rounded-xl bg-surface-2 px-4 py-4">
                  <p className="text-sm text-muted mb-2">Chưa làm bài nào</p>
                  {chuaLam.length === 0
                    ? <p className="text-sm text-success">Tất cả đã làm 👍</p>
                    : chuaLam.slice(0, 3).map((h) => (
                      <p key={h.hoc_sinh_id} className="text-sm text-ink leading-relaxed">{h.ho_ten}</p>
                    ))}
                  {chuaLam.length > 3 && <p className="text-xs text-muted mt-1">+{chuaLam.length - 3} khác</p>}
                </div>
              </div>
            </section>
          </div>

          {/* Cột phải */}
          <div className="flex flex-col gap-7">
            {/* 2. Phân bố năng lực */}
            <section>
              <p className="text-sm font-semibold text-muted uppercase tracking-wide mb-3">Phân bố năng lực</p>
              <div className="flex flex-col gap-3">
                {[
                  { label: 'Giỏi (≥80%)', val: phanBo.gioi, tone: 'success' },
                  { label: 'Khá (60–79%)', val: phanBo.kha, tone: 'primary' },
                  { label: 'Trung bình (40–59%)', val: phanBo.tb, tone: 'warning' },
                  { label: 'Yếu (<40%)', val: phanBo.yeu, tone: 'danger' },
                  { label: 'Chưa có dữ liệu', val: phanBo.chuaLam, tone: 'neutral' },
                ].map((r) => (
                  <div key={r.label} className="flex items-center gap-3">
                    <span className="text-sm text-ink w-40 shrink-0">{r.label}</span>
                    <div className="flex-1 bg-surface-2 rounded-full h-2.5 overflow-hidden">
                      <div
                        className={`h-2.5 rounded-full ${
                          r.tone === 'success' ? 'bg-success' :
                          r.tone === 'primary' ? 'bg-primary' :
                          r.tone === 'warning' ? 'bg-warning' :
                          r.tone === 'danger' ? 'bg-danger' : 'bg-muted'
                        }`}
                        style={{ width: `${pct(r.val)}%` }}
                      />
                    </div>
                    <span className="text-sm font-medium text-ink w-20 text-right shrink-0">
                      {r.val} ({pct(r.val)}%)
                    </span>
                  </div>
                ))}
              </div>
            </section>

            {/* 4. Chuyên đề */}
            <section>
              <p className="text-sm font-semibold text-muted uppercase tracking-wide mb-3">Chuyên đề</p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div className="rounded-xl bg-surface-2 px-4 py-4">
                  <p className="text-sm text-muted mb-2">Được học nhiều nhất</p>
                  {cdNhieu.length === 0
                    ? <p className="text-sm text-muted">Chưa có</p>
                    : cdNhieu.map((c) => (
                      <p key={c.ten} className="text-sm text-ink leading-relaxed">
                        {c.ten} <span className="text-muted">({c.baiLam})</span>
                      </p>
                    ))}
                </div>
                <div className="rounded-xl bg-surface-2 px-4 py-4">
                  <p className="text-sm text-muted mb-2">Ít được học nhất</p>
                  {cdIt.length === 0
                    ? <p className="text-sm text-muted">Chưa có</p>
                    : cdIt.map((c) => (
                      <p key={c.ten} className="text-sm text-ink leading-relaxed">
                        {c.ten} <span className="text-muted">({c.baiLam})</span>
                      </p>
                    ))}
                </div>
                <div className="rounded-xl bg-surface-2 px-4 py-4">
                  <p className="text-sm text-muted mb-2">Tỉ lệ đúng cao nhất</p>
                  {cdCaoNhat
                    ? <p className="text-sm text-ink leading-relaxed">
                        {cdCaoNhat.ten} <span className="text-success font-medium">({Math.round(cdCaoNhat.tlTB * 100)}%)</span>
                      </p>
                    : <p className="text-sm text-muted">Chưa có</p>}
                </div>
                <div className="rounded-xl bg-surface-2 px-4 py-4">
                  <p className="text-sm text-muted mb-2">Tỉ lệ đúng thấp nhất</p>
                  {cdThapNhat
                    ? <p className="text-sm text-ink leading-relaxed">
                        {cdThapNhat.ten} <span className="text-muted font-medium">({Math.round(cdThapNhat.tlTB * 100)}%)</span>
                      </p>
                    : <p className="text-sm text-muted">Chưa có</p>}
                </div>
              </div>
            </section>
          </div>
        </div>

        <div className="px-4 sm:px-8 pb-4 sm:pb-6 pt-4 flex justify-end border-t border-border shrink-0">
          <Button variant="secondary" onClick={onDong}>Đóng</Button>
        </div>
      </div>
    </div>
  )
}

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
  const [hqChon, setHqChon] = useState(null)
  const [nhipChon, setNhipChon] = useState(null)
  const [dangTaiTk, setDangTaiTk] = useState(false)
  const [dangCapNhatAi, setDangCapNhatAi] = useState(false)
  const [nhatKy, setNhatKy] = useState([])
  const [fLop, setFLop] = useState('')
  const [tongHop, setTongHop] = useState(null)
  const [trangHs, setTrangHs] = useState(1)
  const [trangNk, setTrangNk] = useState(1)
  const [nhanXetHs, setNhanXetHs] = useState(null) // {id, ho_ten} đang gửi nhận xét
  const [thongBaoOk, setThongBaoOk] = useState('')
  const [lopDialog, setLopDialog] = useState(null) // tên lớp đang xem thống kê
  const [trangLop, setTrangLop] = useState(1)
  const [gcSession, setGcSession] = useState(null) // {session_id, ho_ten} đang gắn cờ thủ công
  const [gcGhiChu, setGcGhiChu] = useState('')
  const [gcDangGui, setGcDangGui] = useState(false)
  const [banDoLopId, setBanDoLopId] = useState('') // '' = gộp mọi lớp GV phụ trách (mặc định)
  const MOI_TRANG = 5
  const MOI_TRANG_LOP = 5

  useEffect(() => {
    api
      .getProgressStudents()
      .then(setStudents)
      .catch(() => {})
      .finally(() => setLoading(false))
    api.listSessionsHoanThanh().then(setNhatKy).catch(() => {})
    api.getTongHopLop().then(setTongHop).catch(() => {})
  }, [])

  function xemHs(id) {
    setChon(id)
    setTkChon(null)
    setPtChon(null)
    setHqChon(null)
    setNhipChon(null)
    setDangTaiTk(true)
    Promise.all([api.getThongKeHocSinh(id), api.getPhanTichHocSinh(id),
                 api.getHieuQuaHocSinh(id), api.getNhipNgayHocSinh(id)])
      .then(([tk, pt, hq, nn]) => { setTkChon(tk); setPtChon(pt); setHqChon(hq); setNhipChon(nn) })
      .catch(() => {})
      .finally(() => setDangTaiTk(false))
  }

  async function capNhatAi() {
    if (!chon) return
    setDangCapNhatAi(true)
    try { setPtChon(await api.capNhatPhanTichHocSinh(chon)) } catch { /* giữ nguyên */ }
    finally { setDangCapNhatAi(false) }
  }

  async function xacNhanGanCo() {
    if (!gcSession) return
    setGcDangGui(true)
    try {
      await api.createFlag(gcSession.session_id, gcGhiChu.trim())
      setGcSession(null)
      setGcGhiChu('')
      setThongBaoOk('Đã gắn cờ — xem ở mục "Cờ theo dõi".')
      setTimeout(() => setThongBaoOk(''), 4000)
    } catch { /* bỏ qua, giữ hộp thoại để GV thử lại */ }
    finally { setGcDangGui(false) }
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

  // Danh sách lớp theo lop_id (cho bộ lọc "Bản đồ năng lực lớp" — backend cần id, không phải tên,
  // và 1 GV có thể có nhiều lớp cùng tên trùng lặp ở trường khác nên id mới xác định đúng 1 lớp).
  const lopOptionsById = useMemo(() => {
    const map = new Map()
    for (const s of students) {
      if (s.lop_id != null) map.set(s.lop_id, s.lop_ten)
    }
    return [...map.entries()]
      .sort((a, b) => (a[1] || '').localeCompare(b[1] || ''))
      .map(([id, ten]) => ({ value: String(id), label: ten }))
  }, [students])
  // GV chỉ có đúng 1 lớp → coi như đã chọn lớp đó (không cần bấm), vẫn hiện rõ tên lớp trong
  // subtitle. Suy ra thuần từ state hiện có (không setState trong effect — tránh render thừa).
  const banDoLopIdHieuLuc =
    banDoLopId || (lopOptionsById.length === 1 ? lopOptionsById[0].value : '')
  const tenLopBanDo = lopOptionsById.find((o) => o.value === banDoLopIdHieuLuc)?.label

  // Danh sách lớp kèm số HS (cho card thống kê lớp)
  const lopDsThongKe = useMemo(() => {
    const ten = [...new Set(students.map((s) => s.lop_ten).filter(Boolean))].sort()
    return ten.map((t) => ({ ten: t, soHs: students.filter((s) => s.lop_ten === t).length }))
  }, [students])
  const tongTrangLop = Math.max(1, Math.ceil(lopDsThongKe.length / MOI_TRANG_LOP))
  const lopTrang = lopDsThongKe.slice((trangLop - 1) * MOI_TRANG_LOP, trangLop * MOI_TRANG_LOP)
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
                render: (r) => <CotThoiGian iso={r.hoan_thanh_luc} />,
              },
              {
                key: 'gan_co',
                header: '',
                render: (r) => (
                  <Button size="sm" variant="secondary"
                    onClick={() => { setGcSession(r); setGcGhiChu('') }}>
                    🚩 Gắn cờ
                  </Button>
                ),
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

      <BanDoNangLuc
        taiDuLieu={() => api.getBanDoLop(banDoLopIdHieuLuc)}
        khoa={banDoLopIdHieuLuc || 'tat_ca'}
        tieu_de="Bản đồ năng lực lớp"
        subtitle={
          tenLopBanDo
            ? `Lớp ${tenLopBanDo} — nhìn 1 lần biết lớp vững/yếu ở chuyên đề × độ khó nào; ô xám = chưa đủ dữ liệu.`
            : lopOptionsById.length > 1
              ? 'Gộp phiên của mọi lớp bạn phụ trách — chọn 1 lớp cụ thể ở góc phải để xem riêng.'
              : 'Chưa được phân lớp nào.'
        }
        action={lopOptionsById.length > 0 && (
          <Select value={banDoLopIdHieuLuc} onChange={(e) => setBanDoLopId(e.target.value)}
            options={lopOptionsById.length > 1
              ? [{ value: '', label: 'Tất cả các lớp' }, ...lopOptionsById]
              : lopOptionsById}
            className="w-44 shrink-0" />
        )}
      />

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

      {lopDsThongKe.length > 0 && (
        <Card>
          <CardHeader title="Lớp của tôi" subtitle="Xem thống kê tổng hợp của từng lớp" />
          <CardBody className="pt-0 flex flex-col">
            {lopTrang.map((l) => (
              <div key={l.ten}
                className="flex items-center justify-between py-2.5 border-b border-border last:border-0">
                <div>
                  <span className="font-medium text-ink">{l.ten}</span>
                  <span className="text-sm text-muted ml-2">· {l.soHs} học sinh</span>
                </div>
                <Button size="sm" variant="primary" onClick={() => setLopDialog(l.ten)}>
                  Thống kê
                </Button>
              </div>
            ))}
            {tongTrangLop > 1 && (
              <div className="flex items-center justify-end gap-2 pt-2">
                <Button size="sm" variant="secondary"
                  disabled={trangLop <= 1} onClick={() => setTrangLop((t) => t - 1)}>Trước</Button>
                <span className="text-sm text-muted">{trangLop}/{tongTrangLop}</span>
                <Button size="sm" variant="secondary"
                  disabled={trangLop >= tongTrangLop} onClick={() => setTrangLop((t) => t + 1)}>Sau</Button>
              </div>
            )}
          </CardBody>
        </Card>
      )}

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
                      <Button size="sm" variant="secondary" onClick={() => xemHs(r.hoc_sinh_id)}>
                        Xem tiến độ
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
        <div className="flex flex-col gap-2 rounded-xl border border-primary/30 bg-primary-soft/40 p-3">
          <div className="flex items-center justify-between gap-3 flex-wrap">
            <h3 className="text-lg font-bold text-ink">Tiến độ chi tiết: {hsChon.ho_ten}</h3>
            <div className="flex items-center gap-2">
              <Button size="sm"
                onClick={() => setNhanXetHs({ id: hsChon.hoc_sinh_id, ho_ten: hsChon.ho_ten })}>
                💬 Gửi nhận xét
              </Button>
              <Button size="sm" variant="secondary" onClick={() => setChon(null)}>
                ✕ Thu gọn
              </Button>
            </div>
          </div>
          {dangTaiTk ? (
            <p className="text-sm text-muted">Đang tải thống kê...</p>
          ) : (
            <>
              <PhanTichNangLuc pt={ptChon} vaiTro="gv"
                onCapNhat={capNhatAi} dangCapNhat={dangCapNhatAi} />
              {nhipChon && (
                <BieuDoVung
                  ds={nhipChon.map((d) => ({ ...d, so: d.so_bai }))}
                  mau="var(--color-gv)"
                  donVi="bài hoàn thành"
                  tieu_de={`Nhịp học 30 ngày: ${hsChon.ho_ten}`}
                  phu_de="Số bài hoàn thành mỗi ngày — đường liền nhịp là học đều"
                />
              )}
              <BieuDoTuan data={hqChon}
                tieu_de={`Diễn biến 8 tuần gần nhất: ${hsChon.ho_ten}`} />
              <BanDoNangLuc khoa={chon} taiDuLieu={() => api.getBanDoHocSinh(chon)}
                tieu_de={`Bản đồ năng lực: ${hsChon.ho_ten}`} />
              <MucTieuPanel
                key={chon}
                tieuDe="🎯 Mục tiêu của học sinh"
                phuDe="Đặt mục tiêu cho em hoặc dùng gợi ý theo điểm yếu"
                taiDs={() => api.gvMucTieu(chon)}
                taiDeXuat={() => api.gvMucTieuDeXuat(chon)}
                taoMt={(body) => api.gvTaoMucTieu(chon, body)}
                xoaMt={api.xoaMucTieu}
              />
              <ThongKeTienDo tk={tkChon} />
            </>
          )}
        </div>
      )}

      <BaoCaoPhuHuynh students={students} />

      <HieuQuaPhuongPhap />

      {thongBaoOk && (
        <div className="rounded-lg bg-success-soft text-success text-sm px-4 py-2.5">
          ✓ {thongBaoOk}
        </div>
      )}

      {gcSession && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="bg-surface rounded-xl shadow-xl w-full max-w-md max-h-[88vh] flex flex-col">
            <div className="px-5 pt-5 pb-3 border-b border-border shrink-0">
              <h2 className="font-bold text-lg text-ink">🚩 Gắn cờ thủ công</h2>
              <p className="text-sm text-muted mt-0.5">
                {gcSession.ho_ten ? `${gcSession.ho_ten} · ` : ''}
                {gcSession.chuyen_de || `Phiên #${gcSession.session_id}`}
              </p>
            </div>
            <div className="px-5 py-4 overflow-y-auto flex-1">
              <label className="text-sm font-medium text-ink">Ghi chú (tùy chọn)</label>
              <textarea
                value={gcGhiChu}
                onChange={(e) => setGcGhiChu(e.target.value)}
                rows={3}
                placeholder="VD: Cần theo dõi thêm bài này, trao đổi với phụ huynh..."
                className="mt-1 w-full rounded-lg border border-border px-3 py-2 text-sm text-ink
                  focus:outline-none focus:ring-2 focus:ring-primary/40 resize-y"
              />
              <p className="text-xs text-muted mt-1">
                Cờ sẽ xuất hiện ở mục "Cờ theo dõi" để xử lý sau.
              </p>
            </div>
            <div className="px-5 py-4 border-t border-border flex gap-2 justify-end shrink-0">
              <Button variant="secondary" onClick={() => setGcSession(null)} disabled={gcDangGui}>
                Hủy
              </Button>
              <Button onClick={xacNhanGanCo} disabled={gcDangGui}>
                {gcDangGui ? 'Đang lưu...' : 'Gắn cờ'}
              </Button>
            </div>
          </div>
        </div>
      )}

      {nhanXetHs && (
        <GuiNhanXetModal
          hsId={nhanXetHs.id}
          hoTen={nhanXetHs.ho_ten}
          onClose={() => setNhanXetHs(null)}
          onSent={(msg) => {
            setNhanXetHs(null)
            setThongBaoOk(msg)
            setTimeout(() => setThongBaoOk(''), 4000)
          }}
        />
      )}

      {lopDialog && (() => {
        const hsLop = students.filter((s) => s.lop_ten === lopDialog)
        const stats = tinhThongKeLop(hsLop)
        return (
          <ThongKeLopDialog
            tenLop={lopDialog}
            stats={stats}
            onDong={() => setLopDialog(null)}
          />
        )
      })()}
    </div>
  )
}
