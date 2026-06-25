import { useEffect, useState } from 'react'
import { api } from '../../api'
import ThongKeTienDo from '../../components/ThongKeTienDo'

export default function TienDo() {
  const [tk, setTk] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.getThongKeMe().then(setTk).catch(() => {}).finally(() => setLoading(false))
  }, [])

  if (loading) return <p className="text-sm text-muted">Đang tải...</p>

  return (
    <div className="flex flex-col gap-6">
      <h2 className="text-2xl font-bold text-ink">Tiến độ học tập</h2>
      <ThongKeTienDo tk={tk} />
    </div>
  )
}
