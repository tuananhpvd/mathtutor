import { useRef, useState } from 'react'
import * as XLSX from 'xlsx'
import { api } from '../../api'
import { Button } from '../ui'

const TANG_LABEL = {
  tu_khoa_khan_cap: 'Khẩn cấp',
  tu_khoa_khong_phu_hop: 'Không phù hợp',
  tu_khoa_ngoai_pham_vi: 'Ngoài phạm vi',
}
const TANG_KEYS = Object.keys(TANG_LABEL)

function boDau(s) {
  return String(s ?? '')
    .replace(/đ/g, 'd')
    .replace(/Đ/g, 'D')
    .normalize('NFD')
    .replace(new RegExp('[\\u0300-\\u036f]', 'g'), '')
    .trim()
    .toLowerCase()
}

function findCol(header, ...keywords) {
  return header.findIndex((h) =>
    keywords.some((k) => String(h).trim().toLowerCase().includes(k.toLowerCase()))
  )
}

function parseTang(str) {
  const s = boDau(str)
  if (s.includes('khan cap')) return 'tu_khoa_khan_cap'
  if (s.includes('khong phu hop')) return 'tu_khoa_khong_phu_hop'
  if (s.includes('ngoai pham vi')) return 'tu_khoa_ngoai_pham_vi'
  return null
}

