/*
 * BanDoNangLuc — heatmap năng lực chuyên đề × độ khó (C3).
 * Dùng chung cho HS (bản đồ của em), GV (bản đồ lớp / từng HS) qua prop `taiDuLieu`.
 *
 * Quy tắc dataviz: giá trị thành thạo 0–100 là MAGNITUDE → sequential 1 hue
 * (tím thương hiệu, nhạt → đậm, 5 bậc đơn điệu về lightness); số hiển thị trong
 * từng ô nên nhận diện không phụ thuộc màu; ô "chưa đủ dữ liệu" tách bạch hẳn
 * (xám + gạch chéo giả bằng viền đứt) khỏi ô yếu; có chú giải + tooltip.
 */

import { useEffect, useState } from 'react'
import { Card, CardBody, CardHeader } from './ui'

const NHAN_KHO = { de: 'Dễ', tb: 'Trung bình', kho: 'Khó' }
// 5 bậc tím nhạt→đậm (lightness đơn điệu, cùng họ ramp C2 đã validate)
const BAC = [
  { toi_thieu: 80, mau: '#4a3bc4', chu: '#ffffff', nhan: '80–100' },
  { toi_thieu: 60, mau: '#7867db', chu: '#ffffff', nhan: '60–79' },
  { toi_thieu: 40, mau: '#a294ea', chu: '#1a1a2e', nhan: '40–59' },
  { toi_thieu: 20, mau: '#c7bef4', chu: '#1a1a2e', nhan: '20–39' },
  { toi_thieu: 0, mau: '#ece9fb', chu: '#1a1a2e', nhan: '0–19' },
]

function bacCua(diem) {
  return BAC.find((b) => diem >= b.toi_thieu) || BAC[BAC.length - 1]
}

function O({ o, chuyen_de, dk }) {
  if (!o || o.diem_thanh_thao == null) {
    const ly_do = !o ? 'chưa làm bài nào' : 'có phiên nhưng chưa hoàn thành bài nào'
    return (
      <td className="p-1">
        <div
          className="h-11 rounded border border-dashed border-border bg-surface-2 grid place-items-center text-muted text-xs"
          title={`${chuyen_de} · ${NHAN_KHO[dk]}: chưa đủ dữ liệu (${ly_do})`}
        >
          —
        </div>
      </td>
    )
  }
  const b = bacCua(o.diem_thanh_thao)
  return (
    <td className="p-1">
      <div
        className="h-11 rounded grid place-items-center text-sm font-semibold"
        style={{ backgroundColor: b.mau, color: b.chu }}
        title={`${chuyen_de} · ${NHAN_KHO[dk]}: thành thạo ${o.diem_thanh_thao}/100 (${o.so_hoan_thanh}/${o.so_phien} bài hoàn thành)`}
      >
        {o.diem_thanh_thao}
      </div>
    </td>
  )
}

// `khoa`: giá trị đổi khi cần tải lại (vd id HS đang xem) — tránh phụ thuộc identity
// của hàm taiDuLieu (arrow mới mỗi render sẽ gây vòng lặp refetch).
export default function BanDoNangLuc({
  taiDuLieu, khoa = 'mac_dinh', tieu_de = 'Bản đồ năng lực', subtitle, action,
}) {
  const [data, setData] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    let con = true
    setTimeout(() => {
      if (!con) return
      setData(null)
      setError('')
      taiDuLieu().then((d) => con && setData(d)).catch((e) => con && setError(e.message))
    }, 0)
    return () => {
      con = false
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [khoa])

  if (error) return <p className="text-sm text-danger">{error}</p>
  if (!data) return <p className="text-sm text-muted">Đang tải bản đồ...</p>

  return (
    <Card>
      <CardHeader title={tieu_de} action={action}
        subtitle={subtitle || 'Điểm thành thạo 0–100 theo chuyên đề × độ khó — ô càng đậm càng vững; ô xám là chưa đủ dữ liệu (khác ô yếu).'} />
      <CardBody className="flex flex-col gap-3">
        {data.hang.length === 0 ? (
          <p className="text-sm text-muted">Chưa có dữ liệu — bản đồ sẽ tự tô màu khi luyện tập.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full border-collapse min-w-96">
              <thead>
                <tr className="text-xs text-muted">
                  <th className="text-left font-medium py-1 pr-2">Chuyên đề</th>
                  {data.cot.map((dk) => (
                    <th key={dk} className="font-medium py-1 w-24 sm:w-28">{NHAN_KHO[dk]}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.hang.map((h) => (
                  <tr key={h.chuyen_de}>
                    <td className="text-sm text-ink pr-2 py-1 max-w-40">
                      <span className="line-clamp-2">{h.chuyen_de}</span>
                    </td>
                    {data.cot.map((dk) => (
                      <O key={dk} o={h.o[dk]} chuyen_de={h.chuyen_de} dk={dk} />
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {/* Chú giải */}
        <div className="flex items-center gap-3 flex-wrap text-[11px] text-muted">
          <span>Thành thạo:</span>
          {[...BAC].reverse().map((b) => (
            <span key={b.nhan} className="inline-flex items-center gap-1">
              <span className="h-3 w-3 rounded-sm inline-block" style={{ backgroundColor: b.mau }} />
              {b.nhan}
            </span>
          ))}
          <span className="inline-flex items-center gap-1">
            <span className="h-3 w-3 rounded-sm inline-block bg-surface-2 border border-dashed border-border" />
            chưa đủ dữ liệu
          </span>
        </div>
      </CardBody>
    </Card>
  )
}
