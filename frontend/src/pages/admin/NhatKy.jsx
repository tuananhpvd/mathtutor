import { useEffect, useState } from 'react'
import { api } from '../../api'
import { Badge, Card, CardBody, CardHeader, Table } from '../../components/ui'
import { dinhDangThoiGian } from '../../utils/format'

const NHAN_CO = {
  ro_ri_dap_an: 'Rò rỉ đáp án',
  noi_dung_khong_phu_hop: 'Nội dung không phù hợp',
  ngoai_pham_vi: 'Ngoài phạm vi',
  khong_hieu_nhieu: 'Không hiểu nhiều',
  chot_chan_nhieu: 'Chốt chặn nhiều',
  thu_cong: 'Gắn thủ công',
}
const TONE = { cho_xu_ly: 'warning', da_xu_ly: 'success', bo_qua: 'neutral' }

export default function NhatKy() {
  const [flags, setFlags] = useState([])
  const [hoanThanh, setHoanThanh] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let active = true
    Promise.all([api.listFlags(), api.listSessionsHoanThanh()])
      .then(([f, h]) => {
        if (!active) return
        setFlags(f)
        setHoanThanh(h)
      })
      .catch(() => {})
      .finally(() => active && setLoading(false))
    return () => {
      active = false
    }
  }, [])

  return (
    <div className="flex flex-col gap-6">
      <Card>
        <CardHeader
          title="Nhật ký bài hoàn thành"
          subtitle="Học sinh nào làm xong bài gì, mất bao lâu"
        />
        <CardBody className="pt-0">
          {loading ? (
            <p className="text-muted text-sm">Đang tải...</p>
          ) : (
            <Table
              columns={[
                {
                  key: 'luc',
                  header: 'Thời điểm',
                  render: (r) => new Date(r.hoan_thanh_luc).toLocaleString('vi-VN'),
                },
                { key: 'ho_ten', header: 'Học sinh' },
                { key: 'chuyen_de', header: 'Chuyên đề' },
                { key: 'loai_cau', header: 'Loại', render: (r) => <Badge tone="primary">{r.loai_cau}</Badge> },
                { key: 'diem', header: 'Điểm', render: (r) => (r.diem != null ? r.diem : '—') },
                { key: 'tg', header: 'Thời gian', render: (r) => dinhDangThoiGian(r.thoi_gian_giay) },
              ]}
              rows={hoanThanh}
              rowKey={(r) => r.session_id}
              empty="Chưa có bài nào hoàn thành."
            />
          )}
        </CardBody>
      </Card>

      <Card>
        <CardHeader
          title="Nhật ký cờ & cảnh báo an toàn"
          subtitle="Các sự kiện chốt chặn / gắn cờ gần đây"
        />
        <CardBody className="pt-0">
          <Table
            columns={[
              {
                key: 'tao_luc',
                header: 'Thời điểm',
                render: (r) => new Date(r.tao_luc).toLocaleString('vi-VN'),
              },
              { key: 'session_id', header: 'Phiên', render: (r) => `#${r.session_id ?? '-'}` },
              { key: 'loai_co', header: 'Loại', render: (r) => NHAN_CO[r.loai_co] || r.loai_co },
              {
                key: 'trang_thai',
                header: 'Trạng thái',
                render: (r) => <Badge tone={TONE[r.trang_thai]}>{r.trang_thai}</Badge>,
              },
            ]}
            rows={flags}
            rowKey={(r) => r.id}
            empty="Chưa có sự kiện nào."
          />
        </CardBody>
      </Card>
    </div>
  )
}
