import { useEffect, useState } from 'react'
import { api } from '../../api'
import { Select } from '../ui'

/**
 * Bộ chọn lớp dùng chung cho các màn THỐNG KÊ của GV.
 *
 * Vì sao cần: thống kê gộp mọi lớp làm chìm khác biệt giữa các lớp và để lớp đông lấn át lớp
 * nhỏ → đơn vị thống kê mặc định là MỘT LỚP.
 *
 * - Tự tải danh sách lớp và **tự chọn lớp đầu tiên** → GV chỉ có 1 lớp thì hoàn toàn trong
 *   suốt (không thấy bộ chọn, số liệu chính là của lớp đó).
 * - `choPhepGop`: chỉ bật ở nơi view gộp thực sự có nghĩa (Hiệu quả phương pháp — đo CÁCH DẠY
 *   chứ không đo lớp), khi đó có thêm mục "Tất cả các lớp" ứng với value ''.
 */
export default function ChonLop({ value, onChange, choPhepGop = false, nhan = 'Lớp' }) {
  const [lops, setLops] = useState(null)

  useEffect(() => {
    let huy = false
    api.gvLop()
      .then((ds) => {
        if (huy) return
        const rows = ds || []
        setLops(rows)
        // Chưa chọn gì → mặc định lớp ĐẦU TIÊN (không để rơi vào trạng thái gộp ngoài ý muốn).
        if (!value && !choPhepGop && rows.length > 0) onChange(String(rows[0].id))
      })
      .catch(() => { if (!huy) setLops([]) })
    return () => { huy = true }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  if (!lops) return null
  // 1 lớp và không cho gộp → không cần bộ chọn, giữ giao diện gọn.
  if (lops.length <= 1 && !choPhepGop) return null

  return (
    <label className="flex items-center gap-2 text-sm text-muted">
      <span className="shrink-0">{nhan}:</span>
      {/* Select của dự án render từ prop `options` và BỎ QUA children — truyền children sẽ ra
          dropdown rỗng. */}
      <Select
        value={value ?? ''}
        onChange={(e) => onChange(e.target.value)}
        options={[
          ...(choPhepGop ? [{ value: '', label: 'Tất cả các lớp' }] : []),
          ...lops.map((l) => ({ value: String(l.id), label: l.ten })),
        ]}
        className="w-44 shrink-0"
      />
    </label>
  )
}
