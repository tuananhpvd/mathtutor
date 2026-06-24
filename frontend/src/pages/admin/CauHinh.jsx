import { useEffect, useState } from 'react'
import { api } from '../../api'
import { Button, Card, CardBody, CardHeader, Input } from '../../components/ui'

export default function CauHinh() {
  const [cfg, setCfg] = useState(null)
  const [nguong, setNguong] = useState('')
  const [temp, setTemp] = useState('')
  const [msg, setMsg] = useState('')
  const [error, setError] = useState('')

  function nap() {
    api.adminGetConfig().then((c) => {
      setCfg(c)
      setNguong(c.nguong_co_khong_hieu)
      setTemp(c.llm_temperature)
    })
  }
  useEffect(nap, [])

  async function luu(khoa, gia_tri) {
    setMsg('')
    setError('')
    try {
      const c = await api.adminSetConfig(khoa, gia_tri)
      setCfg(c)
      setMsg('Đã lưu cấu hình.')
    } catch (e) {
      setError(e.message)
    }
  }

  if (!cfg) return <p className="text-muted text-sm">Đang tải cấu hình...</p>

  return (
    <div className="flex flex-col gap-5">
      <Card>
        <CardHeader title="Ngưỡng & LLM" subtitle="Áp dụng cho toàn hệ thống" />
        <CardBody className="grid sm:grid-cols-2 gap-4 items-end">
          <div className="flex items-end gap-2">
            <Input
              label="Ngưỡng cờ 'không hiểu nhiều'"
              type="number"
              value={nguong}
              onChange={(e) => setNguong(e.target.value)}
            />
            <Button onClick={() => luu('nguong_co_khong_hieu', Number(nguong))}>Lưu</Button>
          </div>
          <div className="flex items-end gap-2">
            <Input
              label="Nhiệt độ LLM"
              type="number"
              step="0.1"
              value={temp}
              onChange={(e) => setTemp(e.target.value)}
            />
            <Button onClick={() => luu('llm_temperature', Number(temp))}>Lưu</Button>
          </div>
          {msg && <p className="text-sm text-success sm:col-span-2">{msg}</p>}
          {error && <p className="text-sm text-danger sm:col-span-2">{error}</p>}
        </CardBody>
      </Card>

      <Card>
        <CardHeader title="Số gợi ý mặc định theo độ khó" subtitle="Giá trị khởi tạo khi tạo/AI sinh bài" />
        <CardBody className="flex gap-6">
          {Object.entries(cfg.so_goi_y_mac_dinh || {}).map(([k, v]) => (
            <div key={k}>
              <p className="text-sm text-muted uppercase">{k}</p>
              <p className="text-2xl font-semibold text-primary">{v}</p>
            </div>
          ))}
        </CardBody>
      </Card>

      <Card>
        <CardHeader title="Bảng điểm bậc thang TNDS" subtitle="Số ý đúng → điểm" />
        <CardBody>
          <div className="flex gap-3">
            {Object.entries(cfg.bang_bac_thang || {}).map(([k, v]) => (
              <div key={k} className="rounded-md bg-surface-2 px-4 py-2 text-center">
                <p className="text-xs text-muted">{k} ý đúng</p>
                <p className="text-lg font-semibold text-ink">{v}</p>
              </div>
            ))}
          </div>
        </CardBody>
      </Card>
    </div>
  )
}
