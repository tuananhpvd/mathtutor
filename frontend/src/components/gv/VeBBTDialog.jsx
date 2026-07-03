import { useRef, useState } from 'react'
import { api } from '../../api'
import { Button } from '../ui'
import Formula from '../Formula'
import { svgSangPngFile } from '../../utils/svgSangPng'

// Lưới cột cách đều theo quy ước SGK (KHÔNG scale theo giá trị x thực — khác đồ thị).
const RONG = 560
const CAO = 260
const LE = 64
const PAD_PHAI = 24
const Y_HANG_X = 30
const Y_HANG_DAU = 78
const Y_TREN = 120
const Y_DUOI = 210

function dinhDangSo(v) {
  if (v == null) return ''
  if (Math.abs(v - Math.round(v)) < 1e-9) return String(Math.round(v))
  return String(Math.round(v * 1000) / 1000)
}

function textGiaTri(gt) {
  if (!gt) return ''
  if (gt.loai === 'vo_cuc_duong') return '+∞'
  if (gt.loai === 'vo_cuc_am') return '−∞'
  if (gt.loai === 'so') return dinhDangSo(gt.gia_tri)
  return '?'
}

// Xếp mức "trên"/"dưới" cho hàng y tại từng cột — lưới KHÔNG scale theo giá trị thực nên phải
// tự suy vị trí tương đối: giá trị ±∞ biết ngay (luôn trên/dưới cùng); giá trị hữu hạn (cực trị,
// hoặc 2 đầu khi có tiệm cận ngang) suy qua DẤU của khoảng liền kề — hàm tăng vào 1 điểm thì điểm
// đó ở mức cao hơn khoảng đó, hàm giảm vào 1 điểm thì điểm đó ở mức thấp hơn (và ngược lại ra khỏi).
function xepMuc(giaTriBien, khoangDau) {
  const mucTuLoai = (loai) => (loai === 'vo_cuc_duong' ? 'top' : loai === 'vo_cuc_am' ? 'bottom' : null)
  const cuoi = giaTriBien.length - 1
  return giaTriBien.map((e, i) => {
    if ('gia_tri' in e) {
      let muc = mucTuLoai(e.gia_tri.loai)
      if (!muc) {
        if (i === 0) muc = khoangDau[0].dau === 'am' ? 'top' : 'bottom'
        else if (i === cuoi) muc = khoangDau[khoangDau.length - 1].dau === 'duong' ? 'top' : 'bottom'
        else muc = khoangDau[i - 1].dau === 'duong' ? 'top' : 'bottom'
      }
      return { ...e, muc }
    }
    const mucTrai = mucTuLoai(e.trai.loai) || (khoangDau[i - 1].dau === 'duong' ? 'top' : 'bottom')
    const mucPhai = mucTuLoai(e.phai.loai) || (khoangDau[i].dau === 'duong' ? 'bottom' : 'top')
    return { ...e, mucTrai, mucPhai }
  })
}

const Y_TOP_BANG = 20 // mép trên khung bảng
const Y_BOT_BANG = CAO - 20 // mép dưới khung bảng
const X_NHAN = LE - 14 // đường kẻ dọc ngăn cột nhãn "x/y'/y" khỏi vùng dữ liệu

