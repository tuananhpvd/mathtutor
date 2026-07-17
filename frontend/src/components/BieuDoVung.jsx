import { useId, useState } from 'react'
import { Card, CardBody, CardHeader } from './ui'

/* BieuDoVung — biểu đồ VÙNG làm mượt theo ngày (area chart): 1 chuỗi đếm được theo thời
   gian liên tục, vùng tô gradient = "khối lượng/nhịp" hoạt động. SVG thuần, không thư viện.
   Làm mượt kiểu MONOTONE (Fritsch–Carlson) — không "võng" quá giá trị thật, các đoạn 0 nằm
   phẳng đúng 0 (spline thường sẽ vẽ giá trị âm/đỉnh ảo với số nguyên nhỏ).

   Props:
   - ds: [{ngay: 'YYYY-MM-DD', so: number, ...}] — chuỗi LIÊN TỤC (ngày trống vẫn có, so=0).
   - mau: màu đường/vùng (var(--color-...) theo token).
   - donVi: nhãn đơn vị trong tooltip (vd 'bài hoàn thành').
   - tieu_de/phu_de: header card.
   - tach?: (item) => string — dòng tách chi tiết trong tooltip (vd cờ/nhờ thầy cô).
*/

const W = 620
const H = 200
const LE = 34    // lề trái (nhãn trục tung)
const PHAI = 8
const TREN = 10
const DUOI = 24  // lề dưới (nhãn ngày)
const BUOC_DEP = [1, 2, 5, 10, 20, 50, 100, 200, 500, 1000]

// Nội suy monotone Fritsch–Carlson → path Bezier mượt, không vượt quá dữ liệu thật.
function duongMuot(p) {
  const n = p.length
  if (n < 2) return ''
  const dx = []
  const m = []
  const t = new Array(n)
  for (let i = 0; i < n - 1; i++) {
    dx[i] = p[i + 1].x - p[i].x
    m[i] = (p[i + 1].y - p[i].y) / dx[i]
  }
  t[0] = m[0]
  t[n - 1] = m[n - 2]
  for (let i = 1; i < n - 1; i++) t[i] = m[i - 1] * m[i] <= 0 ? 0 : (m[i - 1] + m[i]) / 2
  for (let i = 0; i < n - 1; i++) {
    if (m[i] === 0) { t[i] = 0; t[i + 1] = 0; continue }
    const a = t[i] / m[i]
    const b = t[i + 1] / m[i]
    const s = a * a + b * b
    if (s > 9) {
      const tau = 3 / Math.sqrt(s)
      t[i] = tau * a * m[i]
      t[i + 1] = tau * b * m[i]
    }
  }
  let d = `M${p[0].x.toFixed(1)},${p[0].y.toFixed(1)}`
  for (let i = 0; i < n - 1; i++) {
    d += `C${(p[i].x + dx[i] / 3).toFixed(1)},${(p[i].y + (t[i] * dx[i]) / 3).toFixed(1)} ` +
      `${(p[i + 1].x - dx[i] / 3).toFixed(1)},${(p[i + 1].y - (t[i + 1] * dx[i]) / 3).toFixed(1)} ` +
      `${p[i + 1].x.toFixed(1)},${p[i + 1].y.toFixed(1)}`
  }
  return d
}

const nhanNgay = (iso) => {
  const [, m, d] = iso.split('-')
  return `${d}/${m}`
}
const nhanNgayDu = (iso) => {
  const [y, m, d] = iso.split('-')
  return `${d}/${m}/${y}`
}

