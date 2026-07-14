import { useEffect, useMemo, useState } from 'react'
import { createPortal } from 'react-dom'
import { api } from '../../api'
import { Button, Card, CardBody, CardHeader, Select } from '../../components/ui'

/* Nhãn thân thiện phụ huynh (tránh thuật ngữ nội bộ). */
const NHAN_XU_HUONG = {
  tien_bo: '📈 Đang tiến bộ',
  giam: '📉 Có dấu hiệu giảm',
  on_dinh: '➡️ Ổn định',
  chua_du: 'Chưa đủ dữ liệu để đánh giá',
}
const NHAN_MUC = {
  manh: 'Tốt', kha: 'Khá', can_cai_thien: 'Cần cải thiện', chua_du_lieu: 'Chưa đủ dữ liệu',
}
const NHAN_TIN_CAY = { cao: 'cao', trung_binh: 'trung bình', thap: 'thấp (còn ít bài)' }

function dinhDangNgay(s) {
  if (!s) return null
  const [y, m, d] = s.split('-')
  return `${d}/${m}/${y}`
}

function KhoangText({ tuNgay, denNgay }) {
  const tu = dinhDangNgay(tuNgay)
  const den = dinhDangNgay(denNgay)
  if (!tu && !den) return <>Toàn bộ quá trình học</>
  if (tu && den) return <>Từ {tu} đến {den}</>
  if (tu) return <>Từ {tu}</>
  return <>Đến {den}</>
}

