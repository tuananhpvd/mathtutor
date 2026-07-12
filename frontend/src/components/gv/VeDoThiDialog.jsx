import { useRef, useState } from 'react'
import { api } from '../../api'
import { Button } from '../ui'
import Formula from '../Formula'
import { svgSangPngFile } from '../../utils/svgSangPng'

// Kích thước cố định của SVG xem trước — cũng là kích thước ảnh PNG xuất ra (x2 cho nét rõ).
const RONG = 480
const CAO = 360
const LE = 40

function dinhDangSo(v) {
  if (v == null) return ''
  if (Math.abs(v - Math.round(v)) < 1e-9) return String(Math.round(v))
  return String(Math.round(v * 1000) / 1000)
}

function DoThiSVG({ ketQua, svgRef }) {
  const { cua_so: cs, cac_doan, tiem_can_dung, tiem_can_ngang, tiem_can_xien, cuc_tri } = ketQua
  const sx = (x) => LE + ((x - cs.x_min) / (cs.x_max - cs.x_min)) * (RONG - 2 * LE)
  const sy = (y) => CAO - LE - ((y - cs.y_min) / (cs.y_max - cs.y_min)) * (CAO - 2 * LE)
  const coTrucX = cs.y_min <= 0 && 0 <= cs.y_max // Ox nằm trong khung nhìn
  const coTrucY = cs.x_min <= 0 && 0 <= cs.x_max // Oy nằm trong khung nhìn

  // Điểm đáng chú ý để chiếu nét đứt xuống Ox / sang Oy — KHÔNG dùng lưới chia đều chung
  // chung, đúng quy ước SGK: chỉ ghi số tại chỗ có ý nghĩa (cực trị, tiệm cận).
  const diemXDangChu = [...cuc_tri.map((c) => c.x), ...tiem_can_dung]
  const diemYDangChu = [...cuc_tri.map((c) => c.y), ...(tiem_can_ngang != null ? [tiem_can_ngang] : [])]

  return (
    <svg
      ref={svgRef}
      width={RONG}
      height={CAO}
      viewBox={`0 0 ${RONG} ${CAO}`}
      style={{ maxWidth: '100%', height: 'auto', background: '#fff' }}
    >
      <defs>
        <marker id="muiTenDoThi" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto">
          <path d="M0,0 L10,5 L0,10 Z" fill="#000" />
        </marker>
        <clipPath id="vungVeDoThi">
          <rect x={LE} y={LE} width={RONG - 2 * LE} height={CAO - 2 * LE} />
        </clipPath>
      </defs>

      {/* Trục Ox/Oy — mũi tên ở đầu dương (đúng quy ước SGK, không khung bao). Nhãn "x"/"y"/"O"
          vẽ SAU đường cong (cuối file) để không bao giờ bị nét vẽ đè lên. */}
      {coTrucX && (
        <line x1={LE - 6} y1={sy(0)} x2={RONG - LE + 10} y2={sy(0)} stroke="#000" strokeWidth="1.5" markerEnd="url(#muiTenDoThi)" />
      )}
      {coTrucY && (
        <line x1={sx(0)} y1={CAO - LE + 6} x2={sx(0)} y2={LE - 10} stroke="#000" strokeWidth="1.5" markerEnd="url(#muiTenDoThi)" />
      )}

      {/* Tiệm cận + đường cong — cắt trong vùng vẽ để không lấn nhãn trục */}
      <g clipPath="url(#vungVeDoThi)">
        {tiem_can_dung.map((xa, i) => (
          <line key={`tcd${i}`} x1={sx(xa)} y1={0} x2={sx(xa)} y2={CAO} stroke="#000" strokeWidth="1" strokeDasharray="4,3" />
        ))}
        {tiem_can_ngang != null && (
          <line x1={0} y1={sy(tiem_can_ngang)} x2={RONG} y2={sy(tiem_can_ngang)} stroke="#000" strokeWidth="1" strokeDasharray="4,3" />
        )}
        {tiem_can_xien && (
          <line
            x1={0} y1={sy(tiem_can_xien.a * cs.x_min + tiem_can_xien.b)}
            x2={RONG} y2={sy(tiem_can_xien.a * cs.x_max + tiem_can_xien.b)}
            stroke="#000" strokeWidth="1" strokeDasharray="4,3"
          />
        )}
        {/* Nét đứt chiếu cực trị xuống Ox / sang Oy — đúng quy ước "chiếu điểm" trong SGK */}
        {cuc_tri.map((c, i) => (
          <g key={`chieu${i}`}>
            {coTrucX && <line x1={sx(c.x)} y1={sy(c.y)} x2={sx(c.x)} y2={sy(0)} stroke="#000" strokeWidth="0.75" strokeDasharray="3,2" />}
            {coTrucY && <line x1={sx(c.x)} y1={sy(c.y)} x2={sx(0)} y2={sy(c.y)} stroke="#000" strokeWidth="0.75" strokeDasharray="3,2" />}
          </g>
        ))}
        {cac_doan.map((doan, i) => (
          <path
            key={i}
            d={doan.map((p, j) => `${j === 0 ? 'M' : 'L'} ${sx(p[0])},${sy(p[1])}`).join(' ')}
            fill="none"
            stroke="#000"
            strokeWidth="2"
          />
        ))}
      </g>

      {/* Cực trị: chấm nhỏ tại điểm, không ghi chữ "CĐ/CT" nổi trên hình (đã có số ở chân chiếu) */}
      {cuc_tri.map((c, i) => (
        <circle key={`cham${i}`} cx={sx(c.x)} cy={sy(c.y)} r="2.5" fill="#000" />
      ))}

      {/* Mọi chữ/số vẽ SAU CÙNG + viền trắng (halo) quanh glyph — nét vẽ nào đi qua bên dưới
          cũng bị halo che, chữ luôn đọc rõ, không cần tính toán tránh va chạm với đường cong. */}
      <g fill="#000" stroke="#fff" strokeWidth="3" strokeLinejoin="round" paintOrder="stroke">
        {coTrucX && <text x={RONG - LE + 12} y={sy(0) - 5} fontSize="12" fontStyle="italic">x</text>}
        {coTrucY && <text x={sx(0) + 6} y={LE - 12} fontSize="12" fontStyle="italic">y</text>}
        {coTrucX && coTrucY && <text x={sx(0) - 10} y={sy(0) + 14} fontSize="11">O</text>}
        {coTrucX && diemXDangChu.map((x0, i) => (
          <text key={`lx${i}`} x={sx(x0)} y={sy(0) + 16} fontSize="11" textAnchor="middle">{dinhDangSo(x0)}</text>
        ))}
        {coTrucY && diemYDangChu.map((y0, i) => (
          <text key={`ly${i}`} x={sx(0) - 8} y={sy(y0) + 4} fontSize="11" textAnchor="end">{dinhDangSo(y0)}</text>
        ))}
      </g>
    </svg>
  )
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
      const file = await svgSangPngFile(svgRef.current, 'do-thi.png', RONG, CAO)
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
      <div className="bg-surface rounded-xl shadow-xl w-full max-w-2xl flex flex-col max-h-[90vh]">
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
