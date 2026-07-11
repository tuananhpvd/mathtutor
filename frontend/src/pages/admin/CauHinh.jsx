import { useEffect, useState } from 'react'
import { api } from '../../api'
import ImportTuKhoaDialog from '../../components/admin/ImportTuKhoaDialog'
import { Badge, Button, Card, CardBody, CardHeader, Input, Select, Table } from '../../components/ui'

const NHA_CUNG_CAP = [
  { value: 'gemini', label: 'Google Gemini (khuyến nghị)', model: 'gemini-2.5-flash' },
  { value: 'anthropic', label: 'Anthropic Claude', model: 'claude-opus-4-8' },
  { value: 'openai', label: 'OpenAI', model: 'gpt-4o-mini' },
  { value: 'stub', label: 'Tắt (mẫu cố định, demo)', model: '—' },
]

function KhoaApi({ label, p, provider, value, onChange, daDat }) {
  return (
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
}

const NHAN_TANG_TU_KHOA = {
  tu_khoa_khan_cap: {
    title: '🆘 Khẩn cấp / dấu hiệu tự hại',
    hint: 'Ưu tiên cao nhất. HS gõ trúng 1 từ ở đây sẽ nhận phản hồi ấm áp trong khung chat '
      + '(KHÔNG chặn lỗi kỹ thuật) và GV được báo ngay ở mức khẩn cấp.',
  },
  tu_khoa_khong_phu_hop: {
    title: '⚠️ Nội dung không phù hợp',
    hint: 'Gắn cờ báo GV (mức thường), phản hồi thân thiện hướng học sinh quay lại bài học.',
  },
  tu_khoa_ngoai_pham_vi: {
    title: '↩️ Ngoài phạm vi môn Toán',
    hint: 'Chỉ nhắc nhẹ hướng về bài học — KHÔNG gắn cờ, KHÔNG báo GV.',
  },
}

// khoa: 1 trong 3 khóa cấu hình tầng từ khóa. items: [{tu_khoa, kich_hoat, la_mac_dinh}].
// onDoi(khoa, danh_sach_moi): lưu ngay khi thêm/bật-tắt/xóa (không cần nút "Lưu" riêng).
// Dạng accordion (đóng mặc định) + bảng + ô tìm kiếm — danh sách dài (mặc định đã > 15
// từ/tầng, admin thêm thêm nữa) vẫn dễ scan thay vì 1 khối thẻ tràn lan.
function KhoiTuKhoa({ khoa, items, onDoi }) {
  const [moRong, setMoRong] = useState(false)
  const [timKiem, setTimKiem] = useState('')
  const [tuMoi, setTuMoi] = useState('')
  const meta = NHAN_TANG_TU_KHOA[khoa]
  const soBat = items.filter((x) => x.kich_hoat).length

  function themTu() {
    const t = tuMoi.trim()
    if (!t) return
    onDoi(khoa, [...items, { tu_khoa: t, kich_hoat: true }])
    setTuMoi('')
  }
  function batTat(item) {
    onDoi(khoa, items.map((x) => (x.tu_khoa === item.tu_khoa ? { ...x, kich_hoat: !x.kich_hoat } : x)))
  }
  function xoa(item) {
    onDoi(khoa, items.filter((x) => x.tu_khoa !== item.tu_khoa))
  }

  const timChuan = timKiem.trim().toLowerCase()
  const hienThi = timChuan
    ? items.filter((it) => it.tu_khoa.toLowerCase().includes(timChuan))
    : items

  return (
    <div className="rounded-lg border border-border overflow-hidden">
      <button type="button" onClick={() => setMoRong((v) => !v)}
        className="w-full flex items-center justify-between gap-3 px-4 py-3 bg-surface-2 text-left">
        <div>
          <p className="text-sm font-semibold text-ink">{meta.title}</p>
          <p className="text-[11px] text-muted">{meta.hint}</p>
        </div>
        <span className="text-xs text-muted whitespace-nowrap">
          {items.length} từ · {soBat} đang bật {moRong ? '▾' : '▸'}
        </span>
      </button>

      {moRong && (
        <div className="p-4 flex flex-col gap-3 border-t border-border">
          <Input
            placeholder="🔍 Tìm từ khóa..."
            value={timKiem}
            onChange={(e) => setTimKiem(e.target.value)}
          />
          <Table
            columns={[
              { key: 'tu_khoa', header: 'Từ khóa' },
              {
                key: 'loai',
                header: 'Loại',
                render: (r) => (
                  <Badge tone={r.la_mac_dinh ? 'neutral' : 'primary'}>
                    {r.la_mac_dinh ? 'Mặc định' : 'Tự thêm'}
                  </Badge>
                ),
              },
              {
                key: 'trang_thai',
                header: 'Trạng thái',
                render: (r) => (
                  <button type="button" onClick={() => batTat(r)}
                    className={`text-xs font-semibold ${r.kich_hoat ? 'text-success' : 'text-muted'}`}
                    title={r.kich_hoat ? 'Bấm để tắt từ khóa này' : 'Bấm để bật lại từ khóa này'}>
                    {r.kich_hoat ? '● Bật' : '○ Tắt'}
                  </button>
                ),
              },
              {
                key: 'hanh_dong',
                header: '',
                className: 'w-10 text-center',
                render: (r) =>
                  r.la_mac_dinh ? (
                    <span title="Từ khóa mặc định — chỉ tắt được, không xóa">🔒</span>
                  ) : (
                    <button type="button" className="text-danger font-bold" title="Xóa từ khóa tự thêm"
                      onClick={() => xoa(r)}>
                      ✕
                    </button>
                  ),
              },
            ]}
            rows={hienThi}
            rowKey={(r) => r.tu_khoa}
            empty={timChuan ? 'Không tìm thấy từ khóa nào khớp.' : 'Chưa có từ khóa nào.'}
          />
          <div className="flex gap-2 items-end max-w-md">
            <Input label="Thêm từ khóa mới" value={tuMoi} placeholder="vd: bỏ học đi bụi"
              onChange={(e) => setTuMoi(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); themTu() } }}
            />
            <Button size="sm" onClick={themTu} disabled={!tuMoi.trim()}>Thêm</Button>
          </div>
        </div>
      )}
    </div>
  )
}

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

  // Từ khóa lọc an toàn (3 tầng) — admin tự quản lý, không cần sửa code
  const [thuVanBan, setThuVanBan] = useState('')
  const [ketQuaThu, setKetQuaThu] = useState(null)
  const [dangThu, setDangThu] = useState(false)
  const [hienImportTuKhoa, setHienImportTuKhoa] = useState(false)
  const [msgImportTuKhoa, setMsgImportTuKhoa] = useState('')

  // Giới hạn lượt AI mỗi ngày (phanh chi phí)
  const [gioiHanHS, setGioiHanHS] = useState('')
  const [gioiHanHeThong, setGioiHanHeThong] = useState('')
  const [suDung, setSuDung] = useState(null)
  const [msgQuota, setMsgQuota] = useState('')

  // "Sản phẩm đang hoàn thiện" — chặn người ngoài xem trước khi ra mắt chính thức
  const [baoTriBat, setBaoTriBat] = useState(false)
  const [baoTriMa, setBaoTriMa] = useState('')
  const [baoTriNoiDung, setBaoTriNoiDung] = useState('')
  const [msgBaoTri, setMsgBaoTri] = useState('')

  function nap() {
    api.adminLLMSuDung().then(setSuDung).catch(() => setSuDung(null))
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
      setGioiHanHS(c.gioi_han_llm_hs_ngay ?? 30)
      setGioiHanHeThong(c.gioi_han_llm_he_thong_ngay ?? 500)
      setBaoTriBat(c.bao_tri_bat === true)
      setBaoTriMa(c.bao_tri_ma ?? '')
      setBaoTriNoiDung(c.bao_tri_noi_dung ?? '')
    }).catch((e) => setError(e.message))
  }
  useEffect(nap, [])

  async function luuBaoTri() {
    setMsgBaoTri(''); setError('')
    try {
      await api.adminSetConfig('bao_tri_bat', baoTriBat)
      await api.adminSetConfig('bao_tri_ma', baoTriMa.trim())
      await api.adminSetConfig('bao_tri_noi_dung', baoTriNoiDung.trim())
      nap()
      setMsgBaoTri('Đã lưu.')
    } catch (e) { setError(e.message) }
  }

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

  async function luuQuota() {
    setMsgQuota(''); setError('')
    try {
      await api.adminSetConfig('gioi_han_llm_hs_ngay', Math.max(0, Number(gioiHanHS) || 0))
      await api.adminSetConfig('gioi_han_llm_he_thong_ngay', Math.max(0, Number(gioiHanHeThong) || 0))
      nap()
      setMsgQuota('Đã lưu giới hạn.')
    } catch (e) { setError(e.message) }
  }

  async function luuGoiY() {
    setMsgGoiY(''); setError('')
    try {
      await api.adminSetConfig('so_goi_y_mac_dinh', goiY)
      nap()
      setMsgGoiY('Đã lưu.')
    } catch (e) { setError(e.message) }
  }

  async function luuTuKhoa(khoa, arr) {
    setError('')
    try {
      const c = await api.adminSetConfig(khoa, arr)
      setCfg(c)
    } catch (e) { setError(e.message) }
  }

  async function thuKiemTraTuKhoa() {
    if (!thuVanBan.trim()) return
    setDangThu(true); setError('')
    try {
      setKetQuaThu(await api.adminTuKhoaThu(thuVanBan.trim()))
    } catch (e) { setError(e.message) } finally { setDangThu(false) }
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

  if (!cfg && error) {
    return (
      <div className="flex items-center gap-3 text-sm text-danger">
        <span>Không tải được cấu hình: {error}</span>
        <Button variant="secondary" onClick={() => { setError(''); nap() }}>Thử lại</Button>
      </div>
    )
  }
  if (!cfg) return <p className="text-muted text-sm">Đang tải cấu hình...</p>

  const modelMacDinh = NHA_CUNG_CAP.find((n) => n.value === provider)?.model || ''

  const urlXemTruoc = baoTriMa
    ? `${window.location.origin}/?ma=${encodeURIComponent(baoTriMa)}`
    : ''

  return (
    <div className="flex flex-col gap-5">
      <Card>
        <CardHeader title="Chế độ bảo trì"
          subtitle="Khi bật, người ngoài truy cập trang chỉ thấy dòng thông báo. Người có đúng mã xem trước (mở qua đường dẫn bên dưới) vẫn dùng bình thường, kể cả đăng nhập GV/HS/Admin." />
        <CardBody className="flex flex-col gap-4">
          <label className="flex items-center gap-3 cursor-pointer">
            <input type="checkbox" className="h-4 w-4 accent-primary"
              checked={baoTriBat} onChange={(e) => setBaoTriBat(e.target.checked)} />
            <span className="text-sm text-ink">Bật trang "đang bảo trì" cho người ngoài</span>
            {cfg.bao_tri_bat === true
              ? <Badge tone="warning">Đang chặn</Badge>
              : <Badge tone="success">Đang mở cho mọi người</Badge>}
          </label>
          <div className="max-w-sm">
            <Input
              label="Mã xem trước (dùng trong đường dẫn để tự vào test)"
              value={baoTriMa}
              onChange={(e) => setBaoTriMa(e.target.value)}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-ink mb-1">
              Nội dung thông báo hiển thị cho người ngoài
            </label>
            <textarea
              className="w-full rounded-md border border-border bg-surface px-3 py-2 text-sm
                text-ink placeholder:text-muted focus:outline-none focus:ring-2
                focus:ring-primary/40 focus:border-primary"
              rows={3}
              value={baoTriNoiDung}
              onChange={(e) => setBaoTriNoiDung(e.target.value)}
            />
          </div>
          {urlXemTruoc && (
            <div className="rounded-lg bg-surface-2 px-4 py-3">
              <p className="text-xs text-muted mb-1">Đường dẫn xem trước (mở 1 lần trên trình duyệt của bạn là nhớ luôn):</p>
              <code className="text-sm text-primary break-all">{urlXemTruoc}</code>
            </div>
          )}
          <div className="flex items-center gap-3">
            <Button onClick={luuBaoTri}>Lưu</Button>
            {msgBaoTri && <span className="text-sm text-success">{msgBaoTri}</span>}
          </div>
        </CardBody>
      </Card>

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
        <CardHeader title="Từ khóa lọc an toàn"
          subtitle="Tự thêm/bật/tắt từ khóa mà không cần sửa code — áp dụng ngay cho ô chat hỏi gia sư và 'Nhờ thầy/cô'. Từ khóa mặc định (🔒) chỉ tắt được, không xóa được, để giữ nền an toàn."
          action={
            <Button variant="secondary" size="sm" onClick={() => setHienImportTuKhoa(true)}>
              Import từ file mẫu
            </Button>
          }
        />
        <CardBody className="flex flex-col gap-5">
          {msgImportTuKhoa && <p className="text-sm text-success">{msgImportTuKhoa}</p>}
          <KhoiTuKhoa khoa="tu_khoa_khan_cap" items={cfg.tu_khoa_khan_cap || []} onDoi={luuTuKhoa} />
          <KhoiTuKhoa khoa="tu_khoa_khong_phu_hop" items={cfg.tu_khoa_khong_phu_hop || []} onDoi={luuTuKhoa} />
          <KhoiTuKhoa khoa="tu_khoa_ngoai_pham_vi" items={cfg.tu_khoa_ngoai_pham_vi || []} onDoi={luuTuKhoa} />

          <div className="rounded-lg bg-surface-2 px-4 py-3 flex flex-col gap-2">
            <p className="text-sm font-semibold text-ink">Thử trước</p>
            <p className="text-[11px] text-muted">
              Gõ 1 câu mẫu để kiểm tra với đúng danh sách từ khóa đang lưu ở trên (không tạo phiên
              học, không gắn cờ).
            </p>
            <div className="flex gap-2 items-end max-w-lg">
              <Input value={thuVanBan} placeholder="vd: em cảm thấy mệt muốn chết"
                onChange={(e) => setThuVanBan(e.target.value)}
                onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); thuKiemTraTuKhoa() } }}
              />
              <Button size="sm" onClick={thuKiemTraTuKhoa} disabled={dangThu || !thuVanBan.trim()}>
                {dangThu ? 'Đang kiểm tra...' : 'Kiểm tra'}
              </Button>
            </div>
            {ketQuaThu && (
              ketQuaThu.an_toan
                ? <Badge tone="success">An toàn — không khớp từ khóa nào</Badge>
                : <Badge tone={ketQuaThu.khan_cap ? 'danger' : 'warning'}>{ketQuaThu.ly_do}</Badge>
            )}
          </div>
          {error && <p className="text-sm text-danger">{error}</p>}
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
              <KhoaApi label="Khóa API Google Gemini" p="gemini" provider={provider}
                value={keyGemini} onChange={setKeyGemini} daDat={cfg.llm_api_key_gemini_da_dat} />
              <KhoaApi label="Khóa API Anthropic Claude" p="anthropic" provider={provider}
                value={keyAnthropic} onChange={setKeyAnthropic} daDat={cfg.llm_api_key_anthropic_da_dat} />
              <KhoaApi label="Khóa API OpenAI" p="openai" provider={provider}
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
        <CardHeader title="Giới hạn lượt AI mỗi ngày (phanh chi phí)"
          subtitle="Vượt ngưỡng: hội thoại chuyển sang lời gợi ý mẫu (học sinh vẫn học bình thường); sinh câu hỏi/phân tích tạm dừng đến ngày mai. 0 = không giới hạn." />
        <CardBody className="flex flex-col gap-4">
          {suDung && (() => {
            const gh = suDung.gioi_han_he_thong_ngay
            const canhBao = gh > 0 && suDung.tong >= gh * 0.8
            return (
              <div className={`rounded-lg px-4 py-3 text-sm ${canhBao ? 'bg-warning-soft' : 'bg-surface-2'}`}>
                <p className="font-semibold text-ink">
                  Hôm nay đã dùng: {suDung.tong}{gh > 0 ? ` / ${gh}` : ''} lượt AI thật
                  {canhBao && <Badge tone="warning" className="ml-2">Sắp chạm giới hạn</Badge>}
                </p>
                <p className="text-muted mt-1">
                  Hội thoại gia sư: {suDung.theo_loai.hoi_thoai} · Sinh câu hỏi:{' '}
                  {suDung.theo_loai.sinh_cau_hoi} · Phân tích năng lực: {suDung.theo_loai.phan_tich}
                  {' '}(tính theo ngày UTC; lượt dùng mẫu cố định không tính)
                </p>
              </div>
            )
          })()}
          <div className="flex gap-4 items-end flex-wrap">
            <Input
              type="number" label="Lượt hội thoại / học sinh / ngày" value={gioiHanHS}
              min={0} className="w-56"
              onChange={(e) => setGioiHanHS(e.target.value)}
            />
            <Input
              type="number" label="Tổng lượt toàn hệ thống / ngày" value={gioiHanHeThong}
              min={0} className="w-56"
              onChange={(e) => setGioiHanHeThong(e.target.value)}
            />
            <Button onClick={luuQuota}>Lưu</Button>
            {msgQuota && <span className="text-sm text-success">{msgQuota}</span>}
          </div>
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
            <Button variant="secondary" onClick={quetNgay} disabled={dangQuet}>
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

      {hienImportTuKhoa && (
        <ImportTuKhoaDialog
          cfg={cfg}
          onClose={() => setHienImportTuKhoa(false)}
          onSaved={(soLuong) => {
            setHienImportTuKhoa(false)
            setMsgImportTuKhoa(`Đã import ${soLuong} từ khóa mới.`)
            nap()
          }}
        />
      )}
    </div>
  )
}
