import { useEffect, useState } from 'react'
import { api } from '../../api'
import { Badge, Button, Card, CardBody, CardHeader, Select } from '../../components/ui'

const NHAN_TRANG_THAI = {
  cho_duyet: { label: 'Chờ duyệt', tone: 'warning' },
  da_duyet: { label: 'Đã duyệt', tone: 'success' },
  tu_choi: { label: 'Từ chối', tone: 'danger' },
}

function dinhDangNgay(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleString('vi-VN', {
    day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit',
  })
}

export default function YeuCauDatLai() {
  const [rows, setRows] = useState([])
  const [filter, setFilter] = useState('cho_duyet')
  const [error, setError] = useState('')
  const [modal, setModal] = useState(null)   // { yc, hanh_dong: 'duyet'|'tu_choi' }
  const [ghiChu, setGhiChu] = useState('')
  const [dangXuLy, setDangXuLy] = useState(false)

  function tai() {
    api.adminDanhSachYeuCauDatLai(filter).then(setRows).catch((e) => setError(e.message))
  }
  useEffect(tai, [filter])

  async function xuLy() {
    if (!modal) return
    setDangXuLy(true)
    try {
      if (modal.hanh_dong === 'duyet') {
        await api.adminDuyetDatLai(modal.yc.id, ghiChu)
      } else {
        await api.adminTuChoiDatLai(modal.yc.id, ghiChu)
      }
      setModal(null); setGhiChu(''); tai()
    } catch (e) { setError(e.message) }
    finally { setDangXuLy(false) }
  }

  return (
    <div className="flex flex-col gap-4">
      {error && (
        <p className="text-danger text-sm bg-danger-soft rounded-md px-3 py-2">
          {error} <button onClick={() => setError('')} className="ml-2 font-bold">✕</button>
        </p>
      )}

      <Card>
        <CardHeader
          title="Yêu cầu đặt lại tiến độ"
          subtitle="GV gửi yêu cầu — Admin xét duyệt trước khi thực hiện"
        />
        <CardBody className="flex flex-col gap-3">
          <Select
            label="Lọc trạng thái"
            className="w-48"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            options={[
              { value: '', label: 'Tất cả' },
              { value: 'cho_duyet', label: 'Chờ duyệt' },
              { value: 'da_duyet', label: 'Đã duyệt' },
              { value: 'tu_choi', label: 'Từ chối' },
            ]}
          />

          {rows.length === 0 ? (
            <p className="text-sm text-muted py-4 text-center">Không có yêu cầu nào.</p>
          ) : (
            <div className="flex flex-col gap-3">
              {rows.map((yc) => {
                const ts = NHAN_TRANG_THAI[yc.trang_thai] || { label: yc.trang_thai, tone: 'neutral' }
                return (
                  <div key={yc.id} className="border rounded-xl p-4 flex flex-col gap-2">
                    <div className="flex items-start justify-between gap-2 flex-wrap">
                      <div>
                        <span className="font-semibold">{yc.ho_ten_hs}</span>
                        <span className="text-muted text-sm ml-2">({yc.dang_nhap_hs})</span>
                      </div>
                      <Badge tone={ts.tone}>{ts.label}</Badge>
                    </div>
                    <p className="text-sm text-muted">
                      <span className="font-medium text-foreground">GV:</span> {yc.gv_ho_ten}
                      <span className="mx-2">·</span>
                      {dinhDangNgay(yc.tao_luc)}
                    </p>
                    <p className="text-sm bg-surface-2 rounded-lg px-3 py-2">
                      <span className="font-medium">Lý do: </span>{yc.ly_do}
                    </p>
                    {yc.ghi_chu_admin && (
                      <p className="text-sm text-muted italic">Ghi chú admin: {yc.ghi_chu_admin}</p>
                    )}
                    {yc.xu_ly_boi && (
                      <p className="text-xs text-muted">Xử lý bởi {yc.xu_ly_boi} lúc {dinhDangNgay(yc.xu_ly_luc)}</p>
                    )}
                    {yc.trang_thai === 'cho_duyet' && (
                      <div className="flex gap-2 mt-1">
                        <Button
                          size="sm"
                          onClick={() => { setModal({ yc, hanh_dong: 'duyet' }); setGhiChu('') }}
                        >
                          Duyệt
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => { setModal({ yc, hanh_dong: 'tu_choi' }); setGhiChu('') }}
                        >
                          <span className="text-danger">Từ chối</span>
                        </Button>
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          )}
        </CardBody>
      </Card>

      {modal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6 flex flex-col gap-4">
            <h2 className={`text-lg font-bold ${modal.hanh_dong === 'duyet' ? 'text-success' : 'text-danger'}`}>
              {modal.hanh_dong === 'duyet' ? '✅ Duyệt yêu cầu đặt lại' : '❌ Từ chối yêu cầu'}
            </h2>
            <p className="text-sm">
              Học sinh: <strong>{modal.yc.ho_ten_hs}</strong>
            </p>
            {modal.hanh_dong === 'duyet' && (
              <p className="text-sm bg-warning-soft rounded-lg px-3 py-2 text-warning">
                Sau khi duyệt, toàn bộ phiên học, tiến độ và phân tích năng lực của học sinh sẽ bị ẩn. Hành động không thể hoàn tác.
              </p>
            )}
            <div className="flex flex-col gap-1">
              <label className="text-sm font-medium">Ghi chú (tùy chọn)</label>
              <textarea
                className="border rounded-lg px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-primary"
                rows={2}
                placeholder="Ghi chú cho GV..."
                value={ghiChu}
                onChange={(e) => setGhiChu(e.target.value)}
              />
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="ghost" onClick={() => setModal(null)}>Hủy</Button>
              <Button
                onClick={xuLy}
                disabled={dangXuLy}
                className={modal.hanh_dong === 'duyet'
                  ? 'bg-success text-white hover:bg-success/90'
                  : 'bg-danger text-white hover:bg-danger/90'}
              >
                {dangXuLy ? 'Đang xử lý...' : modal.hanh_dong === 'duyet' ? 'Xác nhận duyệt' : 'Xác nhận từ chối'}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
