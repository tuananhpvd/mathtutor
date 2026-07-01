import { phanTachTg } from '../utils/format'

// Dùng inline sau tên: · HH:MM:SS · DD/MM/YYYY (với dấu · đậm ink)
export default function ThoiGianPhanCach({ iso }) {
  const tg = phanTachTg(iso)
  if (!tg) return null
  return (
    <>
      <span className="font-bold text-ink mx-0.5">·</span>
      <span>{tg.gio}</span>
      <span className="font-bold text-ink mx-0.5">·</span>
      <span>{tg.ngay}</span>
    </>
  )
}

// Dùng trong ô bảng: HH:MM:SS · DD/MM/YYYY
export function CotThoiGian({ iso }) {
  const tg = phanTachTg(iso)
  if (!tg) return <span className="text-muted">—</span>
  return (
    <span className="whitespace-nowrap">
      {tg.gio}
      <span className="font-bold text-ink mx-1">·</span>
      {tg.ngay}
    </span>
  )
}
