import { useEffect, useMemo, useRef, useState } from 'react'
import * as XLSX from 'xlsx'
import { api } from '../../api'
import { Badge, Button, Card, CardBody, CardHeader, Input, useConfirm } from '../../components/ui'
import SuaHocSinhModal from '../../components/gv/SuaHocSinhModal'
import ImportHocSinhDialog from '../../components/gv/ImportHocSinhDialog'

// Modal xem trước danh sách lớp sẽ import
function PreviewModal({ preview, dangImport, onXacNhan, onHuy }) {
  const { tenLops, kiemTra } = preview
  const soTrung = tenLops.filter((t) => kiemTra[t]?.ton_tai).length
  const soMoi = tenLops.length - soTrung

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="bg-surface rounded-xl shadow-xl w-full max-w-md flex flex-col max-h-[80vh]">
        {/* Header */}
        <div className="px-5 pt-5 pb-3 border-b border-border shrink-0">
          <h2 className="font-bold text-lg text-ink">Xem trước danh sách lớp</h2>
          <p className="text-sm text-muted mt-0.5">
            {tenLops.length} tên từ file ·{' '}
            <span className="text-success font-medium">{soMoi} có thể tạo</span>
            {soTrung > 0 && (
              <>
                {' '}·{' '}
                <span className="text-danger font-medium">{soTrung} trùng tên</span>
              </>
            )}
          </p>
        </div>

        {/* Danh sách */}
        <div className="overflow-y-auto flex-1 px-5 py-3 flex flex-col gap-1.5">
          {tenLops.map((ten, idx) => {
            const kt = kiemTra[ten]
            const trung = kt?.ton_tai
            return (
              <div
                key={idx}
                className={`flex items-center justify-between gap-2 rounded-md px-3 py-2 ${
                  trung ? 'bg-red-50 border border-red-200' : 'bg-green-50 border border-green-200'
                }`}
              >
                <span className={`font-medium text-sm ${trung ? 'text-red-700' : 'text-green-700'}`}>
                  {ten}
                </span>
                {trung ? (
                  <span className="text-xs text-red-600 whitespace-nowrap">
                    Đã tồn tại ({kt.so_hoc_sinh} học sinh)
                  </span>
                ) : (
                  <span className="text-xs text-green-600">Mới</span>
                )}
              </div>
            )
          })}
        </div>

        {/* Buttons */}
        <div className="px-5 py-4 border-t border-border flex gap-2 justify-end shrink-0">
          <Button variant="secondary" onClick={onHuy} disabled={dangImport}>
            Hủy bỏ
          </Button>
          <Button onClick={onXacNhan} disabled={dangImport || soMoi === 0}>
            {dangImport
              ? 'Đang tạo...'
              : soMoi === 0
              ? 'Không có lớp mới'
              : `Xác nhận (tạo ${soMoi} lớp)`}
          </Button>
        </div>
      </div>
    </div>
  )
}

