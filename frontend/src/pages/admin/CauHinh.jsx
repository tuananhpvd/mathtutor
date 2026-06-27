import { useEffect, useState } from 'react'
import { api } from '../../api'
import { Badge, Button, Card, CardBody, CardHeader, Input, Select } from '../../components/ui'

const NHA_CUNG_CAP = [
  { value: 'gemini', label: 'Google Gemini (khuyến nghị)', model: 'gemini-2.5-flash' },
  { value: 'anthropic', label: 'Anthropic Claude', model: 'claude-opus-4-8' },
  { value: 'openai', label: 'OpenAI', model: 'gpt-4o-mini' },
  { value: 'stub', label: 'Tắt (mẫu cố định, demo)', model: '—' },
]

export default function CauHinh() {
  const [cfg, setCfg] = useState(null)
  const [nguong, setNguong] = useState('')
  const [temp, setTemp] = useState('')
  const [nghi, setNghi] = useState('')
  const [msg, setMsg] = useState('')
  const [error, setError] = useState('')

  // Cấu hình AI
  const [provider, setProvider] = useState('gemini')
  const [model, setModel] = useState('')
  const [keyGemini, setKeyGemini] = useState('')
  const [keyAnthropic, setKeyAnthropic] = useState('')
  const [keyOpenai, setKeyOpenai] = useState('')
  const [msgAI, setMsgAI] = useState('')

  function nap() {
    api.adminGetConfig().then((c) => {
      setCfg(c)
      setNguong(c.nguong_co_khong_hieu)
      setTemp(c.llm_temperature)
      setNghi(c.nguong_nghi_giay)
      setProvider(c.llm_provider || 'gemini')
      setModel(c.llm_model || '')
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

  async function luuAI() {
    setMsgAI(''); setError('')
    try {
      await api.adminSetConfig('llm_provider', provider)
      await api.adminSetConfig('llm_model', model)
      // Khóa API chỉ gửi khi có nhập (để trống = giữ nguyên).
      if (keyGemini.trim()) await api.adminSetConfig('llm_api_key_gemini', keyGemini.trim())
      if (keyAnthropic.trim()) await api.adminSetConfig('llm_api_key_anthropic', keyAnthropic.trim())
      if (keyOpenai.trim()) await api.adminSetConfig('llm_api_key_openai', keyOpenai.trim())
      setKeyGemini(''); setKeyAnthropic(''); setKeyOpenai('')
      nap()
      setMsgAI('Đã lưu cấu hình AI.')
    } catch (e) {
      setError(e.message)
    }
  }

  if (!cfg) return <p className="text-muted text-sm">Đang tải cấu hình...</p>

  const modelMacDinh = NHA_CUNG_CAP.find((n) => n.value === provider)?.model || ''
  const KhoaApi = ({ label, p, value, onChange, daDat }) => (
    <div>
      <div className="flex items-center gap-2 mb-1">
        <span className="text-xs text-muted">{label}</span>
        {daDat
          ? <Badge tone="success">Đã lưu khóa</Badge>
          : <Badge tone="warning">Chưa có khóa</Badge>}
        {provider === p && <Badge tone="primary">Đang dùng</Badge>}
      </div>
      <Input
        type="password"
        placeholder={daDat ? '•••••••• (để trống nếu giữ nguyên)' : 'Dán khóa API vào đây'}
        value={value}
        onChange={(e) => onChange(e.target.value)}
      />
    </div>
  )

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
          <div className="flex items-end gap-2 sm:col-span-2">
            <Input
              label="Ngưỡng nghỉ (giây) — chặn thời gian rời đi khi tính giờ làm bài"
              type="number"
              min={30}
              value={nghi}
              onChange={(e) => setNghi(e.target.value)}
            />
            <Button onClick={() => luu('nguong_nghi_giay', Number(nghi))}>Lưu</Button>
          </div>
          <p className="text-[11px] text-muted sm:col-span-2">
            Khoảng cách giữa 2 lần học sinh thao tác vượt ngưỡng này được coi là "rời đi" và chỉ
            tính tối đa bằng ngưỡng — để thời gian hoàn thành phản ánh đúng công sức thực, kể cả khi
            học sinh "quay lại làm sau".
          </p>
          {msg && <p className="text-sm text-success sm:col-span-2">{msg}</p>}
          {error && <p className="text-sm text-danger sm:col-span-2">{error}</p>}
        </CardBody>
      </Card>

      <Card>
        <CardHeader title="AI sinh câu hỏi"
          subtitle="Chọn nhà cung cấp & nhập khóa API. Khóa được lưu phía máy chủ, không hiển thị lại." />
        <CardBody className="flex flex-col gap-4">
          <div className="grid sm:grid-cols-2 gap-4">
            <Select
              label="Nhà cung cấp"
              value={provider}
              onChange={(e) => setProvider(e.target.value)}
              options={NHA_CUNG_CAP.map((n) => ({ value: n.value, label: n.label }))}
            />
            <Input
              label={`Model (để trống = mặc định: ${modelMacDinh})`}
              placeholder={modelMacDinh}
              value={model}
              onChange={(e) => setModel(e.target.value)}
              disabled={provider === 'stub'}
            />
          </div>

          {provider !== 'stub' && (
            <div className="grid sm:grid-cols-1 gap-3">
              <KhoaApi label="Khóa API Google Gemini" p="gemini"
                value={keyGemini} onChange={setKeyGemini} daDat={cfg.llm_api_key_gemini_da_dat} />
              <KhoaApi label="Khóa API Anthropic Claude" p="anthropic"
                value={keyAnthropic} onChange={setKeyAnthropic} daDat={cfg.llm_api_key_anthropic_da_dat} />
              <KhoaApi label="Khóa API OpenAI" p="openai"
                value={keyOpenai} onChange={setKeyOpenai} daDat={cfg.llm_api_key_openai_da_dat} />
            </div>
          )}

          <div className="flex items-center gap-3">
            <Button onClick={luuAI}>Lưu cấu hình AI</Button>
            {msgAI && <span className="text-sm text-success">{msgAI}</span>}
          </div>
          <p className="text-[12px] text-muted">
            Nếu nhà cung cấp đang chọn chưa có khóa, hệ thống tạm dùng mẫu cố định (không sinh theo
            yêu cầu). Lấy khóa: Gemini tại Google AI Studio, Claude tại console.anthropic.com,
            OpenAI tại platform.openai.com.
          </p>
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
