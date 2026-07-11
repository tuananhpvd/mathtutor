/*
 * HuongDanPhongHoc — hướng dẫn 3 bước hiện đúng 1 LẦN cho HS khi vào phòng học, lưu trạng thái
 * "đã xem" ở server (User.da_xem_huong_dan_phong_hoc) chứ không dùng localStorage, để hướng
 * dẫn không hiện lại dù HS đổi máy/trình duyệt và không mất khi xóa dữ liệu trình duyệt.
 */

import { useEffect, useState } from 'react'
import { api } from '../api'
import { Button } from './ui'

const BUOC = [
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

export default function HuongDanPhongHoc() {
  const [hien, setHien] = useState(false)
  const [buoc, setBuoc] = useState(0)

  useEffect(() => {
    let con = true
    api.hsHoSo()
      .then((ho_so) => {
        if (con && !ho_so.da_xem_huong_dan_phong_hoc) setTimeout(() => setHien(true), 0)
      })
      .catch(() => {})
    return () => { con = false }
  }, [])

  function dong() {
    setHien(false)
    api.hsDaXemHuongDanPhongHoc().catch(() => {})
  }

  if (!hien) return null

  const b = BUOC[buoc]
  const cuoi = buoc === BUOC.length - 1

  return (
    <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4">
      <div className="bg-surface rounded-xl shadow-xl max-w-sm w-full p-5 flex flex-col gap-4">
        <div className="flex gap-1.5 justify-center">
          {BUOC.map((_, i) => (
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
          <Button variant="secondary" size="sm" onClick={dong}>Bỏ qua</Button>
          {cuoi ? (
            <Button size="sm" onClick={dong}>Bắt đầu học</Button>
          ) : (
            <Button size="sm" onClick={() => setBuoc((n) => n + 1)}>Tiếp →</Button>
          )}
        </div>
      </div>
    </div>
  )
}