/* Một trang báo cáo của 1 HS (dùng cho cả xuất 1 HS lẫn nhiều HS cùng lúc). */
function ThanBaoCao({ bc, khoang }) {
  const { hoc_sinh, tong_quan, diem_manh, diem_yeu, theo_dang } = bc
  const tyLe = tong_quan.so_phien > 0
    ? Math.round((tong_quan.so_hoan_thanh / tong_quan.so_phien) * 100) : 0

  return (
    <div className="bao-cao-trang text-ink">
      <div className="border-b-2 border-primary pb-3 mb-4">
        <h1 className="text-xl font-bold text-primary">BÁO CÁO KẾT QUẢ HỌC TẬP</h1>
        <p className="text-sm text-muted">Môn Toán 12 — Gia sư MathTutor</p>
      </div>

      <div className="grid grid-cols-2 gap-x-6 gap-y-1 text-sm mb-4">
        <p><span className="text-muted">Học sinh:</span> <b>{hoc_sinh.ho_ten}</b></p>
        <p><span className="text-muted">Lớp:</span> <b>{hoc_sinh.lop_ten || '—'}</b></p>
        <p className="col-span-2"><span className="text-muted">Khoảng thời gian:</span>{' '}
          <b><KhoangText {...khoang} /></b></p>
      </div>

      <h2 className="font-bold text-ink mb-2">1. Tổng quan</h2>
      <div className="grid grid-cols-3 gap-3 mb-4">
        {[
          ['Số buổi học', tong_quan.so_phien],
          ['Bài hoàn thành', tong_quan.so_hoan_thanh],
          ['Tỉ lệ hoàn thành', `${tyLe}%`],
        ].map(([nhan, gt]) => (
          <div key={nhan} className="rounded-lg border border-border px-3 py-2 text-center">
            <p className="text-2xl font-bold text-ink">{gt}</p>
            <p className="text-xs text-muted">{nhan}</p>
          </div>
        ))}
      </div>
      <p className="text-sm mb-1">
        <span className="text-muted">Xu hướng gần đây:</span>{' '}
        <b>{NHAN_XU_HUONG[tong_quan.xu_huong] || '—'}</b>
      </p>
      {!tong_quan.du_lieu_du && (
        <p className="text-xs text-muted mb-3">
          (Độ tin cậy đánh giá còn {NHAN_TIN_CAY[tong_quan.do_tin_cay] || 'thấp'} — em cần luyện
          thêm bài để nhận xét chính xác hơn.)
        </p>
      )}

      <h2 className="font-bold text-ink mt-4 mb-2">2. Điểm mạnh</h2>
      {diem_manh.length === 0 ? (
        <p className="text-sm text-muted mb-3">Chưa có đủ dữ liệu để xác định điểm mạnh nổi bật.</p>
      ) : (
        <ul className="list-disc pl-5 text-sm mb-3">
          {diem_manh.map((d) => (
            <li key={d.ten}>{d.ten}{d.diem_thanh_thao != null && <> — thành thạo {d.diem_thanh_thao}%</>}</li>
          ))}
        </ul>
      )}

      <h2 className="font-bold text-ink mt-4 mb-2">3. Nội dung cần cải thiện</h2>
      {diem_yeu.length === 0 ? (
        <p className="text-sm text-muted mb-3">Không có dạng nào đang ở mức yếu — em đang học tốt!</p>
      ) : (
        <ul className="list-disc pl-5 text-sm mb-3">
          {diem_yeu.map((d) => (
            <li key={d.ten}>{d.ten}{d.diem_thanh_thao != null && <> — mới đạt {d.diem_thanh_thao}%</>}</li>
          ))}
        </ul>
      )}

      {theo_dang.length > 0 && (
        <>
          <h2 className="font-bold text-ink mt-4 mb-2">4. Chi tiết theo dạng bài</h2>
          <table className="w-full text-sm border-collapse mb-3">
            <thead>
              <tr className="border-b border-border text-muted text-xs">
                <th className="text-left py-1.5 font-medium">Dạng</th>
                <th className="text-right py-1.5 font-medium">Bài hoàn thành</th>
                <th className="text-right py-1.5 font-medium">Mức độ thành thạo</th>
                <th className="text-right py-1.5 font-medium">Đánh giá</th>
              </tr>
            </thead>
            <tbody>
              {theo_dang.map((d) => (
                <tr key={d.ten} className="border-b border-border/50">
                  <td className="py-1.5 pr-2">{d.ten}</td>
                  <td className="py-1.5 text-right">{d.so_hoan_thanh ?? 0}</td>
                  <td className="py-1.5 text-right">
                    {d.diem_thanh_thao != null ? `${d.diem_thanh_thao}%` : '—'}
                  </td>
                  <td className="py-1.5 text-right">{NHAN_MUC[d.nhan] || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}

      <p className="text-xs text-muted mt-4 pt-2 border-t border-border">
        Báo cáo do giáo viên xuất từ hệ thống MathTutor ngày{' '}
        {new Date().toLocaleDateString('vi-VN')}. Đánh giá dựa trên quá trình luyện tập của học sinh,
        mang tính tham khảo để đồng hành cùng em.
      </p>
    </div>
  )
}

/* Hộp xem trước + in. cacHs: mảng payload báo cáo (1 hoặc nhiều HS).

   Render qua PORTAL thẳng ra document.body (KHÔNG lồng trong cây React app) — lý do:
   Chrome lặp lại y hệt nội dung của mọi phần tử `position: fixed` trên TỪNG TRANG khi in,
   nên nếu vùng in nằm trong khung modal `fixed` (như trước), báo cáo dài hơn 1 trang sẽ bị
   in lặp lại chính nó, và nhiều HS sẽ dính/lồng vào nhau. Portal ra ngoài + CSS in đưa modal
   về `position: static` (luồng tài liệu bình thường) để mỗi `.bao-cao-trang` ngắt trang đúng
   theo `break-before: page`. */
function BaoCaoModal({ tieuDe, cacHs, khoang, onDong }) {
  return createPortal(
    <div className="bao-cao-overlay fixed inset-0 z-50 bg-black/50 flex items-start justify-center overflow-y-auto p-4">
      <div className="bao-cao-card bg-surface rounded-xl shadow-[var(--shadow-pop)] w-full max-w-3xl my-4">
        <div className="khong-in flex items-center justify-between gap-3 px-5 py-3 border-b border-border sticky top-0 bg-surface rounded-t-xl">
          <p className="font-bold text-ink truncate">{tieuDe}</p>
          <div className="flex items-center gap-2 shrink-0">
            <Button size="sm" onClick={() => window.print()}>🖨️ In / Lưu PDF</Button>
            <Button size="sm" variant="secondary" onClick={onDong}>Đóng</Button>
          </div>
        </div>
        <div className="bao-cao-in p-5 flex flex-col gap-8">
          {cacHs.map((hs) => (
            <ThanBaoCao key={hs.hoc_sinh.id} bc={hs} khoang={khoang} />
          ))}
        </div>
      </div>
    </div>,
    document.body
  )
}

/* Toolbar xuất báo cáo — độc lập với phần chọn HS/lọc lớp phía dưới trang. Chỉ hiện khi
   Admin đã bật cấu hình. Props: students (danh sách tiến độ đầy đủ của GV, dùng để suy ra
   danh sách lớp + HS trong từng lớp). */
export default function BaoCaoPhuHuynh({ students }) {
  const [choPhep, setChoPhep] = useState(false)
  const [lopId, setLopId] = useState('')
  const [chonHs, setChonHs] = useState(() => new Set())
  const [tuNgay, setTuNgay] = useState('')
  const [denNgay, setDenNgay] = useState('')
  const [dangTai, setDangTai] = useState(false)
  const [loi, setLoi] = useState('')
  const [ketQua, setKetQua] = useState(null) // {tieuDe, cacHs}

  useEffect(() => {
    api.getBaoCaoChoPhep().then((r) => setChoPhep(!!r.cho_phep)).catch(() => setChoPhep(false))
  }, [])

  // Danh sách lớp của GV (suy từ students — không gọi API riêng).
  const lopOptions = useMemo(() => {
    const map = new Map()
    for (const s of students) {
      if (s.lop_id != null) map.set(s.lop_id, s.lop_ten)
    }
    return [...map.entries()]
      .sort((a, b) => (a[1] || '').localeCompare(b[1] || ''))
      .map(([id, ten]) => ({ value: String(id), label: ten }))
  }, [students])

  // HS thuộc lớp đang chọn.
  const hsTrongLop = useMemo(
    () => (lopId ? students.filter((s) => String(s.lop_id) === lopId) : []),
    [students, lopId]
  )

  // Đổi lớp → mặc định chọn TẤT CẢ HS của lớp đó (trường hợp dùng nhiều nhất), GV bỏ bớt nếu cần.
  function doiLop(id) {
    setLopId(id)
    setChonHs(new Set(students.filter((s) => String(s.lop_id) === id).map((s) => s.hoc_sinh_id)))
    setLoi('')
  }

  function toggleHs(id) {
    setChonHs((s) => {
      const next = new Set(s)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
  }

  function toggleTatCa() {
    setChonHs((s) =>
      s.size === hsTrongLop.length ? new Set() : new Set(hsTrongLop.map((h) => h.hoc_sinh_id))
    )
  }

  const khoang = { tuNgay, denNgay }

  async function xuat() {
    setLoi('')
    if (chonHs.size === 0) {
      setLoi('Chọn ít nhất 1 học sinh để xuất báo cáo.')
      return
    }
    if (tuNgay && denNgay && tuNgay > denNgay) {
      setLoi('Khoảng thời gian không hợp lệ (từ ngày sau đến ngày).')
      return
    }
    setDangTai(true)
    try {
      const ds = hsTrongLop.filter((h) => chonHs.has(h.hoc_sinh_id))
      const cacHs = await Promise.all(
        ds.map((h) => api.getBaoCaoHocSinh(h.hoc_sinh_id, tuNgay, denNgay))
      )
      cacHs.sort((a, b) => a.hoc_sinh.ho_ten.localeCompare(b.hoc_sinh.ho_ten))
      const tenLop = lopOptions.find((o) => o.value === lopId)?.label || ''
      const tieuDe = cacHs.length === 1
        ? `Báo cáo: ${cacHs[0].hoc_sinh.ho_ten}`
        : `Báo cáo lớp ${tenLop} (${cacHs.length} học sinh)`
      setKetQua({ tieuDe, cacHs })
    } catch (e) { setLoi(e.message) }
    finally { setDangTai(false) }
  }

  if (!choPhep) return null

  return (
    <>
      <Card>
        <CardHeader title="Xuất báo cáo cho phụ huynh"
          subtitle="Chọn lớp → chọn học sinh (mặc định cả lớp, có thể bỏ bớt) → chọn khoảng thời gian (để trống = toàn bộ) → in ra PDF." />
        <CardBody className="flex flex-col gap-4">
          <div className="max-w-xs">
            <Select label="Lớp" value={lopId} onChange={(e) => doiLop(e.target.value)}
              options={[{ value: '', label: '— Chọn lớp —' }, ...lopOptions]} />
          </div>

          {lopId && (
            <div className="flex flex-col gap-2">
              <div className="flex items-center justify-between gap-2">
                <p className="text-sm font-semibold text-ink">
                  Học sinh ({chonHs.size}/{hsTrongLop.length})
                </p>
                <Button size="sm" variant="secondary" onClick={toggleTatCa}>
                  {chonHs.size === hsTrongLop.length ? 'Bỏ chọn tất cả' : 'Chọn tất cả'}
                </Button>
              </div>
              <div className="overflow-y-auto max-h-56 rounded-lg border border-border divide-y divide-border">
                {hsTrongLop.length === 0 ? (
                  <p className="text-sm text-muted px-3 py-4">Lớp chưa có học sinh.</p>
                ) : hsTrongLop.map((h) => (
                  <label key={h.hoc_sinh_id}
                    className="flex items-center gap-2 px-3 py-2 hover:bg-surface-2 cursor-pointer">
                    <input type="checkbox" checked={chonHs.has(h.hoc_sinh_id)}
                      onChange={() => toggleHs(h.hoc_sinh_id)} />
                    <span className="text-sm text-ink">{h.ho_ten}</span>
                  </label>
                ))}
              </div>
            </div>
          )}

          <div className="flex flex-wrap items-end gap-3">
            <div>
              <label className="block text-sm font-medium text-ink mb-1">Từ ngày</label>
              <input type="date" value={tuNgay} onChange={(e) => setTuNgay(e.target.value)}
                className="rounded-md border border-border bg-surface px-3 py-1.5 text-sm text-ink
                  focus:outline-none focus:ring-2 focus:ring-primary/40 focus:border-primary" />
            </div>
            <div>
              <label className="block text-sm font-medium text-ink mb-1">Đến ngày</label>
              <input type="date" value={denNgay} onChange={(e) => setDenNgay(e.target.value)}
                className="rounded-md border border-border bg-surface px-3 py-1.5 text-sm text-ink
                  focus:outline-none focus:ring-2 focus:ring-primary/40 focus:border-primary" />
            </div>
            <Button disabled={!lopId || chonHs.size === 0 || dangTai} onClick={xuat}>
              {dangTai ? 'Đang tạo...' : `Xuất báo cáo (${chonHs.size} học sinh)`}
            </Button>
          </div>
          {loi && <p className="text-sm text-danger">{loi}</p>}
        </CardBody>
      </Card>

      {ketQua && (
        <BaoCaoModal tieuDe={ketQua.tieuDe} cacHs={ketQua.cacHs} khoang={khoang}
          onDong={() => setKetQua(null)} />
      )}
    </>
  )
}