function BangBienThienSVG({ ketQua, svgRef }) {
  const { moc, khoang_dau: khoangDau, gia_tri_bien: giaTriBienGoc } = ketQua
  const N = moc.length
  const giaTriBien = xepMuc(giaTriBienGoc, khoangDau)
  const colX = (i) => LE + (i * (RONG - LE - PAD_PHAI)) / (N + 1)
  const yCua = (muc) => (muc === 'top' ? Y_TREN : Y_DUOI)

  return (
    <svg
      ref={svgRef}
      width={RONG}
      height={CAO}
      viewBox={`0 0 ${RONG} ${CAO}`}
      style={{ maxWidth: '100%', height: 'auto', background: '#fff' }}
    >
      <defs>
        <marker id="muiTenBBT" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto">
          <path d="M0,0 L10,5 L0,10 Z" fill="#000" />
        </marker>
      </defs>

      {/* Khung bảng: viền ngoài + kẻ ngang 3 hàng + kẻ dọc ngăn cột nhãn ("x"/"y'"/"y"). Không
          còn nét đơn dọc nào khác trong vùng dữ liệu — chỉ giữ 2 nét song song tại mốc gián đoạn. */}
      <rect x={0} y={Y_TOP_BANG} width={RONG} height={Y_BOT_BANG - Y_TOP_BANG} fill="none" stroke="#000" strokeWidth="1.2" />
      <line x1={0} y1={52} x2={RONG} y2={52} stroke="#000" strokeWidth="1" />
      <line x1={0} y1={98} x2={RONG} y2={98} stroke="#000" strokeWidth="1" />
      <line x1={X_NHAN} y1={Y_TOP_BANG} x2={X_NHAN} y2={Y_BOT_BANG} stroke="#000" strokeWidth="1" />
      {/* Kẻ dọc CHỈ tại mốc gián đoạn (hàm không xác định) — 2 nét song song xuyên suốt xuống
          hết hàng y, đúng quy ước SGK. Mốc cực trị KHÔNG kẻ gì (chỉ có "0" ở hàng y' là đủ). */}
      {giaTriBien.slice(1, -1).map((e, idx) => {
        if ('gia_tri' in e) return null
        const x0 = colX(idx + 1)
        return (
          <g key={`vd${idx}`}>
            <line x1={x0 - 1.5} y1={52} x2={x0 - 1.5} y2={Y_BOT_BANG} stroke="#000" strokeWidth="1" />
            <line x1={x0 + 1.5} y1={52} x2={x0 + 1.5} y2={Y_BOT_BANG} stroke="#000" strokeWidth="1" />
          </g>
        )
      })}

      {/* Nhãn hàng bên trái, trong ô riêng */}
      <text x={X_NHAN / 2} y={Y_HANG_X + 4} fontSize="14" fontStyle="italic" textAnchor="middle">x</text>
      <text x={X_NHAN / 2} y={Y_HANG_DAU + 4} fontSize="14" textAnchor="middle">y&apos;</text>
      <text x={X_NHAN / 2} y={(Y_TREN + Y_DUOI) / 2 + 4} fontSize="14" fontStyle="italic" textAnchor="middle">y</text>

      {/* Hàng x: nhãn mốc, cách đều */}
      {giaTriBien.map((_e, i) => (
        <text key={`x${i}`} x={colX(i)} y={Y_HANG_X + 4} fontSize="14" textAnchor="middle">
          {i === 0 ? '-∞' : i === N + 1 ? '+∞' : dinhDangSo(moc[i - 1])}
        </text>
      ))}

      {/* Hàng y': dấu +/− giữa mỗi khoảng */}
      {khoangDau.map((k, j) => {
        const xGiua = (colX(j) + colX(j + 1)) / 2
        return (
          <text key={`d${j}`} x={xGiua} y={Y_HANG_DAU + 6} fontSize="19" fontWeight="bold" textAnchor="middle">
            {k.dau === 'duong' ? '+' : k.dau === 'am' ? '−' : '?'}
          </text>
        )
      })}
      {/* Hàng y': "0" tại mốc cực trị. Mốc gián đoạn không cần chữ — đã có 2 nét dọc song song
          (vẽ ở khối kẻ dọc phía trên) tự thể hiện "hàm không xác định tại đây". */}
      {giaTriBien.slice(1, -1).map((e, idx) => (
        'gia_tri' in e ? (
          <text key={`m${idx + 1}`} x={colX(idx + 1)} y={Y_HANG_DAU + 5} fontSize="14" textAnchor="middle">0</text>
        ) : null
      ))}

      {/* Hàng y: đường nối có mũi tên giữa các cột liên tiếp trong cùng 1 khoảng — hướng theo dấu
          y'. Nếu đầu nào chạm mốc gián đoạn thì lùi vào GAP để không đè lên 2 nét song song. */}
      {khoangDau.map((_k, j) => {
        const xuatPhat = 'gia_tri' in giaTriBien[j] ? giaTriBien[j].muc : giaTriBien[j].mucPhai
        const denNoi = 'gia_tri' in giaTriBien[j + 1] ? giaTriBien[j + 1].muc : giaTriBien[j + 1].mucTrai
        const GAP = 5
        const x1 = 'gia_tri' in giaTriBien[j] ? colX(j) : colX(j) + GAP
        const x2 = 'gia_tri' in giaTriBien[j + 1] ? colX(j + 1) : colX(j + 1) - GAP
        return (
          <line key={`l${j}`} x1={x1} y1={yCua(xuatPhat)} x2={x2} y2={yCua(denNoi)}
            stroke="#000" strokeWidth="1.5" markerEnd="url(#muiTenBBT)" />
        )
      })}

      {/* Hàng y: giá trị tại từng cột — 1 giá trị, hoặc 2 giá trị TÁCH RỜI (không nối) nếu gián đoạn */}
      {giaTriBien.map((e, i) =>
        'gia_tri' in e ? (
          <text key={`v${i}`} x={colX(i)} y={yCua(e.muc) + (e.muc === 'top' ? -8 : 18)}
            fontSize="14" fontWeight="600" textAnchor="middle">
            {textGiaTri(e.gia_tri)}
          </text>
        ) : (
          // Gián đoạn: 2 nét dọc song song đã vẽ riêng (khối kẻ dọc phía trên) — ở đây chỉ dịch
          // số trái/phải ra 2 bên để KHÔNG đè lên nét kẻ (lỗi cũ: căn giữa làm nét cắt qua số).
          <g key={`v${i}`}>
            <text x={colX(i) - 8} y={yCua(e.mucTrai) + (e.mucTrai === 'top' ? -8 : 18)}
              fontSize="14" fontWeight="600" textAnchor="end">
              {textGiaTri(e.trai)}
            </text>
            <text x={colX(i) + 8} y={yCua(e.mucPhai) + (e.mucPhai === 'top' ? -8 : 18)}
              fontSize="14" fontWeight="600" textAnchor="start">
              {textGiaTri(e.phai)}
            </text>
          </g>
        )
      )}
    </svg>
  )
}

