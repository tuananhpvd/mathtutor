import { useEffect, useState } from 'react'
import { api } from '../../api'
import { Badge, Button, Card, CardBody, CardHeader, Table } from '../../components/ui'
import { dinhDangThoiGian } from '../../utils/format'
import { CotThoiGian } from '../../components/ThoiGianPhanCach'

const NHAN_CO = {
  ro_ri_dap_an: 'Rò rỉ đáp án',
  noi_dung_khong_phu_hop: 'Nội dung không phù hợp',
  ngoai_pham_vi: 'Ngoài phạm vi',
  khong_hieu_nhieu: 'Không hiểu nhiều',
  chot_chan_nhieu: 'Chốt chặn nhiều',
  khong_phan_tich_duoc: 'CAS không đọc được',
  thu_cong: 'Gắn thủ công',
}
const TONE = { cho_xu_ly: 'warning', da_xu_ly: 'success', bo_qua: 'neutral' }
const NHAN_TT = { cho_xu_ly: 'Chờ xử lý', da_xu_ly: 'Đã xử lý', bo_qua: 'Bỏ qua' }

export default function NhatKy() {
  const [flags, setFlags] = useState([])
  const [hoanThanh, setHoanThanh] = useState([])
  const [loading, setLoading] = useState(true)

  const [hoatDong, setHoatDong] = useState([])
  const [lopTimThay, setLopTimThay] = useState(true)
  const [dangTaiHoatDong, setDangTaiHoatDong] = useState(true)
  const [tuNgay, setTuNgay] = useState('')
  const [denNgay, setDenNgay] = useState('')
  const [chiTiet, setChiTiet] = useState(false)

  useEffect(() => {
    let active = true
    Promise.all([api.listFlags(), api.listSessionsHoanThanh()])
      .then(([f, h]) => {
        if (!active) return
        setFlags(f)
        // v162 đổi shape trả về của listSessionsHoanThanh() từ mảng phẳng sang
        // {rows, tong} (phân trang server-side) — chỗ gọi này bị sót lúc đó.
        setHoanThanh(h.rows)
      })
      .catch(() => {})
      .finally(() => active && setLoading(false))
    return () => {
      active = false
    }
  }, [])

  function taiHoatDong(tu, den, ct) {
    setDangTaiHoatDong(true)
    api
      .nhatKyHoatDong({ tu_ngay: tu || undefined, den_ngay: den || undefined, chi_tiet: ct })
      .then((d) => {
        setHoatDong(d.rows)
        setLopTimThay(d.lop_tim_thay)
      })
      .catch(() => {})
      .finally(() => setDangTaiHoatDong(false))
  }

  useEffect(() => {
    setTimeout(() => taiHoatDong('', '', false), 0)
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
                  render: (r) => <CotThoiGian iso={r.hoan_thanh_luc} />,
                },
                { key: 'ho_ten', header: 'Học sinh' },
                { key: 'chuyen_de', header: 'Chuyên đề' },
                { key: 'loai_cau', header: 'Loại', render: (r) => <Badge tone="primary">{r.loai_cau}</Badge> },
                { key: 'diem', header: 'Điểm', render: (r) => (r.diem != null ? r.diem : '-') },
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
                render: (r) => <CotThoiGian iso={r.tao_luc} />,
              },
              { key: 'session_id', header: 'Phiên', render: (r) => `#${r.session_id ?? '-'}` },
              { key: 'loai_co', header: 'Loại', render: (r) => NHAN_CO[r.loai_co] || r.loai_co },
              {
                key: 'trang_thai',
                header: 'Trạng thái',
                render: (r) => <Badge tone={TONE[r.trang_thai]}>{NHAN_TT[r.trang_thai] || r.trang_thai}</Badge>,
              },
            ]}
            rows={flags}
            rowKey={(r) => r.id}
            empty="Chưa có sự kiện nào."
          />
        </CardBody>
      </Card>

      <Card>
        <CardHeader
          title="Nhật ký hoạt động Ban giám khảo"
          subtitle="Tái dựng từ dấu vết thời gian sẵn có trong CSDL (Lớp Demo) — không phải audit log đầy đủ: chỉ ghi được đăng ký, bắt đầu/hoàn thành bài, tạo câu hỏi/chuyên đề/dạng, giao nhiệm vụ, đề thi, nhờ trợ giúp, cờ tự phát sinh. KHÔNG ghi được sửa/duyệt/xóa câu hỏi hay lượt đăng nhập."
        />
        <CardBody className="pt-0">
          {!lopTimThay ? (
            <p className="text-muted text-sm">Chưa có "Lớp Demo" trên hệ thống.</p>
          ) : (
            <>
              <div className="flex flex-wrap items-end gap-3 mb-4">
                <div>
                  <label className="block text-sm font-medium text-ink mb-1">Từ ngày</label>
                  <input type="date" value={tuNgay} onChange={(e) => setTuNgay(e.target.value)}
                    className="rounded-md border border-border bg-surface px-3 py-1.5 text-sm text-ink
                      focus:outline-none focus:ring-2 focus:ring-primary/40 focus:border-primary" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-ink mb-1">Đến ngày</label>
                  <input type="date" value={denNgay} onChange={(e) => setDenNgay(e.target.value)}
                    className="rounded-md border border-border bg-surface px-3 py-1.5 text-sm text-ink
                      focus:outline-none focus:ring-2 focus:ring-primary/40 focus:border-primary" />
                </div>
                <label className="flex items-center gap-2 text-sm text-ink pb-1.5">
                  <input type="checkbox" checked={chiTiet}
                    onChange={(e) => setChiTiet(e.target.checked)} />
                  Hiện cả từng lượt hội thoại
                </label>
                <Button
                  disabled={dangTaiHoatDong}
                  onClick={() => taiHoatDong(tuNgay, denNgay, chiTiet)}
                >
                  {dangTaiHoatDong ? 'Đang tải...' : 'Lọc'}
                </Button>
              </div>
              <Table
                columns={[
                  {
                    key: 'thoi_diem',
                    header: 'Thời điểm',
                    render: (r) => <CotThoiGian iso={r.thoi_diem} />,
                  },
                  { key: 'dang_nhap', header: 'Tài khoản', render: (r) => r.dang_nhap || r.ho_ten },
                  {
                    key: 'vai_tro',
                    header: 'Vai trò',
                    render: (r) => r.vai_tro ? <Badge tone="primary">{r.vai_tro}</Badge> : '-',
                  },
                  { key: 'hanh_dong', header: 'Hoạt động' },
                  { key: 'chi_tiet', header: 'Chi tiết' },
                ]}
                rows={hoatDong}
                rowKey={(r) => `${r.thoi_diem}-${r.dang_nhap}-${r.hanh_dong}-${r.chi_tiet}`}
                empty="Chưa có hoạt động nào."
              />
            </>
          )}
        </CardBody>
      </Card>
    </div>
  )
}
