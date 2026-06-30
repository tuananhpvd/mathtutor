import { useRef, useState } from 'react'
import * as XLSX from 'xlsx'
import { api } from '../../api'
import { Button } from '../ui'

const NHAN_VAI = { gv: 'Giáo viên', hs: 'Học sinh' }

function parseVaiTro(str) {
  const s = String(str ?? '').trim().toLowerCase()
  if (s === 'giáo viên' || s === 'giao vien' || s === 'gv') return 'gv'
  if (s === 'học sinh' || s === 'hoc sinh' || s === 'hs') return 'hs'
  return null
}

function findCol(header, ...keywords) {
  return header.findIndex((h) =>
    keywords.some((k) => String(h).trim().toLowerCase().includes(k.toLowerCase()))
  )
}

function validateRow(row) {
  if (!row.ho_ten) return 'Thiếu họ tên'
  if (!row.dang_nhap) return 'Thiếu tên đăng nhập'
  if (!row.mat_khau) return 'Thiếu mật khẩu'
  if (row.mat_khau.length < 4) return 'Mật khẩu phải ≥ 4 ký tự'
  if (!row.vai_tro) return 'Vai trò không hợp lệ (nhập "Giáo viên" hoặc "Học sinh")'
  return null
}

export default function ImportTaiKhoanDialog({ onClose, onSaved }) {
  const [rows, setRows] = useState(null)
  const [dangXuLy, setDangXuLy] = useState(false)
  const [loi, setLoi] = useState('')
  const fileRef = useRef(null)

  function xuatMau() {
    const wb = XLSX.utils.book_new()
    const ws = XLSX.utils.aoa_to_sheet([
      ['Họ tên', 'Tên đăng nhập', 'Mật khẩu', 'Vai trò'],
      ['Nguyễn Văn An', 'nguyen.van.an', '123456', 'Giáo viên'],
      ['Trần Thị Bình', 'tran.thi.binh', '123456', 'Học sinh'],
    ])
    ws['!cols'] = [{ wch: 24 }, { wch: 20 }, { wch: 12 }, { wch: 14 }]
    XLSX.utils.book_append_sheet(wb, ws, 'Danh sách tài khoản')
    XLSX.writeFile(wb, 'mau_danh_sach_tai_khoan.xlsx')
  }

  async function onChonFile(e) {
    const file = e.target.files?.[0]
    if (!file) return
    setLoi('')
    setDangXuLy(true)

    try {
      const buf = await file.arrayBuffer()
      const wb = XLSX.read(buf, { type: 'array' })
      const ws = wb.Sheets[wb.SheetNames[0]]
      const data = XLSX.utils.sheet_to_json(ws, { header: 1, defval: '' })

      const header = data[0] || []
      const idxHoTen = findCol(header, 'họ tên', 'ho ten')
      const idxDN = findCol(header, 'đăng nhập', 'dang nhap')
      const idxMK = findCol(header, 'mật khẩu', 'mat khau')
      const idxVai = findCol(header, 'vai trò', 'vai tro', 'vai')

      if (idxHoTen === -1 || idxDN === -1 || idxMK === -1 || idxVai === -1) {
        setLoi('Không tìm thấy đủ cột "Họ tên", "Tên đăng nhập", "Mật khẩu", "Vai trò". Hãy dùng file mẫu.')
        setRows(null)
        return
      }

      const parsed = data
        .slice(1)
        .map((r) => ({
          ho_ten: String(r[idxHoTen] ?? '').trim(),
          dang_nhap: String(r[idxDN] ?? '').trim(),
          mat_khau: String(r[idxMK] ?? '').trim(),
          vai_tro: parseVaiTro(r[idxVai]),
          vai_tro_raw: String(r[idxVai] ?? '').trim(),
        }))
        .filter((r) => r.ho_ten || r.dang_nhap || r.mat_khau || r.vai_tro_raw)

      if (parsed.length === 0) {
        setLoi('File không có dữ liệu tài khoản nào hợp lệ.')
        setRows(null)
        return
      }

      const withErrors = parsed.map((r) => ({ ...r, ly_do: validateRow(r) }))

      // Kiểm tra trùng dang_nhap toàn hệ thống cho các dòng pass validate
      const dnsCheck = [...new Set(
        withErrors.filter((r) => !r.ly_do).map((r) => r.dang_nhap)
      )]

      if (dnsCheck.length > 0) {
        const res = await api.adminKiemTraDangNhap(dnsCheck)
        const trungSet = new Set(res.trung)
        withErrors.forEach((r) => {
          if (!r.ly_do && trungSet.has(r.dang_nhap)) {
            r.ly_do = 'Tên đăng nhập đã tồn tại'
          }
        })
      }

      setRows(withErrors)
    } catch (err) {
      setLoi(err.message)
    } finally {
      setDangXuLy(false)
      e.target.value = ''
    }
  }

  async function xacNhan() {
    if (!rows) return
    const valid = rows.filter((r) => !r.ly_do)
    if (valid.length === 0) return

    setDangXuLy(true)
    try {
      const result = await api.adminImportTaiKhoanBatch(
        valid.map(({ ho_ten, dang_nhap, mat_khau, vai_tro }) => ({
          ho_ten, dang_nhap, mat_khau, vai_tro,
        }))
      )
      onSaved(`Đã tạo ${result.da_tao.length} tài khoản thành công.`)
    } catch (err) {
      setLoi(err.message)
      setDangXuLy(false)
    }
  }

  const soLoi = rows ? rows.filter((r) => r.ly_do).length : 0
  const soMoi = rows ? rows.filter((r) => !r.ly_do).length : 0

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-3xl flex flex-col max-h-[88vh]">
        {/* Header */}
        <div className="px-5 pt-5 pb-3 border-b border-border flex-shrink-0">
          <h2 className="font-bold text-lg text-ink">Import danh sách tài khoản</h2>
          <p className="text-sm text-muted mt-0.5">Tạo hàng loạt tài khoản Giáo viên / Học sinh từ file Excel</p>
        </div>

        {/* Scrollable body */}
        <div className="overflow-y-auto flex-1 px-5 py-4 flex flex-col gap-4">
          {/* Controls */}
          <div className="flex items-center gap-3 flex-wrap">
            <Button variant="secondary" onClick={xuatMau}>
              Tải file mẫu (.xlsx)
            </Button>
            <Button
              variant="secondary"
              onClick={() => fileRef.current?.click()}
              disabled={dangXuLy}
            >
              {dangXuLy ? 'Đang xử lý...' : 'Import từ Excel'}
            </Button>
            <input
              ref={fileRef}
              type="file"
              accept=".xlsx,.xls"
              className="hidden"
              onChange={onChonFile}
            />
          </div>
          <p className="text-xs text-muted">
            File phải có cột <strong>Họ tên</strong>, <strong>Tên đăng nhập</strong>,{' '}
            <strong>Mật khẩu</strong> (≥ 4 ký tự), <strong>Vai trò</strong>{' '}
            (<em>Giáo viên</em> hoặc <em>Học sinh</em>). Có thể chọn lại file để cập nhật.
          </p>

          {loi && (
            <p className="text-sm text-danger bg-danger-soft rounded-md px-3 py-2">{loi}</p>
          )}

          {/* Preview */}
          {rows && (
            <div className="flex flex-col gap-2">
              <p className="text-sm text-muted">
                {rows.length} dòng ·{' '}
                <span className="text-green-600 font-medium">{soMoi} có thể tạo</span>
                {soLoi > 0 && (
                  <> · <span className="text-danger font-medium">{soLoi} lỗi (bỏ qua)</span></>
                )}
              </p>
              <div className="rounded-lg border border-border overflow-hidden">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="bg-surface border-b border-border">
                      <th className="text-left px-3 py-2 font-medium text-muted">Họ tên</th>
                      <th className="text-left px-3 py-2 font-medium text-muted">Tên đăng nhập</th>
                      <th className="text-left px-3 py-2 font-medium text-muted">Mật khẩu</th>
                      <th className="text-left px-3 py-2 font-medium text-muted">Vai trò</th>
                      <th className="text-left px-3 py-2 font-medium text-muted">Trạng thái</th>
                    </tr>
                  </thead>
                  <tbody>
                    {rows.map((r, i) => (
                      <tr key={i} className={`border-t border-border ${r.ly_do ? 'bg-red-50' : ''}`}>
                        <td className={`px-3 py-2 ${r.ly_do ? 'text-red-700' : 'text-ink'}`}>
                          {r.ho_ten || <span className="italic text-muted">—</span>}
                        </td>
                        <td className={`px-3 py-2 ${r.ly_do ? 'text-red-700' : 'text-ink'}`}>
                          {r.dang_nhap || <span className="italic text-muted">—</span>}
                        </td>
                        <td className={`px-3 py-2 ${r.ly_do ? 'text-red-700' : 'text-ink'}`}>
                          {r.mat_khau || <span className="italic text-muted">—</span>}
                        </td>
                        <td className={`px-3 py-2 ${r.ly_do ? 'text-red-700' : 'text-ink'}`}>
                          {r.vai_tro ? NHAN_VAI[r.vai_tro] : (
                            <span className="italic text-red-500">{r.vai_tro_raw || '—'}</span>
                          )}
                        </td>
                        <td className="px-3 py-2">
                          {r.ly_do ? (
                            <span className="text-red-600 text-xs">{r.ly_do}</span>
                          ) : (
                            <span className="text-green-600 text-xs">✓ Mới</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-5 py-4 border-t border-border flex-shrink-0 flex gap-2 justify-end">
          <Button variant="secondary" onClick={onClose} disabled={dangXuLy}>
            Hủy bỏ
          </Button>
          {rows && soMoi > 0 && (
            <Button onClick={xacNhan} disabled={dangXuLy}>
              {dangXuLy ? 'Đang tạo...' : `Xác nhận (tạo ${soMoi} tài khoản)`}
            </Button>
          )}
        </div>
      </div>
    </div>
  )
}
