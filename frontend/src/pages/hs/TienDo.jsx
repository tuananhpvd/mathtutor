import { useEffect, useState } from 'react'
import { api } from '../../api'
import ThongKeTienDo from '../../components/ThongKeTienDo'
import PhanTichNangLuc from '../../components/PhanTichNangLuc'
import BanDoNangLuc from '../../components/BanDoNangLuc'
import BieuDoTuan from '../../components/BieuDoTuan'
import { Button, Card, CardBody, CardHeader } from '../../components/ui'
import ThoiGianPhanCach from '../../components/ThoiGianPhanCach'

const MOI_TRANG_NX = 3

// Card "Nhận xét của thầy/cô" — chuyển từ trang chủ sang đây, đặt ngay sau card
// "Nhận xét & gợi ý cho em" của PhanTichNangLuc (qua slot sauNhanXet).
function TheNhanXet({ nhanXet, trang, onTrang }) {
  const tongTrang = Math.max(1, Math.ceil(nhanXet.length / MOI_TRANG_NX))
  const trangAnToan = Math.min(trang, tongTrang)
  const dsTrang = nhanXet.slice((trangAnToan - 1) * MOI_TRANG_NX, trangAnToan * MOI_TRANG_NX)
  return (
    <Card>
      <CardHeader title="💬 Nhận xét của thầy/cô"
        subtitle={nhanXet.length > 0 ? `${nhanXet.length} lời nhắn từ giáo viên` : undefined} />
      <CardBody className="flex flex-col gap-3">
        {nhanXet.length === 0 ? (
          <p className="text-sm text-muted">Thầy/cô chưa gửi nhận xét nào cho em.</p>
        ) : (
          <>
            {dsTrang.map((tb) => (
              <div key={tb.id} className="rounded-xl border border-gv/30 bg-gv/5 px-4 py-3">
                <p className="text-sm text-ink whitespace-pre-wrap break-words">{tb.noi_dung}</p>
                <div className="flex items-center flex-wrap gap-x-0.5 text-xs text-muted mt-1.5">
                  {tb.nguoi_gui_ten && <span>— {tb.nguoi_gui_ten}</span>}
                  {tb.tao_luc && <ThoiGianPhanCach iso={tb.tao_luc} />}
                </div>
              </div>
            ))}
            {tongTrang > 1 && (
              <div className="flex items-center justify-center gap-3 pt-1">
                <Button size="sm" variant="secondary" disabled={trangAnToan <= 1}
                  onClick={() => onTrang(trangAnToan - 1)}>← Trước</Button>
                <span className="text-sm text-muted">{trangAnToan}/{tongTrang}</span>
                <Button size="sm" variant="secondary" disabled={trangAnToan >= tongTrang}
                  onClick={() => onTrang(trangAnToan + 1)}>Sau →</Button>
              </div>
            )}
          </>
        )}
      </CardBody>
    </Card>
  )
}

export default function TienDo({ onLuyenDang }) {
  const [tk, setTk] = useState(null)
  const [pt, setPt] = useState(null)
  const [hq, setHq] = useState(null)
  const [nhanXet, setNhanXet] = useState([])
  const [trangNx, setTrangNx] = useState(1)
  const [loading, setLoading] = useState(true)
  const [dangCapNhat, setDangCapNhat] = useState(false)

  useEffect(() => {
    Promise.all([api.getThongKeMe(), api.getPhanTichMe(), api.getHieuQuaMe()])
      .then(([t, p, h]) => { setTk(t); setPt(p); setHq(h) })
      .catch(() => {})
      .finally(() => setLoading(false))
    api.thongBao()
      .then((rows) => setNhanXet((rows || []).filter((t) => t.loai === 'nhan_xet')))
      .catch(() => {})
  }, [])

  async function capNhatAi() {
    setDangCapNhat(true)
    try { setPt(await api.capNhatPhanTichMe()) } catch { /* giữ nguyên */ }
    finally { setDangCapNhat(false) }
  }

  if (loading) return <p className="text-sm text-muted">Đang tải...</p>

  return (
    <div className="flex flex-col gap-6">
      <h2 className="text-2xl font-bold text-black">Tiến độ học tập</h2>
      <PhanTichNangLuc pt={pt} vaiTro="hs" onCapNhat={capNhatAi} dangCapNhat={dangCapNhat}
        onLuyen={onLuyenDang}
        sauNhanXet={
          <TheNhanXet nhanXet={nhanXet} trang={trangNx} onTrang={setTrangNx} />
        }
      />
      <BieuDoTuan data={hq} tieu_de="Diễn biến 8 tuần gần nhất của em" />
      <BanDoNangLuc taiDuLieu={api.getBanDoCuaToi} tieu_de="Bản đồ năng lực của em" />
      <ThongKeTienDo tk={tk} />
    </div>
  )
}
