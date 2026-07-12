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

// focusId: { id, ts } | null — GV bấm thông báo "⚠️/🆘 ..." ở chuông thông báo, cần nhảy
// tới + làm nổi bật đúng cờ đó. "ts" đổi mỗi lần bấm để ép hiệu ứng chạy lại kể cả bấm
// trùng đúng cờ đã focus trước đó.
export default function QuanLyCo({ focusId, onFocusDone } = {}) {
  const [rows, setRows] = useState([])
  const [loading, setLoading] = useState(true)
  const [fTT, setFTT] = useState('')
  const [xuLy, setXuLy] = useState(null) // cờ đang xử lý (mở modal lời nhắn)
  const [loiNhan, setLoiNhan] = useState('')
  const [dangGui, setDangGui] = useState(false)
  const [noiBatId, setNoiBatId] = useState(null)

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

  async function capNhat(id, trang_thai, loi_nhan = '') {
    await api.updateFlag(id, trang_thai, loi_nhan)
    await taiFlags()
  }

  function moXuLy(flag) {
    setXuLy(flag)
    setLoiNhan('')
  }

  async function xacNhanXuLy() {
    if (!xuLy) return
    setDangGui(true)
    try {
      await capNhat(xuLy.id, 'da_xu_ly', loiNhan.trim())
      setXuLy(null)
      setLoiNhan('')
    } finally {
      setDangGui(false)
    }
  }

  // Cờ liên quan đến HS (gửi lời nhắn được); cờ nội dung (chốt chặn) chỉ xử lý.
  const coTheNhanHs = (loai) => loai !== 'chot_chan_nhieu'

  // Nhảy tới + làm nổi bật đúng cờ khi được yêu cầu focus từ chuông thông báo — đợi danh
  // sách tải xong (loading=false) rồi mới tìm. Nếu không thấy (có thể do đang lọc theo
  // trạng thái khác), mở lại "Tất cả" rồi để effect chạy lại lần tới danh sách đổi.
  useEffect(() => {
    if (!focusId || loading) return
    let cuonTimeout, tatNoiBat
    const batDau = setTimeout(() => {
      if (!rows.some((r) => r.id === focusId.id)) {
        if (fTT !== '') { setFTT(''); return }
        onFocusDone?.()
        return
      }
      setNoiBatId(focusId.id)
      cuonTimeout = setTimeout(() => {
        document.getElementById(`co-${focusId.id}`)
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
  }, [focusId, loading, rows])

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
                { key: 'hoc_sinh_ten', header: 'Học sinh', render: (r) => r.hoc_sinh_ten || '—' },
                {
                  key: 'bai', header: 'Bài',
                  render: (r) => r.chuyen_de
                    ? `${r.chuyen_de}${r.dang_ten ? ` › ${r.dang_ten}` : ''}`
                    : `Phiên #${r.session_id ?? '-'}`,
                },
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
                        {coTheNhanHs(r.loai_co) ? (
                          <Button size="sm" variant="success" onClick={() => moXuLy(r)}>
                            Xử lý & nhắn HS
                          </Button>
                        ) : (
                          <Button size="sm" variant="success" onClick={() => capNhat(r.id, 'da_xu_ly')}>
                            Đã xử lý
                          </Button>
                        )}
                        <Button size="sm" variant="secondary" onClick={() => capNhat(r.id, 'bo_qua')}>
                          Bỏ qua
                        </Button>
                      </div>
                    ) : null,
                },
              ]}
              rows={rows}
              rowKey={(r) => r.id}
              rowId={(r) => `co-${r.id}`}
              rowClassName={(r) => (noiBatId === r.id ? 'ring-2 ring-primary' : '')}
              empty="Không có cờ nào."
            />
          )}
        </CardBody>
      </Card>

      {xuLy && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="bg-surface rounded-xl shadow-xl w-full max-w-md max-h-[88vh] flex flex-col">
            <div className="px-5 pt-5 pb-3 border-b border-border shrink-0">
              <h2 className="font-bold text-lg text-ink">Xử lý cờ & nhắn học sinh</h2>
              <p className="text-sm text-muted mt-0.5">
                {xuLy.hoc_sinh_ten ? `${xuLy.hoc_sinh_ten} · ` : ''}
                {xuLy.chuyen_de || `Phiên #${xuLy.session_id}`}
              </p>
            </div>
            <div className="px-5 py-4 overflow-y-auto flex-1">
              <label className="text-sm font-medium text-ink">Lời nhắn cho học sinh (tùy chọn)</label>
              <textarea
                value={loiNhan}
                onChange={(e) => setLoiNhan(e.target.value)}
                rows={4}
                placeholder="VD: Em xem lại ví dụ mẫu phần này rồi thử lại nhé. Cần thì nhờ thầy/cô."
                className="mt-1 w-full rounded-lg border border-border px-3 py-2 text-sm text-ink
                  focus:outline-none focus:ring-2 focus:ring-primary/40 resize-y"
              />
              <p className="text-xs text-muted mt-1">
                Để trống nếu chỉ muốn đánh dấu đã xử lý mà không nhắn HS.
              </p>
            </div>
            <div className="px-5 py-4 border-t border-border flex gap-2 justify-end shrink-0">
              <Button variant="secondary" onClick={() => setXuLy(null)} disabled={dangGui}>Hủy</Button>
              <Button onClick={xacNhanXuLy} disabled={dangGui}>
                {dangGui ? 'Đang lưu...' : (loiNhan.trim() ? 'Xử lý & gửi lời nhắn' : 'Đánh dấu đã xử lý')}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
