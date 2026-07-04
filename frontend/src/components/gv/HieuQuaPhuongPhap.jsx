/*
 * HieuQuaPhuongPhap — panel "minh chứng hiệu quả phương pháp gợi mở" cho GV (C2).
 * Dữ liệu tất định từ /progress/hieu-qua/lop (không LLM).
 *
 * Trực quan theo quy tắc dataviz:
 * - Phân bố mức gợi ý là thang THỨ BẬC (0 → 3+) → sequential 1 hue (tím thương hiệu)
 *   nhạt → đậm, ĐÃ validate (lightness band + chroma + CVD; 2 cảnh báo được xử lý
 *   bằng khe trắng 2px giữa các đoạn + nhãn chữ mực tối + bảng dữ liệu kèm theo).
 * - Chữ luôn dùng token chữ (text-ink/text-muted), không tô màu series lên chữ.
 * - Xu hướng trong bảng: icon + nhãn, không dựa vào màu đơn thuần.
 */

import { useEffect, useState } from 'react'
import { api } from '../../api'
import { Badge, Button, Card, CardBody, CardHeader } from '../ui'

// Sequential tím nhạt→đậm cho mức gợi ý 0/1/2/3+ (đã chạy validate_palette: PASS)
const MAU_MUC = ['#a294ea', '#8272e2', '#6353d0', '#4a3bc4']
const NHAN_MUC = ['Mức 0 — tự làm', 'Mức 1', 'Mức 2', 'Mức 3+']

function StatTile({ nhan, gia_tri, phu }) {
  return (
    <div className="rounded-lg bg-surface-2 px-4 py-3 flex flex-col gap-0.5 min-w-36">
      <p className="text-2xl font-bold text-ink leading-tight">{gia_tri}</p>
      <p className="text-xs text-muted leading-snug">{nhan}</p>
      {phu && <p className="text-[11px] text-muted">{phu}</p>}
    </div>
  )
}

function ThanhPhanBo({ pb }) {
  const gia_tri = [pb.muc_0, pb.muc_1, pb.muc_2, pb.muc_3_plus]
  if (!pb.tong) return null
  return (
    <div className="flex flex-col gap-2">
      {/* Thanh chồng ngang: khe trắng 2px giữa các đoạn (gap), đầu bo 4px */}
      <div className="flex h-7 rounded overflow-hidden gap-0.5 bg-surface">
        {gia_tri.map((v, i) => {
          if (!v) return null
          const pct = (v * 100) / pb.tong
          return (
            <div
              key={i}
              className="h-full first:rounded-l last:rounded-r"
              style={{ width: `${pct}%`, backgroundColor: MAU_MUC[i] }}
              title={`${NHAN_MUC[i]}: ${v} bài (${Math.round(pct)}%)`}
            />
          )
        })}
      </div>
      {/* Chú giải + nhãn số trực tiếp (chữ mực tối, không màu series) */}
      <div className="flex gap-x-4 gap-y-1 flex-wrap">
        {gia_tri.map((v, i) => (
          <span key={i} className="inline-flex items-center gap-1.5 text-xs text-ink">
            <span className="h-3 w-3 rounded-sm inline-block"
              style={{ backgroundColor: MAU_MUC[i] }} />
            {NHAN_MUC[i]}: <b>{v}</b>
            <span className="text-muted">({pb.tong ? Math.round((v * 100) / pb.tong) : 0}%)</span>
          </span>
        ))}
      </div>
    </div>
  )
}

function XuHuong({ xh }) {
  if (!xh?.du_du_lieu) return <span className="text-xs text-muted">— chưa đủ dữ liệu</span>
  if (xh.xu_huong === 'giam') {
    return <span className="text-xs text-success font-medium">↓ Giảm (tiến bộ)</span>
  }
  if (xh.xu_huong === 'tang') {
    return <span className="text-xs text-warning font-medium">↑ Tăng</span>
  }
  return <span className="text-xs text-muted font-medium">→ Ổn định</span>
}

