import { useEffect, useState } from 'react'
import { api } from '../../api'
import { Badge, Button, Card, CardBody, Select, Table } from '../../components/ui'

const NHAN_CO = {
  ro_ri_dap_an: 'Rò rỉ đáp án',
  noi_dung_khong_phu_hop: 'Nội dung không phù hợp',
  ngoai_pham_vi: 'Ngoài phạm vi',
  thu_cong: 'Gắn thủ công',
  khong_hieu_nhieu: 'Không hiểu nhiều',
  chot_chan_nhieu: 'Chốt chặn nhiều',
}
const TONE_TT = { cho_xu_ly: 'warning', da_xu_ly: 'success', bo_qua: 'neutral' }
const NHAN_TT = { cho_xu_ly: 'Chờ xử lý', da_xu_ly: 'Đã xử lý', bo_qua: 'Bỏ qua' }

export default function QuanLyCo() {
  const [rows, setRows] = useState([])
  const [loading, setLoading] = useState(true)
  const [fTT, setFTT] = useState('')

  function taiFlags() {
    return api.listFlags(fTT || undefined).then(setRows).catch(() => {})
  }

  useEffect(() => {
    let active = true
    api
      .listFlags(fTT || undefined)
      .then((d) => active && setRows(d))
      .catch(() => {})
      .finally(() => active && setLoading(false))
    return () => {
      active = false
    }
  }, [fTT])

  async function capNhat(id, trang_thai) {
    await api.updateFlag(id, trang_thai)
    await taiFlags()
  }

  return (
    <div className="flex flex-col gap-4">
      <Select
        label="Lọc trạng thái"
        className="w-56"
        value={fTT}
        onChange={(e) => setFTT(e.target.value)}
        options={[
          { value: '', label: 'Tất cả' },
          { value: 'cho_xu_ly', label: 'Chờ xử lý' },
          { value: 'da_xu_ly', label: 'Đã xử lý' },
          { value: 'bo_qua', label: 'Bỏ qua' },
        ]}
      />

      <Card>
        <CardBody className="pt-5">
          {loading ? (
            <p className="text-muted text-sm">Đang tải...</p>
          ) : (
            <Table
              columns={[
                { key: 'id', header: '#', className: 'w-12' },
                { key: 'session_id', header: 'Phiên', render: (r) => `#${r.session_id ?? '-'}` },
                {
                  key: 'loai_co',
                  header: 'Loại cờ',
                  render: (r) => NHAN_CO[r.loai_co] || r.loai_co,
                },
                { key: 'ghi_chu', header: 'Ghi chú', render: (r) => r.ghi_chu || '—' },
                {
                  key: 'trang_thai',
                  header: 'Trạng thái',
                  render: (r) => (
                    <Badge tone={TONE_TT[r.trang_thai]}>{NHAN_TT[r.trang_thai] || r.trang_thai}</Badge>
                  ),
                },
                {
                  key: 'hanh_dong',
                  header: '',
                  render: (r) =>
                    r.trang_thai === 'cho_xu_ly' ? (
                      <div className="flex gap-2">
                        <Button size="sm" variant="success" onClick={() => capNhat(r.id, 'da_xu_ly')}>
                          Đã xử lý
                        </Button>
                        <Button size="sm" variant="secondary" onClick={() => capNhat(r.id, 'bo_qua')}>
                          Bỏ qua
                        </Button>
                      </div>
                    ) : null,
                },
              ]}
              rows={rows}
              rowKey={(r) => r.id}
              empty="Không có cờ nào."
            />
          )}
        </CardBody>
      </Card>
    </div>
  )
}
