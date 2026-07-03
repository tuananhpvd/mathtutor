import { useRef, useState } from 'react'
import { api } from '../../api'
import { Button } from '../ui'
import Formula from '../Formula'

// Kích thước cố định của SVG xem trước — cũng là kích thước ảnh PNG xuất ra (x2 cho nét rõ).
const RONG = 480
const CAO = 360
const LE = 40

function dinhDangSo(v) {
  if (v == null) return ''
  if (Math.abs(v - Math.round(v)) < 1e-9) return String(Math.round(v))
  return String(Math.round(v * 1000) / 1000)
}

// Chọn bước lưới "đẹp" (1/2/5 × 10^n) theo độ rộng khoảng — thuật toán chuẩn cho trục biểu đồ.
function buocDep(phamVi) {
  if (!(phamVi > 0)) return 1
  const tho = phamVi / 8
  const luyThua = Math.pow(10, Math.floor(Math.log10(tho)))
  const chuan = tho / luyThua
  const buoc = chuan < 1.5 ? 1 : chuan < 3 ? 2 : chuan < 7 ? 5 : 10
  return buoc * luyThua
}

function taoTick(min, max) {
  const buoc = buocDep(max - min)
  const ds = []
  const batDau = Math.ceil(min / buoc) * buoc
  for (let v = batDau; v <= max + 1e-9; v += buoc) {
    ds.push(Math.abs(v) < buoc / 1e6 ? 0 : Math.round(v * 1e6) / 1e6)
  }
  return ds
}

function DoThiSVG({ ketQua, svgRef }) {
  const { cua_so: cs, cac_doan, tiem_can_dung, tiem_can_ngang, tiem_can_xien, cuc_tri } = ketQua
  const sx = (x) => LE + ((x - cs.x_min) / (cs.x_max - cs.x_min)) * (RONG - 2 * LE)
  const sy = (y) => CAO - LE - ((y - cs.y_min) / (cs.y_max - cs.y_min)) * (CAO - 2 * LE)

  const ticksX = taoTick(cs.x_min, cs.x_max).filter((v) => v !== 0)
  const ticksY = taoTick(cs.y_min, cs.y_max).filter((v) => v !== 0)
  const coTrucX = cs.y_min <= 0 && 0 <= cs.y_max
  const coTrucY = cs.x_min <= 0 && 0 <= cs.x_max

  return (
    <svg
      ref={svgRef}
      width={RONG}
      height={CAO}
      viewBox={`0 0 ${RONG} ${CAO}`}
      className="rounded-md border border-border bg-white"
      style={{ maxWidth: '100%', height: 'auto' }}
    >
      <defs>
        <clipPath id="vungVeDoThi">
          <rect x={LE} y={LE} width={RONG - 2 * LE} height={CAO - 2 * LE} />
        </clipPath>
      </defs>

      {/* Lưới mờ */}
      {ticksX.map((v) => (
        <line key={`gx${v}`} x1={sx(v)} y1={LE} x2={sx(v)} y2={CAO - LE} stroke="#e5e7eb" strokeWidth="1" />
      ))}
      {ticksY.map((v) => (
        <line key={`gy${v}`} x1={LE} y1={sy(v)} x2={RONG - LE} y2={sy(v)} stroke="#e5e7eb" strokeWidth="1" />
      ))}

      {/* Trục Ox/Oy */}
      {coTrucX && <line x1={LE} y1={sy(0)} x2={RONG - LE} y2={sy(0)} stroke="#374151" strokeWidth="1.5" />}
      {coTrucY && <line x1={sx(0)} y1={LE} x2={sx(0)} y2={CAO - LE} stroke="#374151" strokeWidth="1.5" />}

      {/* Nhãn số trên trục */}
      {coTrucX && ticksX.map((v) => (
        <text key={`lx${v}`} x={sx(v)} y={sy(0) + 14} fontSize="10" textAnchor="middle" fill="#6b7280">
          {dinhDangSo(v)}
        </text>
      ))}
      {coTrucY && ticksY.map((v) => (
        <text key={`ly${v}`} x={sx(0) - 6} y={sy(v) + 3} fontSize="10" textAnchor="end" fill="#6b7280">
          {dinhDangSo(v)}
        </text>
      ))}

      {/* Tiệm cận + đường cong — cắt trong vùng vẽ để không lấn nhãn trục */}
      <g clipPath="url(#vungVeDoThi)">
        {tiem_can_dung.map((xa, i) => (
          <line key={`tcd${i}`} x1={sx(xa)} y1={0} x2={sx(xa)} y2={CAO} stroke="#f59e0b" strokeWidth="1.5" strokeDasharray="5,4" />
        ))}
        {tiem_can_ngang != null && (
          <line x1={0} y1={sy(tiem_can_ngang)} x2={RONG} y2={sy(tiem_can_ngang)} stroke="#f59e0b" strokeWidth="1.5" strokeDasharray="5,4" />
        )}
        {tiem_can_xien && (
          <line
            x1={0} y1={sy(tiem_can_xien.a * cs.x_min + tiem_can_xien.b)}
            x2={RONG} y2={sy(tiem_can_xien.a * cs.x_max + tiem_can_xien.b)}
            stroke="#f59e0b" strokeWidth="1.5" strokeDasharray="5,4"
          />
        )}
        {cac_doan.map((doan, i) => (
          <path
            key={i}
            d={doan.map((p, j) => `${j === 0 ? 'M' : 'L'} ${sx(p[0])},${sy(p[1])}`).join(' ')}
            fill="none"
            stroke="#2563eb"
            strokeWidth="2.5"
          />
        ))}
      </g>

      {/* Cực trị */}
      {cuc_tri.map((c, i) => (
        <g key={i}>
          <circle cx={sx(c.x)} cy={sy(c.y)} r="4" fill="#dc2626" />
          <text x={sx(c.x) + 6} y={sy(c.y) - 6} fontSize="10" fill="#dc2626">
            {c.loai === 'cuc_dai' ? 'CĐ' : 'CT'}({dinhDangSo(c.x)}; {dinhDangSo(c.y)})
          </text>
        </g>
      ))}

      <rect x={LE} y={LE} width={RONG - 2 * LE} height={CAO - 2 * LE} fill="none" stroke="#d1d5db" />
    </svg>
  )
}

