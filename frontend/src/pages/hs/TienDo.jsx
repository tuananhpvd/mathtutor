import { useEffect, useState } from 'react'
import { api } from '../../api'
import ThongKeTienDo from '../../components/ThongKeTienDo'
import PhanTichNangLuc from '../../components/PhanTichNangLuc'
import BanDoNangLuc from '../../components/BanDoNangLuc'

export default function TienDo({ onLuyenDang }) {
  const [tk, setTk] = useState(null)
  const [pt, setPt] = useState(null)
  const [loading, setLoading] = useState(true)
  const [dangCapNhat, setDangCapNhat] = useState(false)

  useEffect(() => {
    Promise.all([api.getThongKeMe(), api.getPhanTichMe()])
      .then(([t, p]) => { setTk(t); setPt(p) })
      .catch(() => {})
      .finally(() => setLoading(false))
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
        onLuyen={onLuyenDang} />
      <BanDoNangLuc taiDuLieu={api.getBanDoCuaToi} tieu_de="Bản đồ năng lực của em" />
      <ThongKeTienDo tk={tk} />
    </div>
  )
}