export default function BieuDoVung({ ds, mau = 'var(--color-primary)', donVi = '',
  tieu_de, phu_de, tach }) {
  // useId có thể chứa ':' — bỏ đi để dùng được trong url(#...) của SVG.
  const gid = `bdv${useId().replace(/:/g, '')}`
  const [hover, setHover] = useState(null)
  if (!ds?.length) return null

  const n = ds.length
  const coHoatDong = ds.some((d) => d.so > 0)
  const maxV = Math.max(...ds.map((d) => d.so), 1)
  const buoc = BUOC_DEP.find((b) => Math.ceil(maxV / b) <= 4) ?? Math.ceil(maxV / 4)
  const yMax = buoc * Math.ceil(maxV / buoc)
  const X = (i) => LE + ((W - LE - PHAI) * i) / (n - 1)
  const Y = (v) => TREN + (H - TREN - DUOI) * (1 - v / yMax)
  const pts = ds.map((d, i) => ({ x: X(i), y: Y(d.so) }))
  const duong = duongMuot(pts)
  const vung = `${duong}L${X(n - 1).toFixed(1)},${Y(0)}L${X(0).toFixed(1)},${Y(0)}Z`

  const vachTruc = []
  for (let v = 0; v <= yMax; v += buoc) vachTruc.push(v)
  const nhanX = []
  for (let i = 0; i < n; i += 7) nhanX.push(i)

  function onMove(e) {
    const r = e.currentTarget.getBoundingClientRect()
    const mx = ((e.clientX - r.left) / r.width) * W
    const i = Math.max(0, Math.min(n - 1, Math.round(((mx - LE) / (W - LE - PHAI)) * (n - 1))))
    setHover(i)
  }

  return (
    <Card>
      <CardHeader title={tieu_de} subtitle={phu_de} />
      <CardBody>
        {!coHoatDong ? (
          <p className="text-sm text-muted">Chưa có hoạt động nào trong 30 ngày gần đây.</p>
        ) : (
          <div className="relative">
            <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-auto block" role="img"
              aria-label={tieu_de} onMouseMove={onMove} onMouseLeave={() => setHover(null)}>
              <defs>
                <linearGradient id={gid} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={mau} stopOpacity="0.32" />
                  <stop offset="100%" stopColor={mau} stopOpacity="0.02" />
                </linearGradient>
              </defs>
              {vachTruc.map((v) => (
                <g key={v}>
                  <line x1={LE} y1={Y(v)} x2={W - PHAI} y2={Y(v)}
                    stroke="var(--color-border)" strokeWidth="1" />
                  <text x={LE - 6} y={Y(v) + 3.5} textAnchor="end" fontSize="10"
                    fill="var(--color-muted)">{v}</text>
                </g>
              ))}
              <path d={vung} fill={`url(#${gid})`} />
              <path d={duong} fill="none" stroke={mau} strokeWidth="2" strokeLinecap="round" />
              {nhanX.map((i) => (
                <text key={i} x={X(i)} y={H - 7} textAnchor="middle" fontSize="10"
                  fill="var(--color-muted)">{nhanNgay(ds[i].ngay)}</text>
              ))}
              {hover != null && (
                <g pointerEvents="none">
                  <line x1={X(hover)} x2={X(hover)} y1={TREN} y2={Y(0)}
                    stroke={mau} strokeWidth="1" strokeDasharray="3 3" />
                  <circle cx={X(hover)} cy={Y(ds[hover].so)} r="3.5" fill={mau}
                    stroke="var(--color-surface)" strokeWidth="1.5" />
                </g>
              )}
            </svg>
            {hover != null && (
              <div className="absolute pointer-events-none bg-ink text-white text-xs rounded-lg
                px-2.5 py-1.5 leading-snug whitespace-nowrap shadow-[var(--shadow-pop)] z-10"
                style={{
                  left: `${(X(hover) / W) * 100}%`,
                  top: `${(Y(ds[hover].so) / H) * 100}%`,
                  transform: 'translate(-50%, -115%)',
                }}>
                <span className="opacity-75">{nhanNgayDu(ds[hover].ngay)}</span><br />
                <b>{ds[hover].so}</b> {donVi}
                {tach && <><br /><span className="opacity-75">{tach(ds[hover])}</span></>}
              </div>
            )}
          </div>
        )}
      </CardBody>
    </Card>
  )
}
