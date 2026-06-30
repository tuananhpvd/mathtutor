import { useRef, useState } from 'react'
import * as XLSX from 'xlsx'
import { Button } from '../ui'

function validateRow(row) {
  if (!row.ho_ten) return 'Thiếu họ tên'
  if (!row.dang_nhap) return 'Thiếu tên đăng nhập'
  if (!row.mat_khau) return 'Thiếu mật khẩu'
  if (row.mat_khau.length < 4) return 'Mật khẩu phải ≥ 4 ký tự'
  return null
}

function findCol(header, ...keywords) {
  return header.findIndex((h) =>
    keywords.some((k) => String(h).trim().toLowerCase().includes(k.toLowerCase()))
  )
}

export default function ImportHocSinhDialog({ lop, onKiemTra, onImport, onClose, onSaved }) {
  const [rows, setRows] = useState(null)
  const [dangXuLy, setDangXuLy] = useState(false)
  const [loi, setLoi] = useState('')
  const fileRef = useRef(null)

  function xuatMau() {
    const wb = XLSX.utils.book_new()
    const ws = XLSX.utils.aoa_to_sheet([
      ['Họ tên học sinh', 'Tên đăng nhập', 'Mật khẩu'],
      ['Nguyễn Văn An', 'nguyen.van.an', '123456'],
      ['Trần Thị Bình', 'tran.thi.binh', '123456'],
    ])
    ws['!cols'] = [{ wch: 24 }, { wch: 20 }, { wch: 12 }]
    XLSX.utils.book_append_sheet(wb, ws, 'Danh sách học sinh')
    XLSX.writeFile(wb, 'mau_danh_sach_hoc_sinh.xlsx')
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

      const header = (data[0] || [])
      const idxHoTen = findCol(header, 'họ tên', 'ho ten')
      const idxDN = findCol(header, 'đăng nhập', 'dang nhap')
      const idxMK = findCol(header, 'mật khẩu', 'mat khau')

      if (idxHoTen === -1 || idxDN === -1 || idxMK === -1) {
        setLoi('Không tìm thấy đủ cột "Họ tên học sinh", "Tên đăng nhập", "Mật khẩu". Hãy dùng file mẫu.')
        setRows(null)
        return
      }

      const parsed = data
        .slice(1)
        .map((r) => ({
          ho_ten: String(r[idxHoTen] ?? '').trim(),
          dang_nhap: String(r[idxDN] ?? '').trim(),
          mat_khau: String(r[idxMK] ?? '').trim(),
        }))
        .filter((r) => r.ho_ten || r.dang_nhap || r.mat_khau)

      if (parsed.length === 0) {
        setLoi('File không có dữ liệu học sinh nào hợp lệ.')
        setRows(null)
        return
      }

      // Validate từng dòng cục bộ trước
      const withErrors = parsed.map((r) => ({ ...r, ly_do: validateRow(r) }))

      // Kiểm tra trùng tên đăng nhập (toàn hệ thống) cho các dòng pass validate
      const dnsCheck = [...new Set(
        withErrors.filter((r) => !r.ly_do).map((r) => r.dang_nhap)
      )]

      if (dnsCheck.length > 0) {
        const res = await onKiemTra(dnsCheck)
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
      const result = await onImport(
        valid.map(({ ho_ten, dang_nhap, mat_khau }) => ({ ho_ten, dang_nhap, mat_khau }))
      )
      onSaved(`Đã thêm ${result.da_tao.length} học sinh vào lớp ${lop.ten}.`)
    } catch (err) {
      setLoi(err.message)
      setDangXuLy(false)
    }
  }

  const soLoi = rows ? rows.filter((r) => r.ly_do).length : 0
  const soMoi = rows ? rows.filter((r) => !r.ly_do).length : 0

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-2xl flex flex-col max-h-[88vh]">
        {/* Header */}
        <div className="px-5 pt-5 pb-3 border-b border-border flex-shrink-0">
          <h2 className="font-bold text-lg text-ink">
            Thêm danh sách học sinh — {lop.ten}
          </h2>
        </div>

        {/* Scrollable body */}
        <div className="overflow-y-auto flex-1 px-5 py-4 flex flex-col gap-4">
          {/* Import controls */}
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
            File phải có cột <strong>Họ tên học sinh</strong>,{' '}
            <strong>Tên đăng nhập</strong>, <strong>Mật khẩu</strong> (tối thiểu 4 ký tự).
            Có thể chọn lại file để cập nhật danh sách.
          </p>

          {loi && (
            <p className="text-sm text-danger bg-danger-soft rounded-md px-3 py-2">
              {loi}
            </p>
          )}

          {/* Preview */}
          {rows && (
            <div className="flex flex-col gap-2">
              <p className="text-sm text-muted">
                {rows.length} dòng ·{' '}
                <span className="text-green-600 font-medium">{soMoi} có thể tạo</span>
                {soLoi > 0 && (
                  <>
                    {' '}·{' '}
                    <span className="text-danger font-medium">{soLoi} lỗi (bỏ qua)</span>
                  </>
                )}
              </p>
              <div className="rounded-lg border border-border overflow-hidden">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="bg-surface border-b border-border">
                      <th className="text-left px-3 py-2 font-medium text-muted">Họ tên</th>
                      <th className="text-left px-3 py-2 font-medium text-muted">Tên đăng nhập</th>
                      <th className="text-left px-3 py-2 font-medium text-muted">Mật khẩu</th>
                      <th className="text-left px-3 py-2 font-medium text-muted">Trạng thái</th>
                    </tr>
                  </thead>
                  <tbody>
                    {rows.map((r, i) => (
                      <tr
                        key={i}
                        className={`border-t border-border ${r.ly_do ? 'bg-red-50' : ''}`}
                      >
                        <td className={`px-3 py-2 ${r.ly_do ? 'text-red-700' : 'text-ink'}`}>
                          {r.ho_ten || <span className="text-muted italic">—</span>}
                        </td>
                        <td className={`px-3 py-2 ${r.ly_do ? 'text-red-700' : 'text-ink'}`}>
                          {r.dang_nhap || <span className="text-muted italic">—</span>}
                        </td>
                        <td className={`px-3 py-2 ${r.ly_do ? 'text-red-700' : 'text-ink'}`}>
                          {r.mat_khau || <span className="text-muted italic">—</span>}
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
              {dangXuLy ? 'Đang tạo...' : `Xác nhận (tạo ${soMoi} học sinh)`}
            </Button>
          )}
        </div>
      </div>
    </div>
  )
}
