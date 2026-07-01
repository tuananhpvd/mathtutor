import { useEffect, useState } from 'react'
import { api } from '../../api'
import { Badge, Button, Card, CardBody, CardHeader } from '../../components/ui'

const NHAN_LOAI = { TN4PA: 'Trắc nghiệm', TNDS: 'Đúng/Sai', TLN: 'Trả lời ngắn' }

function hanInfo(iso) {
  if (!iso) return null
  const han = new Date(iso)
  const conLai = Math.ceil((han.getTime() - Date.now()) / 86400000)
  const ngay = han.toLocaleDateString('vi-VN')
  if (conLai < 0) return { text: `Quá hạn (${ngay})`, tone: 'danger' }
  if (conLai <= 2) return { text: `Còn ${conLai} ngày (${ngay})`, tone: 'warning' }
  return { text: `Hạn ${ngay}`, tone: 'primary' }
}

export default function NhiemVu({ onChon }) {
  const [ds, setDs] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.hsNhiemVu()
      .then((rows) => setDs(rows || []))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="flex flex-col gap-5">
      <div>
        <h2 className="text-xl font-semibold text-ink">Nhiệm vụ của em</h2>
        <p className="text-muted text-sm mt-1">
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
        ds.map((nv) => {
          const xong = nv.tong_bai > 0 && nv.so_hoan_thanh >= nv.tong_bai
          const han = hanInfo(nv.han_chot)
          return (
            <Card key={nv.id}>
              <CardHeader
                title={nv.tieu_de}
                subtitle={nv.gv_ten ? `Giao bởi ${nv.gv_ten}` : undefined}
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
                    className="flex items-center justify-between gap-3 rounded-lg border border-border px-3 py-2.5">
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-ink truncate">
                        {b.chuyen_de}{b.dang_ten ? ` › ${b.dang_ten}` : ''}
                      </p>
                      <p className="text-xs mt-0.5">
                        <Badge tone="primary">{NHAN_LOAI[b.loai_cau] || b.loai_cau}</Badge>
                      </p>
                    </div>
                    {b.da_hoan_thanh ? (
                      <Badge tone="success">✓ Đã hoàn thành</Badge>
                    ) : (
                      <Button size="sm" onClick={() => onChon?.(b.problem_id)}>Làm bài</Button>
                    )}
                  </div>
                ))}
              </CardBody>
            </Card>
          )
        })
      )}
    </div>
  )
}