export default function VeBBTDialog({ initialSpec, onDong, onXongHinh }) {
  const [bieuThuc, setBieuThuc] = useState(initialSpec?.bieu_thuc || '')
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
      setKetQua(await api.veBBT({ bieu_thuc: bieuThuc.trim() }))
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
      const file = await svgSangPngFile(svgRef.current, 'bang-bien-thien.png', RONG, CAO)
      const { url } = await api.uploadHinh(file)
      onXongHinh(url, { loai: 'bang_bien_thien', bieu_thuc: bieuThuc.trim() })
    } catch (e) {
      setLoi(e.message)
    } finally {
      setDangDung(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-3xl flex flex-col max-h-[90vh]">
        <div className="px-5 pt-5 pb-3 border-b border-border flex-shrink-0">
          <h2 className="font-bold text-lg text-ink">Vẽ bảng biến thiên từ hàm số</h2>
          <p className="text-xs text-muted mt-0.5">
            Chỉ cần nhập f(x) — hệ thống tự tính chiều biến thiên và cực trị bằng CAS (không phải
            AI đoán).
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
            <Button onClick={ve} disabled={dangVe}>{dangVe ? 'Đang tính...' : 'Vẽ'}</Button>
          </div>

          {bieuThuc.trim() && (
            <p className="text-sm text-ink/70">
              Xem trước: <Formula latex={bieuThuc.trim()} />
            </p>
          )}

          {loi && <p className="text-sm text-danger bg-danger-soft rounded-md px-3 py-2">{loi}</p>}

          {ketQua && (
            <div className="overflow-x-auto">
              <BangBienThienSVG ketQua={ketQua} svgRef={svgRef} />
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
