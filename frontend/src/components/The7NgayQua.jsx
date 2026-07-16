import { Card, CardBody, CardHeader } from './ui'
import { dinhDangThoiGian } from '../utils/format'

// Nền nhẹ riêng cho từng ô — thuần phân biệt trực quan (không mang nghĩa đúng/sai), cùng
// tông đã dùng nhất quán ở nơi khác của app (Nhiệm vụ/Mục tiêu/Luyện đề, Tổng/Nhanh/Chậm).
const TONE_BG = { primary: 'bg-primary-soft', accent: 'bg-accent-soft', warning: 'bg-warning-soft' }
const TONE_TXT = { primary: 'text-primary', accent: 'text-accent', warning: 'text-warning-ink' }

/* Ô so sánh 7 ngày qua vs 7 ngày trước. totKhiTang: tăng là tốt (số bài) hay giảm là tốt
   (thời gian, gợi ý). Backend trả số thô 2 kỳ — màu/mũi tên quyết định ở đây.
   Mũi tên ▲/▼ cỡ lớn trong huy hiệu nền màu + kèm mức chênh lệch để nổi bật, nhìn là thấy. */
function TheSoSanh({ nhan, nay, truoc, fmt = (v) => v, fmtDelta = null, totKhiTang = true, tone = 'primary' }) {
  const coNay = nay != null
  const coTruoc = truoc != null
  let mui = null
  if (coNay && coTruoc) {
    if (nay === truoc) {
      mui = (
        <span className="inline-flex items-center rounded-lg bg-surface px-2 py-0.5
          text-muted text-lg font-black leading-none" title="Không đổi so với 7 ngày trước">
          →
        </span>
      )
    } else {
      const tang = nay > truoc
      const tot = tang === totKhiTang
      const chenh = Math.abs(Math.round((nay - truoc) * 10) / 10)
      mui = (
        <span className={`inline-flex items-center gap-1 rounded-lg px-2 py-0.5
            ${tot ? 'text-success bg-success-soft' : 'text-warning bg-warning-soft'}`}
          title={`${tang ? 'Tăng' : 'Giảm'} so với 7 ngày trước${tot ? ' — chiều hướng tốt' : ''}`}>
          <span className="text-2xl font-black leading-none">{tang ? '▲' : '▼'}</span>
          <b className="text-sm">{fmtDelta ? fmtDelta(chenh) : chenh}</b>
        </span>
      )
    }
  }
  return (
    <div className={`rounded-lg px-4 py-3 flex-1 min-w-[150px] ${TONE_BG[tone]}`}>
      <p className="text-xs text-muted">{nhan}</p>
      <div className="flex items-center justify-between gap-2 flex-wrap mt-0.5">
        <p className={`text-xl font-bold ${TONE_TXT[tone]}`}>{coNay ? fmt(nay) : '—'}</p>
        {mui}
      </div>
      <p className="text-[11px] text-muted mt-0.5">7 ngày trước: {coTruoc ? fmt(truoc) : '—'}</p>
    </div>
  )
}

// Card "so sánh 7 ngày qua vs 7 ngày trước" dùng chung (Tiến độ chi tiết + Trang chủ HS).
// ss: tk.so_sanh_7_ngay = {ky_nay:{so_bai,thoi_gian_tb_giay,goi_y_tb}, ky_truoc:{...}}.
export default function The7NgayQua({ ss, title = '7 ngày qua so với 7 ngày trước', className = '' }) {
  if (!ss) return null
  return (
    <Card className={className}>
      <CardHeader title={title}
        subtitle="Làm nhiều bài hơn, nhanh hơn, ít cần gợi ý hơn = đang tiến bộ" />
      <CardBody className="flex flex-col gap-3">
        <TheSoSanh nhan="Bài hoàn thành" nay={ss.ky_nay.so_bai} truoc={ss.ky_truoc.so_bai}
          totKhiTang tone="primary" />
        <TheSoSanh nhan="Thời gian TB mỗi bài" nay={ss.ky_nay.thoi_gian_tb_giay}
          truoc={ss.ky_truoc.thoi_gian_tb_giay} fmt={dinhDangThoiGian}
          fmtDelta={dinhDangThoiGian} totKhiTang={false} tone="accent" />
        <TheSoSanh nhan="Lượt cần gợi ý TB mỗi bài" nay={ss.ky_nay.goi_y_tb}
          truoc={ss.ky_truoc.goi_y_tb} totKhiTang={false} tone="warning" />
      </CardBody>
    </Card>
  )
}
