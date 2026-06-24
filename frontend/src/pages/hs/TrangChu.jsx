import { useEffect, useState } from 'react'
import { api } from '../../api'
import { getSession } from '../../auth'
import { Badge, Button, Card, CardBody, CardHeader, ProgressChart } from '../../components/ui'

const NHAN_LOAI = { TN4PA: 'Trắc nghiệm', TNDS: 'Đúng/Sai', TLN: 'Trả lời ngắn' }

export default function TrangChu({ onChonBai, onLamTiep }) {
  const { ho_ten } = getSession() || {}
  const [baiDo, setBaiDo] = useState([])
  const [tienDo, setTienDo] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([api.getDangDo(), api.getProgressMe()])
      .then(([dd, pg]) => {
        setBaiDo(dd)
        setTienDo(
          pg.map((p) => ({
            nhan: p.chuyen_de,
            gia_tri: p.ty_le_dung_trung_binh,
            phu: `${p.so_bai_hoan_thanh}/${p.so_bai_lam} bài`,
          }))
        )
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h2 className="text-xl font-semibold text-ink">Chào em{ho_ten ? `, ${ho_ten}` : ''}!</h2>
        <p className="text-muted text-sm mt-1">
          Gia sư sẽ dẫn dắt bằng câu hỏi gợi mở — em tự tìm ra lời giải nhé.
        </p>
      </div>

      <div className="grid md:grid-cols-2 gap-4">
        <Card>
          <CardHeader title="Bài đang làm dở" subtitle="Tiếp tục đúng chỗ em dừng lại" />
          <CardBody className="flex flex-col gap-3">
            {loading ? (
              <p className="text-sm text-muted">Đang tải...</p>
            ) : baiDo.length === 0 ? (
              <p className="text-sm text-muted">Em chưa có bài nào đang làm dở.</p>
            ) : (
              baiDo.map((b) => (
                <div
                  key={b.session_id}
                  className="flex items-center justify-between rounded-md border border-border px-3 py-2.5"
                >
                  <div>
                    <p className="text-sm font-medium text-ink">{b.chuyen_de}</p>
                    <p className="text-xs text-muted mt-0.5 flex items-center gap-2">
                      <Badge tone="primary">{NHAN_LOAI[b.loai_cau] || b.loai_cau}</Badge>
                      <span>Bước {b.buoc_hien_tai}</span>
                    </p>
                  </div>
                  <Button size="sm" onClick={() => onLamTiep(b.session_id)}>
                    Làm tiếp
                  </Button>
                </div>
              ))
            )}
            <Button variant="secondary" onClick={onChonBai}>
              Chọn bài mới
            </Button>
          </CardBody>
        </Card>

        <Card>
          <CardHeader title="Tiến độ của em" subtitle="Tỉ lệ đúng trung bình theo chuyên đề" />
          <CardBody>
            <ProgressChart data={tienDo} />
          </CardBody>
        </Card>
      </div>
    </div>
  )
}