// SVG (đã render trong DOM) -> PNG File, nền trắng, x2 độ phân giải cho nét rõ khi phóng to.
async function svgSangPngFile(svgEl, tenFile) {
  const xml = new XMLSerializer().serializeToString(svgEl)
  const url = URL.createObjectURL(new Blob([xml], { type: 'image/svg+xml;charset=utf-8' }))
  try {
    const img = new Image()
    await new Promise((resolve, reject) => {
      img.onload = resolve
      img.onerror = () => reject(new Error('Không chuyển được hình sang ảnh'))
      img.src = url
    })
    const canvas = document.createElement('canvas')
    canvas.width = RONG * 2
    canvas.height = CAO * 2
    const ctx = canvas.getContext('2d')
    ctx.fillStyle = '#ffffff'
    ctx.fillRect(0, 0, canvas.width, canvas.height)
    ctx.drawImage(img, 0, 0, canvas.width, canvas.height)
    const blob = await new Promise((resolve) => canvas.toBlob(resolve, 'image/png'))
    if (!blob) throw new Error('Không tạo được file ảnh')
    return new File([blob], tenFile, { type: 'image/png' })
  } finally {
    URL.revokeObjectURL(url)
  }
}

export default function VeDoThiDialog({ initialSpec, onDong, onXongHinh }) {
  const [bieuThuc, setBieuThuc] = useState(initialSpec?.bieu_thuc || '')
  const [xMin, setXMin] = useState(initialSpec?.x_min ?? '')
  const [xMax, setXMax] = useState(initialSpec?.x_max ?? '')
  const [dangVe, setDangVe] = useState(false)
  const [dangDung, setDangDung] = useState(false)
  const [loi, setLoi] = useState('')
  const [ketQua, setKetQua] = useState(null)
  const svgRef = useRef(null)

  async function ve() {
    if (!bieuThuc.trim()) { setLoi('Hãy nhập hàm số f(x).'); return }
    setLoi('')
    setDangVe(true)
    setKetQua(null)
    try {
      const body = { bieu_thuc: bieuThuc.trim() }
      const a = Number(xMin)
      const b = Number(xMax)
      if (xMin !== '' && xMax !== '' && !Number.isNaN(a) && !Number.isNaN(b) && b > a) {
        body.x_min = a
        body.x_max = b
      }
      setKetQua(await api.veDoThi(body))
    } catch (e) {
      setLoi(e.message)
    } finally {
      setDangVe(false)
    }
  }

  async function dungHinhNay() {
    if (!svgRef.current || !ketQua) return
    setDangDung(true)
    setLoi('')
    try {
      const file = await svgSangPngFile(svgRef.current, 'do-thi.png')
      const { url } = await api.uploadHinh(file)
      onXongHinh(url, {
        loai: 'do_thi',
        bieu_thuc: bieuThuc.trim(),
        x_min: ketQua.cua_so.x_min,
        x_max: ketQua.cua_so.x_max,
      })
    } catch (e) {
      setLoi(e.message)
    } finally {
      setDangDung(false)
    }
  }

  const khongCoMoc =
    ketQua &&
    ketQua.tiem_can_dung.length === 0 &&
    ketQua.tiem_can_ngang == null &&
    !ketQua.tiem_can_xien &&
    ketQua.cuc_tri.length === 0

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-2xl flex flex-col max-h-[90vh]">
        <div className="px-5 pt-5 pb-3 border-b border-border flex-shrink-0">
          <h2 className="font-bold text-lg text-ink">Vẽ đồ thị từ hàm số</h2>
          <p className="text-xs text-muted mt-0.5">
            Chỉ cần nhập f(x) — hệ thống tự tính tiệm cận, cực trị và vẽ đường cong bằng CAS
            (không phải AI đoán).
          </p>
        </div>

        <div className="overflow-y-auto flex-1 px-5 py-4 flex flex-col gap-3">
          <div className="flex gap-2 items-end flex-wrap">
            <div className="flex-1 min-w-[220px]">
              <p className="text-xs text-muted mb-1">Hàm số f(x)</p>
              <input
                value={bieuThuc}
                onChange={(e) => setBieuThuc(e.target.value)}
                placeholder="Ví dụ: x^3 - 3*x + 1  hoặc  (2*x-1)/(x+1)"
                className="w-full rounded-md border border-border bg-surface px-2.5 py-1.5 text-sm font-mono text-ink focus:border-primary focus:outline-none"
                onKeyDown={(e) => { if (e.key === 'Enter') ve() }}
              />
            </div>
            <div className="w-20">
              <p className="text-xs text-muted mb-1">x từ</p>
              <input
                value={xMin}
                onChange={(e) => setXMin(e.target.value)}
                placeholder="auto"
                className="w-full rounded-md border border-border bg-surface px-2 py-1.5 text-sm text-ink focus:border-primary focus:outline-none"
              />
            </div>
            <div className="w-20">
              <p className="text-xs text-muted mb-1">đến</p>
              <input
                value={xMax}
                onChange={(e) => setXMax(e.target.value)}
                placeholder="auto"
                className="w-full rounded-md border border-border bg-surface px-2 py-1.5 text-sm text-ink focus:border-primary focus:outline-none"
              />
            </div>
            <Button onClick={ve} disabled={dangVe}>{dangVe ? 'Đang vẽ...' : 'Vẽ'}</Button>
          </div>

          {bieuThuc.trim() && (
            <p className="text-sm text-ink/70">
              Xem trước: <Formula latex={bieuThuc.trim()} />
            </p>
          )}

          {loi && <p className="text-sm text-danger bg-danger-soft rounded-md px-3 py-2">{loi}</p>}

          {ketQua && (
            <div className="flex flex-col items-center gap-2">
              <DoThiSVG ketQua={ketQua} svgRef={svgRef} />
              <div className="text-xs text-muted flex flex-col gap-0.5 self-start">
                {ketQua.tiem_can_dung.map((x, i) => (
                  <p key={i}>Tiệm cận đứng: x = {dinhDangSo(x)}</p>
                ))}
                {ketQua.tiem_can_ngang != null && <p>Tiệm cận ngang: y = {dinhDangSo(ketQua.tiem_can_ngang)}</p>}
                {ketQua.tiem_can_xien && (
                  <p>Tiệm cận xiên: y = {dinhDangSo(ketQua.tiem_can_xien.a)}x + {dinhDangSo(ketQua.tiem_can_xien.b)}</p>
                )}
                {ketQua.cuc_tri.map((c, i) => (
                  <p key={i}>
                    {c.loai === 'cuc_dai' ? 'Cực đại' : 'Cực tiểu'} tại x = {dinhDangSo(c.x)}, y = {dinhDangSo(c.y)}
                  </p>
                ))}
                {khongCoMoc && <p>Hàm không có tiệm cận/cực trị đáng chú ý trong miền xác định.</p>}
              </div>
            </div>
          )}
        </div>

        <div className="px-5 py-4 border-t border-border flex-shrink-0 flex gap-2 justify-end">
          <Button variant="secondary" onClick={onDong} disabled={dangDung}>Hủy</Button>
          {ketQua && (
            <Button onClick={dungHinhNay} disabled={dangDung}>
              {dangDung ? 'Đang lưu...' : 'Dùng hình này'}
            </Button>
          )}
        </div>
      </div>
    </div>
  )
}
