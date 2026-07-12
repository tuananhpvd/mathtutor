import { useEffect, useState } from 'react'
import { api } from '../../api'
import { Badge, Button, Card, CardBody, CardHeader } from '../../components/ui'
import Formula from '../../components/Formula'
import ThoiGianPhanCach from '../../components/ThoiGianPhanCach'

const NHAN_LOAI = { TN4PA: 'Trắc nghiệm', TNDS: 'Đúng/Sai', TLN: 'Trả lời ngắn' }
const MOI_TRANG = 10

function renderDeBai(text) {
  if (!text) return null
  return String(text).split(/(\$[^$]+\$)/g).map((p, i) =>
    p.startsWith('$') && p.endsWith('$')
      ? <Formula key={i} latex={p.slice(1, -1)} />
      : <span key={i}>{p}</span>
  )
}

function hanInfo(iso) {
  if (!iso) return null
  const han = new Date(iso)
  const conLai = Math.ceil((han.getTime() - Date.now()) / 86400000)
  const ngay = han.toLocaleDateString('vi-VN')
  if (conLai < 0) return { text: `Quá hạn (${ngay})`, tone: 'danger' }
  if (conLai <= 2) return { text: `Còn ${conLai} ngày (${ngay})`, tone: 'warning' }
  return { text: `Hạn ${ngay}`, tone: 'primary' }
}

// focusId: { id, ts } | null — HS bấm thông báo "Nhiệm vụ mới" ở chuông, cần nhảy tới +
// làm nổi bật tạm thời đúng nhiệm vụ đó. "ts" đổi mỗi lần bấm để ép hiệu ứng chạy lại kể cả
// bấm trùng nhiệm vụ đã focus trước đó.
export default function NhiemVu({ onChon, focusId, onFocusDone }) {
  const [ds, setDs] = useState([])
  const [loading, setLoading] = useState(true)
  const [noiBatId, setNoiBatId] = useState(null)
  const [trang, setTrang] = useState(1)

  useEffect(() => {
    api.hsNhiemVu()
      .then((rows) => setDs(rows || []))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    if (!focusId || loading) return
    let cuonTimeout, tatNoiBat
    const batDau = setTimeout(() => {
      const idx = ds.findIndex((nv) => nv.id === focusId.id)
      if (idx < 0) { onFocusDone?.(); return }
      setTrang(Math.floor(idx / MOI_TRANG) + 1)
      setNoiBatId(focusId.id)
      cuonTimeout = setTimeout(() => {
        document.getElementById(`nv-${focusId.id}`)
          ?.scrollIntoView({ behavior: 'smooth', block: 'center' })
      }, 150)
      tatNoiBat = setTimeout(() => setNoiBatId(null), 3000)
      onFocusDone?.()
    }, 0)
    return () => {
      clearTimeout(batDau)
      clearTimeout(cuonTimeout)
      clearTimeout(tatNoiBat)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [focusId, loading, ds])

  const tongTrang = Math.max(1, Math.ceil(ds.length / MOI_TRANG))
  const dsTrang = ds.slice((trang - 1) * MOI_TRANG, trang * MOI_TRANG)

  return (
    <div className="flex flex-col gap-5">
      <div>
        <h2 className="text-xl font-semibold text-black">Nhiệm vụ của em</h2>
        <p className="text-black/90 text-sm mt-1">
          Bài tập thầy/cô giao riêng cho em — hoàn thành để tiến bộ đúng trọng tâm nhé.
        </p>
      </div>

      {loading ? (
        <p className="text-sm text-muted">Đang tải...</p>
      ) : ds.length === 0 ? (
        <Card><CardBody>
          <p className="text-sm text-muted">Hiện chưa có nhiệm vụ nào. 🎉</p>
        </CardBody></Card>
      ) : (
        <div className="grid lg:grid-cols-2 gap-5 items-start">
        {dsTrang.map((nv) => {
          const xong = nv.tong_bai > 0 && nv.so_hoan_thanh >= nv.tong_bai
          const han = hanInfo(nv.han_chot)
          return (
            <Card key={nv.id} id={`nv-${nv.id}`}
              className={noiBatId === nv.id ? 'ring-2 ring-primary transition-shadow' : ''}>
              <CardHeader
                title={nv.tieu_de}
                subtitle={nv.gv_ten ? (
                  <span className="inline-flex items-center gap-0.5 flex-wrap">
                    <span>Giao bởi <b>{nv.gv_ten}</b></span>
                    {nv.tao_luc && <ThoiGianPhanCach iso={nv.tao_luc} />}
                  </span>
                ) : undefined}
                action={
                  <div className="flex items-center gap-2">
                    {han && <Badge tone={han.tone}>{han.text}</Badge>}
                    <Badge tone={xong ? 'success' : 'warning'}>
                      {nv.so_hoan_thanh}/{nv.tong_bai} bài
                    </Badge>
                  </div>
                }
              />
              <CardBody className="flex flex-col gap-2">
                {nv.mo_ta && <p className="text-sm text-muted">{nv.mo_ta}</p>}
                {nv.bai.map((b) => (
                  <div key={b.problem_id}
                    className="rounded-lg border border-border px-3 py-2.5 flex flex-col gap-1.5">
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0 flex-1">
                        <p className="text-xs text-muted truncate">
                          {b.chuyen_de}{b.dang_ten ? ` › ${b.dang_ten}` : ''}
                        </p>
                        <p className="text-sm text-ink leading-snug mt-0.5 line-clamp-2">
                          {renderDeBai(b.de_bai)}
                        </p>
                      </div>
                      <div className="shrink-0">
                        {b.da_hoan_thanh ? (
                          <Badge tone="success">✓ Hoàn thành</Badge>
                        ) : (
                          <Button size="sm" onClick={() => onChon?.(b.problem_id)}>Làm bài</Button>
                        )}
                      </div>
                    </div>
                    <p className="text-xs">
                      <Badge tone="primary">{NHAN_LOAI[b.loai_cau] || b.loai_cau}</Badge>
                    </p>
                  </div>
                ))}
              </CardBody>
            </Card>
          )
        })}
        </div>
      )}

      {!loading && ds.length > 0 && tongTrang > 1 && (
        <div className="flex items-center justify-center gap-3 pt-1">
          <Button size="sm" variant="secondary" disabled={trang <= 1}
            onClick={() => setTrang((t) => t - 1)}>← Trước</Button>
          <span className="text-sm text-muted">Trang {trang}/{tongTrang}</span>
          <Button size="sm" variant="secondary" disabled={trang >= tongTrang}
            onClick={() => setTrang((t) => t + 1)}>Sau →</Button>
        </div>
      )}
    </div>
  )
}