// cfg: object cấu hình hiện tại (có 3 khóa tu_khoa_*, mỗi khóa là mảng {tu_khoa,...}).
// onSaved(soLuong): gọi sau khi lưu xong, để CauHinh.jsx tải lại cấu hình + đóng dialog.
export default function ImportTuKhoaDialog({ cfg, onClose, onSaved }) {
  const [rows, setRows] = useState(null)
  const [dangXuLy, setDangXuLy] = useState(false)
  const [loi, setLoi] = useState('')
  const fileRef = useRef(null)

  function xuatMau() {
    const wb = XLSX.utils.book_new()
    const ws = XLSX.utils.aoa_to_sheet([
      ['Tầng', 'Từ khóa'],
      ['Khẩn cấp', 'tự vẫn'],
      ['Không phù hợp', 'cá độ'],
      ['Ngoài phạm vi', 'làm hộ bài tập môn khác'],
    ])
    ws['!cols'] = [{ wch: 18 }, { wch: 36 }]
    XLSX.utils.book_append_sheet(wb, ws, 'Từ khóa an toàn')
    XLSX.writeFile(wb, 'mau_tu_khoa_an_toan.xlsx')
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
      const idxTang = findCol(header, 'tầng', 'tang')
      const idxTu = findCol(header, 'từ khóa', 'tu khoa', 'tukhoa')

      if (idxTang === -1 || idxTu === -1) {
        setLoi('Không tìm thấy đủ cột "Tầng" và "Từ khóa". Hãy dùng file mẫu.')
        setRows(null)
        return
      }

      const daCoTheoTang = Object.fromEntries(
        TANG_KEYS.map((k) => [k, new Set((cfg[k] || []).map((it) => boDau(it.tu_khoa)))])
      )
      const trongFileTheoTang = Object.fromEntries(TANG_KEYS.map((k) => [k, new Set()]))

      const parsed = data
        .slice(1)
        .map((r) => ({
          tang: parseTang(r[idxTang]),
          tang_raw: String(r[idxTang] ?? '').trim(),
          tu_khoa: String(r[idxTu] ?? '').trim(),
        }))
        .filter((r) => r.tang_raw || r.tu_khoa)
        .map((r) => {
          let ly_do = null
          if (!r.tu_khoa) ly_do = 'Thiếu từ khóa'
          else if (!r.tang) ly_do = 'Tầng không hợp lệ (Khẩn cấp / Không phù hợp / Ngoài phạm vi)'
          else if (daCoTheoTang[r.tang].has(boDau(r.tu_khoa))) ly_do = 'Đã có trong danh sách'
          else if (trongFileTheoTang[r.tang].has(boDau(r.tu_khoa))) ly_do = 'Trùng lặp trong file'
          if (!ly_do && r.tang) trongFileTheoTang[r.tang].add(boDau(r.tu_khoa))
          return { ...r, ly_do }
        })

      if (parsed.length === 0) {
        setLoi('File không có dữ liệu từ khóa nào.')
        setRows(null)
        return
      }
      setRows(parsed)
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
      for (const khoa of TANG_KEYS) {
        const themVao = valid.filter((r) => r.tang === khoa)
        if (themVao.length === 0) continue
        const danhSachMoi = [
          ...(cfg[khoa] || []),
          ...themVao.map((r) => ({ tu_khoa: r.tu_khoa, kich_hoat: true })),
        ]
        await api.adminSetConfig(khoa, danhSachMoi)
      }
      onSaved(valid.length)
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
        <div className="px-5 pt-5 pb-3 border-b border-border flex-shrink-0">
          <h2 className="font-bold text-lg text-ink">Import từ khóa an toàn</h2>
          <p className="text-sm text-muted mt-0.5">
            Thêm hàng loạt từ khóa mới cho cả 3 tầng cùng lúc từ file Excel
          </p>
        </div>

        <div className="overflow-y-auto flex-1 px-5 py-4 flex flex-col gap-4">
          <div className="flex items-center gap-3 flex-wrap">
            <Button variant="secondary" onClick={xuatMau}>Tải file mẫu (.xlsx)</Button>
            <Button variant="secondary" onClick={() => fileRef.current?.click()} disabled={dangXuLy}>
              {dangXuLy ? 'Đang xử lý...' : 'Chọn file Excel'}
            </Button>
            <input ref={fileRef} type="file" accept=".xlsx,.xls" className="hidden" onChange={onChonFile} />
          </div>
          <p className="text-xs text-muted">
            File cần cột <strong>Tầng</strong> (<em>Khẩn cấp</em> / <em>Không phù hợp</em> /{' '}
            <em>Ngoài phạm vi</em>) và <strong>Từ khóa</strong>. Từ khóa đã có sẵn hoặc trùng lặp
            trong file sẽ tự bỏ qua, không tạo bản sao. Có thể chọn lại file để cập nhật.
          </p>

          {loi && <p className="text-sm text-danger bg-danger-soft rounded-md px-3 py-2">{loi}</p>}

          {rows && (
            <div className="flex flex-col gap-2">
              <p className="text-sm text-muted">
                {rows.length} dòng ·{' '}
                <span className="text-success font-medium">{soMoi} sẽ thêm mới</span>
                {soLoi > 0 && (
                  <> · <span className="text-danger font-medium">{soLoi} bỏ qua</span></>
                )}
              </p>
              <div className="rounded-lg border border-border overflow-hidden max-h-72 overflow-y-auto">
                <table className="w-full text-sm">
                  <thead className="sticky top-0">
                    <tr className="bg-surface-2 border-b border-border">
                      <th className="text-left px-3 py-2 font-medium text-muted">Tầng</th>
                      <th className="text-left px-3 py-2 font-medium text-muted">Từ khóa</th>
                      <th className="text-left px-3 py-2 font-medium text-muted">Trạng thái</th>
                    </tr>
                  </thead>
                  <tbody>
                    {rows.map((r, i) => (
                      <tr key={i} className={`border-t border-border ${r.ly_do ? 'bg-danger-soft' : ''}`}>
                        <td className={`px-3 py-2 ${r.ly_do ? 'text-danger' : 'text-ink'}`}>
                          {r.tang ? TANG_LABEL[r.tang] : (
                            <span className="italic">{r.tang_raw || '—'}</span>
                          )}
                        </td>
                        <td className={`px-3 py-2 ${r.ly_do ? 'text-danger' : 'text-ink'}`}>
                          {r.tu_khoa || <span className="italic text-muted">—</span>}
                        </td>
                        <td className="px-3 py-2">
                          {r.ly_do ? (
                            <span className="text-danger text-xs">{r.ly_do}</span>
                          ) : (
                            <span className="text-success text-xs">✓ Mới</span>
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

        <div className="px-5 py-4 border-t border-border flex-shrink-0 flex gap-2 justify-end">
          <Button variant="secondary" onClick={onClose} disabled={dangXuLy}>Hủy bỏ</Button>
          {rows && soMoi > 0 && (
            <Button onClick={xacNhan} disabled={dangXuLy}>
              {dangXuLy ? 'Đang lưu...' : `Xác nhận (thêm ${soMoi} từ khóa)`}
            </Button>
          )}
        </div>
      </div>
    </div>
  )
}