export default function HieuQuaPhuongPhap() {
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  const [dangTai, setDangTai] = useState(false)

  useEffect(() => {
    api.getHieuQuaLop().then(setData).catch((e) => setError(e.message))
  }, [])

  async function taiCsv() {
    setDangTai(true)
    try { await api.taiCsvHieuQua() } catch (e) { setError(e.message) }
    finally { setDangTai(false) }
  }

  if (error) {
    return (
      <Card>
        <CardHeader title="Hiệu quả phương pháp gợi mở" />
        <CardBody><p className="text-sm text-danger">{error}</p></CardBody>
      </Card>
    )
  }
  if (!data) return null
  const pb = data.phan_bo_goi_y

  return (
    <Card>
      <CardHeader
        title="Hiệu quả phương pháp gợi mở"
        subtitle="Thống kê mô tả tính từ toàn bộ phiên đã hoàn thành — mức gợi ý cao nhất học sinh cần trước khi tự tìm ra đáp án. Dùng làm minh chứng báo cáo."
        action={
          <Button variant="secondary" size="sm" onClick={taiCsv} disabled={dangTai || !pb.tong}>
            {dangTai ? 'Đang tải...' : '⬇ Xuất CSV'}
          </Button>
        }
      />
      <CardBody className="flex flex-col gap-4">
        {!pb.tong ? (
          <p className="text-sm text-muted">
            Chưa có phiên hoàn thành nào — số liệu sẽ tự tích lũy khi học sinh luyện tập.
          </p>
        ) : (
          <>
            <div className="flex gap-3 flex-wrap">
              <StatTile nhan="tự làm không cần gợi ý" gia_tri={`${pb.ty_le_tu_lam}%`}
                phu={`${pb.muc_0}/${pb.tong} bài`} />
              <StatTile nhan="chỉ cần tối đa gợi ý mức 1 (định hướng)"
                gia_tri={`${pb.ty_le_muc_toi_da_1}%`} />
              <StatTile nhan="bài đã hoàn thành" gia_tri={pb.tong}
                phu={`${data.so_hoc_sinh} học sinh`} />
            </div>

            <ThanhPhanBo pb={pb} />

            {/* Bảng từng HS — đồng thời là "table view" cho phần trực quan phía trên */}
            <div className="overflow-x-auto">
              <table className="w-full text-sm border-collapse">
                <thead>
                  <tr className="text-muted text-xs border-b border-border">
                    <th className="py-2 pr-3 text-left font-medium">Học sinh</th>
                    <th className="py-2 pr-3 text-left font-medium">Lớp</th>
                    <th className="py-2 pr-3 text-right font-medium">Bài xong</th>
                    <th className="py-2 pr-3 text-right font-medium">% tự làm</th>
                    <th className="py-2 pr-3 text-right font-medium">
                      Gợi ý TB: 5 bài đầu → 5 gần nhất
                    </th>
                    <th className="py-2 text-left font-medium">Xu hướng phụ thuộc gợi ý</th>
                  </tr>
                </thead>
                <tbody>
                  {data.hoc_sinhs.map((r) => (
                    <tr key={r.hoc_sinh_id} className="border-b border-border/60">
                      <td className="py-2 pr-3 text-ink">{r.ho_ten}</td>
                      <td className="py-2 pr-3 text-muted">{r.lop_ten || '—'}</td>
                      <td className="py-2 pr-3 text-right text-ink">{r.so_bai}</td>
                      <td className="py-2 pr-3 text-right text-ink">
                        {r.ty_le_tu_lam == null ? '—' : `${r.ty_le_tu_lam}%`}
                      </td>
                      <td className="py-2 pr-3 text-right text-ink">
                        {r.xu_huong_goi_y.du_du_lieu
                          ? `${r.xu_huong_goi_y.dau} → ${r.xu_huong_goi_y.gan_nhat}`
                          : '—'}
                      </td>
                      <td className="py-2"><XuHuong xh={r.xu_huong_goi_y} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="text-[11px] text-muted">
              Mức gợi ý = mức cao nhất trong phiên (0 = tự làm hoàn toàn). Xu hướng so trung
              bình 5 bài đầu với 5 bài gần nhất của từng em; cần ≥ 10 bài mới hiện. Đây là
              thống kê mô tả trên dữ liệu lớp, không phải kiểm định thống kê.
            </p>
            {data.theo_tuan?.some((t) => t.so_bai > 0) && (
              <div className="flex gap-1.5 items-end flex-wrap">
                {data.theo_tuan.map((t) => (
                  <div key={t.tuan} className="flex flex-col items-center gap-0.5"
                    title={`${t.tuan}: ${t.so_bai} bài${t.goi_y_tb != null ? `, gợi ý TB ${t.goi_y_tb}` : ''}`}>
                    <span className="text-[10px] text-ink font-medium">{t.so_bai || ''}</span>
                    <div className="w-7 rounded-t bg-primary/70"
                      style={{ height: `${Math.min(48, t.so_bai * 8)}px`, minHeight: t.so_bai ? '4px' : '1px' }} />
                    <span className="text-[10px] text-muted">{t.tuan.slice(5)}</span>
                  </div>
                ))}
                <span className="text-[11px] text-muted ml-2 self-center">bài hoàn thành / tuần (8 tuần)</span>
              </div>
            )}
          </>
        )}
      </CardBody>
    </Card>
  )
}
