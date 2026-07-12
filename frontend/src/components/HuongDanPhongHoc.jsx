/*
 * HuongDanPhongHoc — hướng dẫn nhiều bước cách dùng phòng học. KHÔNG tự hiện — HS tự bấm nút
 * "Hướng dẫn" (PhongHoc.jsx) để mở bất cứ khi nào cần, xem lại được nhiều lần (trước đây tự
 * hiện 1 lần rồi biến mất khiến HS khó nhớ).
 * Nội dung các bước tải từ server (Admin chỉnh qua trang Cấu hình, không cần sửa code) —
 * dùng MAC_DINH bên dưới làm dự phòng khi chưa tải xong / lỗi mạng.
 */

import { useEffect, useState } from 'react'
import { api } from '../api'
import { Button } from './ui'

const MAC_DINH = [
  {
    icon: '🧭',
    tieu_de: 'Gia sư dẫn dắt, không cho đáp án',
    mo_ta: 'Gia sư sẽ đặt câu hỏi gợi mở để em tự tìm ra cách làm — đúng/sai do máy chấm '
      + '(CAS), không phải AI tự quyết định, và đáp án luôn được khóa tới khi em hoàn thành.',
  },
  {
    icon: '💡',
    tieu_de: 'Gợi ý có giới hạn, tăng dần',
    mo_ta: 'Nút "Gợi ý" hiện rõ số lượt còn lại (vd 2/3) — gợi ý sau cụ thể hơn gợi ý trước. '
      + 'Hết gợi ý mà vẫn chưa hiểu, em bấm "Nhờ thầy/cô" để được hỗ trợ trực tiếp.',
  },
  {
    icon: '✍️',
    tieu_de: 'Nhập công thức & hỏi tự do',
    mo_ta: 'Bấm vào bảng ký hiệu dưới ô trả lời để chèn phân số, căn, lũy thừa... Em cũng có '
      + 'thể gõ câu hỏi tự do (vd "vì sao lại làm vậy ạ?") vào ô chat để gia sư giải thích ngắn.',
  },
]

// open/onClose: điều khiển bởi PhongHoc.jsx (nút "Hướng dẫn").
export default function HuongDanPhongHoc({ open, onClose }) {
  const [cacBuoc, setCacBuoc] = useState(MAC_DINH)
  const [buoc, setBuoc] = useState(0)
  const [openTruoc, setOpenTruoc] = useState(open)

  useEffect(() => {
    api.hsHuongDanPhongHoc()
      .then((ds) => { if (ds?.length) setCacBuoc(ds) })
      .catch(() => {})
  }, [])

  // Mỗi lần mở lại, quay về bước 1 — xem lại từ đầu cho dễ theo dõi. Chỉnh state ngay
  // trong lúc render (không dùng effect) — đúng cách React khuyến nghị để reset state
  // theo prop đổi, tránh render lồng thêm 1 nhịp.
  if (open !== openTruoc) {
    setOpenTruoc(open)
    if (open) setBuoc(0)
  }

  if (!open) return null

  const b = cacBuoc[buoc]
  const dau = buoc === 0
  const cuoi = buoc === cacBuoc.length - 1

  return (
    <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4">
      <div className="bg-surface rounded-xl shadow-xl max-w-sm w-full p-5 flex flex-col gap-4">
        <div className="flex gap-1.5 justify-center">
          {cacBuoc.map((_, i) => (
            <span key={i}
              className={`h-1.5 w-6 rounded-full transition-colors ${i === buoc ? 'bg-primary' : 'bg-surface-2'}`} />
          ))}
        </div>
        <div className="text-center flex flex-col gap-2">
          <div className="text-3xl">{b.icon}</div>
          <p className="font-semibold text-ink">{b.tieu_de}</p>
          <p className="text-sm text-muted leading-relaxed">{b.mo_ta}</p>
        </div>
        <div className="flex justify-between gap-2">
          <Button variant="secondary" size="sm" onClick={onClose}>Đóng</Button>
          <div className="flex gap-2">
            {!dau && (
              <Button variant="secondary" size="sm" onClick={() => setBuoc((n) => n - 1)}>
                ← Quay lại
              </Button>
            )}
            {cuoi ? (
              <Button size="sm" onClick={onClose}>Đã hiểu</Button>
            ) : (
              <Button size="sm" onClick={() => setBuoc((n) => n + 1)}>Tiếp →</Button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
