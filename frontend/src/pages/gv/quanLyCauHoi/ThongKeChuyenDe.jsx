import { useState } from 'react'
import { Badge, Card, CardBody } from '../../../components/ui'
import { NHAN_LOAI } from './constants'

// Đếm câu hỏi trong 1 danh sách theo mức độ — dùng cho tổng quan đầu trang.
function demTheoMuc(list) {
  const kho = { de: 0, tb: 0, kho: 0 }
  for (const r of list) if (kho[r.do_kho] != null) kho[r.do_kho]++
  return { kho, tong: list.length }
}

// Ma trận loại câu × mức độ — dùng cho bảng chi tiết mỗi chuyên đề.
function demChoBangCheo(list) {
  const bang = { TN4PA: { de: 0, tb: 0, kho: 0 }, TNDS: { de: 0, tb: 0, kho: 0 }, TLN: { de: 0, tb: 0, kho: 0 } }
  for (const r of list) {
    if (bang[r.loai_cau] && bang[r.loai_cau][r.do_kho] != null) bang[r.loai_cau][r.do_kho]++
  }
  return bang
}

// Mức độ là thang có thứ bậc (Dễ→Khó) nên dùng đúng bộ màu trạng thái đã có sẵn trong app
// (thành công/cảnh báo/lỗi) — nhất quán với ThongKeTienDo.jsx, không tự bịa màu mới.
const MUC_DO_CFG = [
  { key: 'de', label: 'Dễ', nhanDay: 'Mức Dễ', dot: 'bg-success', fill: 'bg-success',
    text: 'text-success', soft: 'bg-success-soft', border: 'border-success/30' },
  { key: 'tb', label: 'TB', nhanDay: 'Trung bình', dot: 'bg-warning', fill: 'bg-warning',
    text: 'text-warning', soft: 'bg-warning-soft', border: 'border-warning/30' },
  { key: 'kho', label: 'Khó', nhanDay: 'Mức Khó', dot: 'bg-danger', fill: 'bg-danger',
    text: 'text-danger', soft: 'bg-danger-soft', border: 'border-danger/30' },
]

// Thanh tỉ lệ mức độ — mảnh (h-2), có khe 2px giữa các đoạn, rỗng thì hiện nền trơn.
function ThanhMucDo({ kho, tong }) {
  return (
    <div className="flex h-2 w-full gap-[2px] rounded-full overflow-hidden bg-surface-2">
      {tong > 0 && MUC_DO_CFG.map(({ key, fill, label }) => {
        const n = kho[key]
        if (n === 0) return null
        return (
          <div key={key} className={fill} title={`${label}: ${n} câu`}
            style={{ width: `${(n / tong) * 100}%` }} />
        )
      })}
    </div>
  )
}

// Tổng quan đầu trang (giống hình 1 user gửi): tổng câu hỏi + tổng theo mức độ, TÍNH TRÊN
// TOÀN BỘ chuyên đề, không phụ thuộc chuyên đề nào đang mở.
function TomTatTongQuan({ rows }) {
  const { kho, tong } = demTheoMuc(rows)
  const pct = (n) => (tong > 0 ? Math.round((n / tong) * 100) : 0)
  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-2.5">
      <div className="rounded-lg border border-primary/30 bg-primary-soft px-3 py-2.5">
        <div className="flex items-center justify-between">
          <span className="text-xs text-muted">Tổng câu hỏi</span>
          <span className="text-primary text-sm font-bold">#</span>
        </div>
        <p className="text-xl font-bold text-primary">{tong.toLocaleString('vi-VN')}</p>
        <p className="text-[11px] text-muted">100% tổng chuyên đề</p>
      </div>
      {MUC_DO_CFG.map((m) => (
        <div key={m.key} className={`rounded-lg border px-3 py-2.5 ${m.border} ${m.soft}`}>
          <div className="flex items-center justify-between">
            <span className="text-xs text-muted">{m.nhanDay}</span>
            <span className={`h-2.5 w-2.5 rounded-full inline-block ${m.dot}`} />
          </div>
          <p className={`text-xl font-bold ${m.text}`}>{kho[m.key].toLocaleString('vi-VN')}</p>
          <p className="text-[11px] text-muted">{pct(kho[m.key])}% tổng chuyên đề</p>
        </div>
      ))}
    </div>
  )
}

