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
  const [chotChan, setChotChan] = useState('')
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
  const [thinkGemini, setThinkGemini] = useState(false)
  const [thinkAnthropic, setThinkAnthropic] = useState(false)
  const [thinkOpenai, setThinkOpenai] = useState(false)

  // Tự động phân tích năng lực
  const [tuDong, setTuDong] = useState(true)
  const [chuKy, setChuKy] = useState('')
  const [msgPt, setMsgPt] = useState('')
  const [dangQuet, setDangQuet] = useState(false)

  // Số gợi ý mặc định theo độ khó
  const [goiY, setGoiY] = useState(null)
  const [msgGoiY, setMsgGoiY] = useState('')

  function nap() {
    api.adminGetConfig().then((c) => {
      setCfg(c)
      setNguong(c.nguong_co_khong_hieu)
      setChotChan(c.nguong_co_chot_chan)
      setTemp(c.llm_temperature)
      setNghi(c.nguong_nghi_giay)
      setProvider(c.llm_provider || 'gemini')
      setModel(c.llm_model || '')
      setThinkGemini(c.llm_thinking_gemini === true)
      setThinkAnthropic(c.llm_thinking_anthropic === true)
      setThinkOpenai(c.llm_thinking_openai === true)
      setTuDong(c.tu_dong_phan_tich !== false)
      setChuKy(c.chu_ky_phut_phan_tich ?? 360)
      setGoiY(c.so_goi_y_mac_dinh ? { ...c.so_goi_y_mac_dinh } : { de: 2, tb: 3, kho: 4 })
    })
  }
  useEffect(nap, [])

  async function luuTuDong() {
    setMsgPt(''); setError('')
    try {
      await api.adminSetConfig('tu_dong_phan_tich', tuDong)
      await api.adminSetConfig('chu_ky_phut_phan_tich', Math.max(5, Number(chuKy) || 360))
      nap()
      setMsgPt('Đã lưu cấu hình tự động phân tích.')
    } catch (e) {
      setError(e.message)
    }
  }

  async function quetNgay() {
    setMsgPt(''); setError(''); setDangQuet(true)
    try {
      const r = await api.adminQuetPhanTich()
      setMsgPt(`Đã quét ${r.da_quet} học sinh — cập nhật ${r.da_cap_nhat}, lỗi ${r.loi}.`)
    } catch (e) {
      setError(e.message)
    } finally {
      setDangQuet(false)
    }
  }

  async function luuGoiY() {
    setMsgGoiY(''); setError('')
    try {
      await api.adminSetConfig('so_goi_y_mac_dinh', goiY)
      nap()
      setMsgGoiY('Đã lưu.')
    } catch (e) { setError(e.message) }
  }

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
      await api.adminSetConfig('llm_thinking_gemini', thinkGemini)
      await api.adminSetConfig('llm_thinking_anthropic', thinkAnthropic)
      await api.adminSetConfig('llm_thinking_openai', thinkOpenai)
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
              label="Ngưỡng cờ 'chốt chặn nhiều'"
              type="number"
              value={chotChan}
              onChange={(e) => setChotChan(e.target.value)}
            />
            <Button onClick={() => luu('nguong_co_chot_chan', Number(chotChan))}>Lưu</Button>
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

          <div className="rounded-lg bg-surface-2 px-4 py-3 flex flex-col gap-2">
            <p className="text-sm font-semibold text-ink">Chế độ suy luận (thinking)</p>
            <p className="text-[12px] text-muted">
              Bật giúp câu trả lời sâu hơn nhưng chậm & tốn token hơn. Mặc định TẮT cho nhanh,
              ổn định (tránh suy luận ăn token gây lỗi cắt cụt). Áp dụng khi nhà cung cấp hỗ trợ.
            </p>
            <label className="flex items-center gap-2 cursor-pointer text-sm text-ink">
              <input type="checkbox" className="h-4 w-4 accent-primary"
                checked={thinkGemini} onChange={(e) => setThinkGemini(e.target.checked)} />
              Google Gemini
            </label>
            <label className="flex items-center gap-2 cursor-pointer text-sm text-ink">
              <input type="checkbox" className="h-4 w-4 accent-primary"
                checked={thinkAnthropic} onChange={(e) => setThinkAnthropic(e.target.checked)} />
              Anthropic Claude
            </label>
            <label className="flex items-center gap-2 cursor-pointer text-sm text-ink">
              <input type="checkbox" className="h-4 w-4 accent-primary"
                checked={thinkOpenai} onChange={(e) => setThinkOpenai(e.target.checked)} />
              OpenAI <span className="text-[11px] text-muted">(chỉ tác dụng với model dòng reasoning)</span>
            </label>
          </div>

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
        <CardHeader title="Tự động phân tích năng lực (AI)"
          subtitle="Hệ thống tự tái sinh nhận định AI cho học sinh đến hạn — GV/HS không cần bấm tay." />
        <CardBody className="flex flex-col gap-4">
          <label className="flex items-center gap-3 cursor-pointer">
            <input type="checkbox" className="h-4 w-4 accent-primary"
              checked={tuDong} onChange={(e) => setTuDong(e.target.checked)} />
            <span className="text-sm text-ink">Bật tự động phân tích theo lịch nền</span>
            {cfg.tu_dong_phan_tich !== false
              ? <Badge tone="success">Đang bật</Badge>
              : <Badge tone="warning">Đang tắt</Badge>}
          </label>
          <div className="flex items-end gap-2 max-w-xs">
            <Input
              label="Chu kỳ quét (phút, tối thiểu 5)"
              type="number"
              min={5}
              value={chuKy}
              onChange={(e) => setChuKy(e.target.value)}
              disabled={!tuDong}
            />
          </div>
          <div className="flex items-center gap-3 flex-wrap">
            <Button onClick={luuTuDong}>Lưu</Button>
            <Button variant="ghost" onClick={quetNgay} disabled={dangQuet}>
              {dangQuet ? 'Đang quét...' : 'Quét ngay'}
            </Button>
            {msgPt && <span className="text-sm text-success">{msgPt}</span>}
          </div>
          <p className="text-[12px] text-muted">
            Phân tích chỉ tái sinh khi học sinh có thêm bài (≥5) hoặc bản cũ quá 7 ngày, nên không
            tốn lời gọi AI thừa. Cần nhà cung cấp AI đã có khóa ở trên thì nhận định mới được tạo.
          </p>
        </CardBody>
      </Card>

      <Card>
        <CardHeader title="Số gợi ý mặc định theo độ khó" subtitle="Giá trị khởi tạo khi tạo/AI sinh bài" />
        <CardBody className="flex flex-col gap-4">
          <div className="flex gap-4 items-end flex-wrap">
            {goiY && (
              <>
                <Input
                  type="number" label="Dễ" value={goiY.de} min={1} max={10}
                  className="w-24"
                  onChange={(e) => setGoiY((g) => ({ ...g, de: Number(e.target.value) }))}
                />
                <Input
                  type="number" label="Trung bình" value={goiY.tb} min={1} max={10}
                  className="w-28"
                  onChange={(e) => setGoiY((g) => ({ ...g, tb: Number(e.target.value) }))}
                />
                <Input
                  type="number" label="Khó" value={goiY.kho} min={1} max={10}
                  className="w-24"
                  onChange={(e) => setGoiY((g) => ({ ...g, kho: Number(e.target.value) }))}
                />
                <Button onClick={luuGoiY}>Lưu</Button>
                {msgGoiY && <span className="text-sm text-success">{msgGoiY}</span>}
              </>
            )}
          </div>
        </CardBody>
      </Card>
    </div>
  )
}