export default function QuanLyLopGV() {
  const confirm = useConfirm()
  const [lops, setLops] = useState([])
  const [error, setError] = useState('')
  const [newTen, setNewTen] = useState('')
  const [q, setQ] = useState('')
  const [moRong, setMoRong] = useState({})
  const [suaLop, setSuaLop] = useState(null)
  const [suaHs, setSuaHs] = useState(null)
  const [importMsg, setImportMsg] = useState('')
  const [importHsLop, setImportHsLop] = useState(null)
  const [errThemLop, setErrThemLop] = useState('')
  const [dangImport, setDangImport] = useState(false)
  const [preview, setPreview] = useState(null) // { tenLops, kiemTra }
  const fileRef = useRef(null)

  function tai() {
    api.gvLop().then(setLops).catch((e) => setError(e.message))
  }
  useEffect(tai, [])

  const lopOptions = lops.map((l) => ({ value: String(l.id), label: l.ten }))

  async function themLop() {
    if (!newTen.trim()) return
    const trung = lops.find((l) => l.ten.trim().toLowerCase() === newTen.trim().toLowerCase())
    if (trung) {
      setErrThemLop(`Trùng tên lớp đã có (có ${trung.so_hoc_sinh} học sinh)`)
      return
    }
    try {
      await api.gvTaoLop({ ten: newTen.trim() })
      setNewTen(''); setErrThemLop(''); tai()
    } catch (e) { setError(e.message) }
  }
  async function luuSuaLop() {
    try { await api.gvSuaLop(suaLop.id, { ten: suaLop.ten }); setSuaLop(null); tai() }
    catch (e) { setError(e.message) }
  }
  async function xoaLop(l) {
    if (!await confirm(`Xóa lớp "${l.ten}"? Học sinh trong lớp sẽ bị gỡ khỏi lớp.`)) return
    try { await api.gvXoaLop(l.id); tai() } catch (e) { setError(e.message) }
  }
  async function doiTrangThaiHs(h) {
    await api.gvDoiTrangThaiHocSinh(h.id, h.trang_thai === 'hoat_dong' ? 'khoa' : 'hoat_dong')
    tai()
  }
  async function xoaHs(h) {
    if (!await confirm(`Xóa học sinh "${h.ho_ten}"?`)) return
    try { await api.gvXoaHocSinh(h.id); tai() } catch (e) { setError(e.message) }
  }

  // Xuất file Excel mẫu
  function xuatMau() {
    const wb = XLSX.utils.book_new()
    const ws = XLSX.utils.aoa_to_sheet([
      ['Tên lớp'],
      ['12A1'],
      ['12A2'],
      ['12B1'],
    ])
    ws['!cols'] = [{ wch: 20 }]
    XLSX.utils.book_append_sheet(wb, ws, 'Danh sách lớp')
    XLSX.writeFile(wb, 'mau_danh_sach_lop.xlsx')
  }

  // Chọn file → parse → kiểm tra trùng → hiện modal preview
  async function onChonFile(e) {
    const file = e.target.files?.[0]
    if (!file) return
    setImportMsg(''); setError(''); setDangImport(true)

    try {
      const buf = await file.arrayBuffer()
      const wb = XLSX.read(buf, { type: 'array' })
      const ws = wb.Sheets[wb.SheetNames[0]]
      const rows = XLSX.utils.sheet_to_json(ws, { header: 1, defval: '' })

      const header = rows[0] || []
      const colIdx = header.findIndex(
        (h) => String(h).trim().toLowerCase() === 'tên lớp'
      )
      if (colIdx === -1) {
        setError('Không tìm thấy cột "Tên lớp" trong file. Hãy dùng file mẫu.')
        return
      }

      const ten_lops_raw = rows
        .slice(1)
        .map((r) => String(r[colIdx] ?? '').trim())
        .filter(Boolean)

      if (ten_lops_raw.length === 0) {
        setError('File không có tên lớp nào hợp lệ.')
        return
      }

      // Loại trùng trong file (giữ thứ tự, lấy lần xuất hiện đầu tiên)
      const ten_lops = [...new Set(ten_lops_raw)]

      // Kiểm tra trùng toàn hệ thống
      const kiemTra = await api.gvKiemTraTrung(ten_lops)
      setPreview({ tenLops: ten_lops, kiemTra })
    } catch (e) {
      setError(e.message)
    } finally {
      setDangImport(false)
      e.target.value = ''
    }
  }

  // Xác nhận: chỉ tạo những lớp không trùng
  async function xacNhanImport() {
    if (!preview) return
    const chuaTrung = preview.tenLops.filter((t) => !preview.kiemTra[t]?.ton_tai)
    setDangImport(true)
    try {
      const result = await api.gvImportLopBatch(chuaTrung)
      tai()
      const msgs = [`Đã tạo ${result.da_tao.length} lớp: ${result.da_tao.join(', ') || '—'}`]
      if (result.bo_qua.length > 0)
        msgs.push(`Bỏ qua ${result.bo_qua.length} tên đã tồn tại: ${result.bo_qua.join(', ')}`)
      setImportMsg(msgs.join(' · '))
      setPreview(null)
    } catch (e) {
      setError(e.message)
    } finally {
      setDangImport(false)
    }
  }

  const loc = useMemo(() => {
    const kw = q.trim().toLowerCase()
    return kw ? lops.filter((l) => l.ten.toLowerCase().includes(kw)) : lops
  }, [lops, q])

  return (
    <div className="flex flex-col gap-5">
      {error && (
        <p className="text-danger text-sm bg-danger-soft rounded-md px-3 py-2">
          {error} <button onClick={() => setError('')} className="ml-2 font-bold">✕</button>
        </p>
      )}

      <Card>
        <CardHeader title="Thêm lớp" subtitle="Thêm từng lớp hoặc import hàng loạt từ Excel" />
        <CardBody className="flex flex-col gap-4">
          {/* Thêm từng lớp */}
          <div className="grid sm:grid-cols-2 gap-3 items-end">
            <Input label="Tên lớp" value={newTen}
              onChange={(e) => { setNewTen(e.target.value); setErrThemLop('') }}
              placeholder="vd: 12A2"
              onKeyDown={(e) => e.key === 'Enter' && themLop()} />
            <Button onClick={themLop}>Thêm lớp</Button>
          </div>
          {errThemLop && <p className="text-sm text-danger">{errThemLop}</p>}

          {/* Phân cách */}
          <div className="flex items-center gap-3">
            <div className="flex-1 border-t border-border" />
            <span className="text-xs text-muted">hoặc import từ Excel</span>
            <div className="flex-1 border-t border-border" />
          </div>

          {/* Import Excel */}
          <div className="flex items-center gap-3 flex-wrap">
            <Button variant="secondary" onClick={xuatMau}>
              Tải file mẫu (.xlsx)
            </Button>
            <Button
              variant="secondary"
              onClick={() => fileRef.current?.click()}
              disabled={dangImport}
            >
              {dangImport ? 'Đang kiểm tra...' : 'Import từ Excel'}
            </Button>
            <input
              ref={fileRef}
              type="file"
              accept=".xlsx,.xls"
              className="hidden"
              onChange={onChonFile}
            />
            {importMsg && (
              <span className="text-sm text-success">{importMsg}</span>
            )}
          </div>
          <p className="text-xs text-muted">
            File Excel phải có cột <strong>Tên lớp</strong>. Tải file mẫu để xem định dạng đúng.
          </p>
        </CardBody>
      </Card>

      <Card>
        <CardHeader title="Lớp của tôi" subtitle={`${loc.length}/${lops.length} lớp`} />
        <CardBody className="flex flex-col gap-3">
          <Input label="Tìm lớp" placeholder="Tên lớp..." value={q} onChange={(e) => setQ(e.target.value)} />
          <div className="flex flex-col gap-2">
            {loc.map((l) => (
              <div key={l.id} className="rounded-lg border border-border">
                {suaLop?.id === l.id ? (
                  <div className="grid sm:grid-cols-2 gap-3 items-end p-3">
                    <Input label="Tên lớp" value={suaLop.ten}
                      onChange={(e) => setSuaLop((s) => ({ ...s, ten: e.target.value }))} />
                    <div className="flex gap-2">
                      <Button onClick={luuSuaLop}>Lưu</Button>
                      <Button variant="secondary" onClick={() => setSuaLop(null)}>Hủy</Button>
                    </div>
                  </div>
                ) : (
                  <div className="flex items-center justify-between gap-2 p-3 flex-wrap">
                    <div>
                      <span className="font-bold text-ink">{l.ten}</span>
                      <span className="text-muted text-sm"> · {l.so_hoc_sinh} học sinh</span>
                    </div>
                    <div className="flex gap-1">
                      <Button size="sm" variant="secondary" onClick={() => setImportHsLop(l)}>
                        Thêm danh sách học sinh
                      </Button>
                      <Button size="sm" variant="secondary" onClick={() => setMoRong((m) => ({ ...m, [l.id]: !m[l.id] }))}>
                        {moRong[l.id] ? 'Ẩn học sinh' : 'Xem học sinh'}
                      </Button>
                      <Button size="sm" variant="secondary" onClick={() => setSuaLop({ id: l.id, ten: l.ten })}>Sửa</Button>
                      <Button size="sm" variant="danger" onClick={() => xoaLop(l)}>Xóa</Button>
                    </div>
                  </div>
                )}

                {moRong[l.id] && (
                  <div className="border-t border-border px-3 py-2 flex flex-col gap-1">
                    {l.hoc_sinhs.length === 0 && <p className="text-sm text-muted py-1">Lớp chưa có học sinh.</p>}
                    {l.hoc_sinhs.map((h) => (
                      <div key={h.id} className="flex items-center justify-between gap-2 py-1.5 border-b border-border last:border-0">
                        <div className="text-sm">
                          <span className="text-ink font-medium">{h.ho_ten}</span>
                          <span className="text-muted"> ({h.dang_nhap})</span>
                          <Badge className="ml-2" tone={h.trang_thai === 'hoat_dong' ? 'success' : 'danger'}>
                            {h.trang_thai === 'hoat_dong' ? 'Hoạt động' : 'Đã khóa'}
                          </Badge>
                        </div>
                        <div className="flex gap-1">
                          <Button size="sm" variant="secondary" onClick={() => setSuaHs(h)}>Sửa</Button>
                          <Button size="sm" variant={h.trang_thai === 'hoat_dong' ? 'warning' : 'success'} onClick={() => doiTrangThaiHs(h)}>
                            {h.trang_thai === 'hoat_dong' ? 'Khóa' : 'Mở khóa'}
                          </Button>
                          <Button size="sm" variant="danger" onClick={() => xoaHs(h)}>Xóa</Button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
            {loc.length === 0 && <p className="text-sm text-muted">Chưa có lớp nào. Hãy thêm lớp ở trên.</p>}
          </div>
        </CardBody>
      </Card>

      {suaHs && (
        <SuaHocSinhModal hs={suaHs} showLop lopOptions={lopOptions}
          onClose={() => setSuaHs(null)} onSaved={() => { setSuaHs(null); tai() }} />
      )}

      {preview && (
        <PreviewModal
          preview={preview}
          dangImport={dangImport}
          onXacNhan={xacNhanImport}
          onHuy={() => setPreview(null)}
        />
      )}

      {importHsLop && (
        <ImportHocSinhDialog
          lop={importHsLop}
          onKiemTra={(dns) => api.gvKiemTraHS(importHsLop.id, dns)}
          onImport={(hs) => api.gvImportHSBatch(importHsLop.id, hs)}
          onClose={() => setImportHsLop(null)}
          onSaved={(msg) => {
            setImportHsLop(null)
            setImportMsg(msg)
            tai()
          }}
        />
      )}
    </div>
  )
}