// Bảng chi tiết 1 chuyên đề khi mở (giống hình 2 user gửi): loại câu × mức độ + dòng Tổng
// + thanh tỉ lệ mức độ bên dưới.
function BangChiTietChuyenDe({ list }) {
  const bang = demChoBangCheo(list)
  const tongTheoMuc = { de: 0, tb: 0, kho: 0 }
  for (const l of ['TN4PA', 'TNDS', 'TLN']) {
    for (const k of ['de', 'tb', 'kho']) tongTheoMuc[k] += bang[l][k]
  }
  const tongTatCa = tongTheoMuc.de + tongTheoMuc.tb + tongTheoMuc.kho

  return (
    <div className="flex flex-col gap-3">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-xs text-muted uppercase tracking-wide border-b border-border">
              <th className="text-left font-medium py-1.5 pr-2">Loại câu</th>
              {MUC_DO_CFG.map((m) => (
                <th key={m.key} className={`text-right font-medium py-1.5 px-2 ${m.text}`}>{m.label}</th>
              ))}
              <th className="text-right font-medium py-1.5 pl-2">Tổng</th>
            </tr>
          </thead>
          <tbody>
            {['TN4PA', 'TNDS', 'TLN'].map((l) => {
              const r = bang[l]
              const t = r.de + r.tb + r.kho
              return (
                <tr key={l} className="border-b border-border/60 last:border-0">
                  <td className="py-1.5 pr-2 font-medium text-ink">{l}</td>
                  {MUC_DO_CFG.map((m) => (
                    <td key={m.key} className="text-right py-1.5 px-2 text-ink">{r[m.key]}</td>
                  ))}
                  <td className="text-right py-1.5 pl-2 font-semibold text-ink">{t}</td>
                </tr>
              )
            })}
            <tr className="border-t-2 border-border">
              <td className="py-1.5 pr-2 font-bold text-ink">Tổng</td>
              {MUC_DO_CFG.map((m) => (
                <td key={m.key} className={`text-right py-1.5 px-2 font-bold ${m.text}`}>{tongTheoMuc[m.key]}</td>
              ))}
              <td className="text-right py-1.5 pl-2 font-bold text-primary">{tongTatCa}</td>
            </tr>
          </tbody>
        </table>
      </div>
      {tongTatCa > 0 && (
        <div className="flex flex-col gap-1.5">
          <ThanhMucDo kho={tongTheoMuc} tong={tongTatCa} />
          <div className="flex items-center gap-3 text-xs text-muted">
            {MUC_DO_CFG.map((m) => (
              <span key={m.key} className="inline-flex items-center gap-1">
                <span className={`h-2 w-2 rounded-full inline-block ${m.dot}`} />
                {m.label} {Math.round((tongTheoMuc[m.key] / tongTatCa) * 100)}%
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

// Tổng quan 1 chuyên đề khi mở: 4 thẻ (tổng + Dễ/TB/Khó, kèm % trong chính chuyên đề này),
// rồi 3 thẻ theo loại câu (mỗi thẻ kèm số Dễ/TB/Khó bên phải) — hiện TRƯỚC lưới dạng bên dưới.
function TongQuanChuyenDe({ list }) {
  const { kho, tong } = demTheoMuc(list)
  const bang = demChoBangCheo(list)
  const pct = (n) => (tong > 0 ? Math.round((n / tong) * 100) : 0)

  return (
    <div className="flex flex-col gap-2.5 mb-3">
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-2.5">
        <div className="rounded-lg border border-primary/30 bg-primary-soft px-3 py-2.5">
          <div className="flex items-center justify-between">
            <span className="text-xs text-muted">Tổng câu hỏi</span>
            <span className="text-primary text-sm font-bold">#</span>
          </div>
          <p className="text-xl font-bold text-primary">{tong}</p>
          <p className="text-[11px] text-muted">100% chuyên đề này</p>
        </div>
        {MUC_DO_CFG.map((m) => (
          <div key={m.key} className={`rounded-lg border px-3 py-2.5 ${m.border} ${m.soft}`}>
            <div className="flex items-center justify-between">
              <span className="text-xs text-muted">{m.nhanDay}</span>
              <span className={`h-2.5 w-2.5 rounded-full inline-block ${m.dot}`} />
            </div>
            <p className={`text-xl font-bold ${m.text}`}>{kho[m.key]}</p>
            <p className="text-[11px] text-muted">{pct(kho[m.key])}% chuyên đề này</p>
          </div>
        ))}
      </div>
      <div className="grid sm:grid-cols-3 gap-2.5">
        {['TN4PA', 'TNDS', 'TLN'].map((l) => {
          const r = bang[l]
          const t = r.de + r.tb + r.kho
          return (
            <div key={l} className="rounded-lg border border-border bg-surface px-3 py-2.5 flex items-center gap-3">
              <span className="shrink-0 h-9 w-9 rounded-full bg-primary-soft text-primary text-xs font-bold grid place-items-center">
                {l === 'TLN' ? 'TL' : 'TN'}
              </span>
              <div className="min-w-0 flex-1">
                <p className="text-xs text-muted truncate">{NHAN_LOAI[l]}</p>
                <p className="text-lg font-bold text-ink">{t}</p>
              </div>
              <div className="text-[11px] text-right shrink-0 leading-tight">
                <p className="font-semibold text-success">{r.de} <span className="text-muted font-normal">Dễ</span></p>
                <p className="font-semibold text-warning">{r.tb} <span className="text-muted font-normal">TB</span></p>
                <p className="font-semibold text-danger">{r.kho} <span className="text-muted font-normal">Khó</span></p>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

// Thẻ 1 dạng trong chuyên đề đang mở: tên dạng + số câu, bên trong là bảng chi tiết loại
// câu × mức độ của riêng dạng đó. Xếp 2 cột trong lưới ở component cha.
function TheDangChiTiet({ ten, list, nhan }) {
  return (
    <div className={`rounded-lg border px-3 py-3 flex flex-col gap-2 ${
      nhan ? 'border-dashed border-border bg-transparent' : 'border-border bg-surface'
    }`}>
      <div className="flex items-center justify-between gap-2">
        <span className={`text-sm font-semibold truncate ${nhan ? 'text-muted italic' : 'text-ink'}`}>{ten}</span>
        <Badge tone="primary" className="shrink-0">{list.length} câu</Badge>
      </div>
      {list.length > 0 && <BangChiTietChuyenDe list={list} />}
    </div>
  )
}

// Thống kê ngân hàng câu hỏi: tổng quan toàn bộ (hình 1) + từng chuyên đề (thu gọn, bấm mới
// mở, hiện bảng loại câu × mức độ như hình 2). Đếm TẤT CẢ trạng thái duyệt, không phụ thuộc
// bộ lọc "Lọc trạng thái duyệt" bên dưới.
export function ThongKeChuyenDe({ danhMuc, rows }) {
  const [moRong, setMoRong] = useState(() => new Set())
  function toggle(id) {
    setMoRong((s) => {
      const moi = new Set(s)
      if (moi.has(id)) moi.delete(id); else moi.add(id)
      return moi
    })
  }

  if (danhMuc.length === 0) return null

  return (
    <Card className="overflow-hidden">
      <div className="border-l-4 border-primary">
        <CardBody className="flex flex-col gap-3 pt-5">
          <p className="text-sm font-bold text-ink">📊 Thống kê ngân hàng câu hỏi</p>
          <TomTatTongQuan rows={rows} />
          <div className="flex flex-col gap-2.5">
            {danhMuc.map((cd) => {
              const dangIds = new Set(cd.dang_list.map((d) => d.id))
              const cauChuyenDe = rows.filter((r) => r.chuyen_de === cd.ten || dangIds.has(r.dang_id))
              const chuaPhanDang = cauChuyenDe.filter((r) => !dangIds.has(r.dang_id))
              const isOpen = moRong.has(cd.id)
              return (
                <div key={cd.id} className="rounded-lg border border-border overflow-hidden">
                  <button type="button" onClick={() => toggle(cd.id)}
                    className={`w-full flex items-center justify-between gap-3 px-4 py-3 text-left transition-colors ${
                      isOpen ? 'bg-primary-soft' : 'bg-surface-2 hover:bg-primary-soft/60'
                    }`}>
                    <span className="flex items-center gap-2 font-semibold text-ink text-sm">
                      <span className={`inline-block transition-transform text-primary ${isOpen ? 'rotate-90' : ''}`}>▸</span>
                      {cd.ten}
                    </span>
                    <Badge tone="primary" className="shrink-0">{cauChuyenDe.length} câu</Badge>
                  </button>
                  {isOpen && (
                    <div className="px-4 py-3 bg-surface">
                      {cauChuyenDe.length > 0 && <TongQuanChuyenDe list={cauChuyenDe} />}
                      {cd.dang_list.length === 0 && chuaPhanDang.length === 0 ? (
                        <p className="text-xs text-muted py-1">Chưa có dạng nào.</p>
                      ) : (
                        <div className="grid sm:grid-cols-2 gap-3">
                          {cd.dang_list.map((d) => (
                            <TheDangChiTiet key={d.id} ten={d.ten} list={rows.filter((r) => r.dang_id === d.id)} />
                          ))}
                          {chuaPhanDang.length > 0 && (
                            <TheDangChiTiet ten="(Chưa phân dạng)" list={chuaPhanDang} nhan />
                          )}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </CardBody>
      </div>
    </Card>
  )
}
