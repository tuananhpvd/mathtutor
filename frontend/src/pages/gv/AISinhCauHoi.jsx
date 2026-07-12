import { useMemo, useRef, useState, useEffect } from 'react'
import { api } from '../../api'
import { Badge, Button, Card, CardBody, CardHeader, Input, Select } from '../../components/ui'
import Formula from '../../components/Formula'
import { ThanCauHoiForm } from './quanLyCauHoi/ThanCauHoiForm'
import { SuaCauHoi } from './quanLyCauHoi/SuaTaoCauHoi'
import { BangCongThuc } from './quanLyCauHoi/BangCongThuc'
import { TexField } from './quanLyCauHoi/TexField'
import { chuanHoaSteps, dungDangOptions, kiemTraDapAnTLN } from '../../utils/cauHoi'

function renderTex(text) {
  return String(text)
    .split(/(\$[^$]+\$)/g)
    .map((p, i) =>
      p.startsWith('$') ? <Formula key={i} latex={p.slice(1, -1)} /> : <span key={i}>{p}</span>
    )
}

// Hiện đầy đủ nội dung câu hỏi nháp: đề + phương án ABCD (TN4PA) / 4 ý a–d (TNDS) / đáp án (TLN).
function NoiDungCauHoi({ c }) {
  const meta = c.meta || {}
  return (
    <div className="flex flex-col gap-2">
      <p className="text-sm text-ink font-medium">{renderTex(c.de_bai)}</p>

      {c.loai_cau === 'TN4PA' && meta.phuong_an && (
        <div className="flex flex-col gap-1 pl-1">
          {['A', 'B', 'C', 'D'].map((k) => (
            <div key={k} className="flex items-start gap-2 text-sm">
              <span className={`font-bold ${meta.dap_an_dung === k ? 'text-success' : 'text-ink'}`}>
                {k}.
              </span>
              <span className="text-ink">{renderTex(meta.phuong_an[k] || '')}</span>
              {meta.dap_an_dung === k && <Badge tone="success">Đáp án đúng</Badge>}
            </div>
          ))}
        </div>
      )}

      {c.loai_cau === 'TNDS' && Array.isArray(meta.y) && (
        <div className="flex flex-col gap-1 pl-1">
          {meta.y.map((y) => (
            <div key={y.ky_hieu} className="flex items-start gap-2 text-sm">
              <span className="font-bold text-ink">{y.ky_hieu})</span>
              <span className="text-ink">{renderTex(y.noi_dung_y || '')}</span>
              <Badge tone={y.dap_an === 'Dung' ? 'success' : 'danger'}>
                {y.dap_an === 'Dung' ? 'Đúng' : 'Sai'}
              </Badge>
            </div>
          ))}
        </div>
      )}

      {c.loai_cau === 'TLN' && meta.dap_an_cuoi != null && (
        <p className="text-sm pl-1">
          <span className="text-muted">Đáp án: </span>
          <b className="text-success">{renderTex(String(meta.dap_an_cuoi))}</b>
        </p>
      )}
    </div>
  )
}

const MAC_DINH_SO_GOI_Y = { de: 2, tb: 3, kho: 4 }
const NHAN_LOAI_CAU = { TN4PA: 'Trắc nghiệm A–D', TNDS: 'Đúng/Sai 4 ý', TLN: 'Trả lời ngắn' }

// Ô dán ảnh đề từ clipboard (Ctrl+V) — đọc file ảnh, xem trước, gọi AI nhận dạng.
function ODanAnh({ anhDan, onDanAnh, onXoaAnh, onNhanDang, dangDoc, loaiCau }) {
  function xuLyPaste(e) {
    const items = e.clipboardData?.items
    if (!items) return
    for (const item of items) {
      if (item.type.startsWith('image/')) {
        const file = item.getAsFile()
        if (!file) continue
        const reader = new FileReader()
        reader.onload = () => onDanAnh({ dataUrl: reader.result, mimeType: file.type })
        reader.readAsDataURL(file)
        e.preventDefault()
        return
      }
    }
  }

  return (
    <div className="rounded-lg border border-dashed border-border bg-surface-2 px-4 py-3 flex flex-col gap-2">
      <p className="text-sm font-semibold text-ink">Dán ảnh đề bài (tùy chọn)</p>
      <p className="text-xs text-muted">
        Chụp/copy ảnh đề rồi bấm vào ô dưới và dán (Ctrl+V) — AI sẽ đọc ảnh và tự điền đề bài{loaiCau === 'TN4PA' ? '/phương án' : loaiCau === 'TNDS' ? '/4 ý' : ''} bên dưới để anh/chị kiểm tra lại trước khi tạo. Ảnh chỉ dùng để đọc, không được lưu lại.
      </p>
      {anhDan ? (
        <div className="flex flex-col gap-2">
          <img src={anhDan.dataUrl} alt="Ảnh đề đã dán" className="max-h-40 max-w-full rounded-md border border-border" />
          <div className="flex flex-wrap gap-2">
            <Button onClick={onNhanDang} disabled={dangDoc}>
              {dangDoc ? 'AI đang đọc ảnh...' : '🔎 Nhận dạng từ ảnh'}
            </Button>
            <Button variant="secondary" onClick={onXoaAnh} disabled={dangDoc}>Xóa ảnh</Button>
          </div>
        </div>
      ) : (
        <div
          tabIndex={0}
          onPaste={xuLyPaste}
          className="rounded-md border border-border bg-surface px-3 py-6 text-center text-sm text-muted cursor-text focus:outline-none focus:ring-2 focus:ring-primary"
        >
          Bấm vào đây rồi dán ảnh (Ctrl+V)
        </div>
      )}
    </div>
  )
}

// "AI tạo bước và gợi ý": GV viết đề bài (+ phương án/ý) sẵn + quy định số bước/số gợi ý —
// AI CHỈ giải ra đáp án đúng, chia đúng số bước, viết đúng số gợi ý mỗi bước. Khác luồng
// "Sinh hàng loạt" (AI tự bịa đề, lưu thẳng) — công cụ này CHƯA lưu DB khi bấm Tạo, GV xem/sửa
// bản nháp (tái dùng đúng khung ThanCauHoiForm của màn Sửa câu hỏi) rồi mới bấm Lưu.
function TaoBuocGoiYPanel({ danhMuc, onLuuXong }) {
  const dangOptions = useMemo(() => dungDangOptions(danhMuc), [danhMuc])

  // Cơ chế chèn ký hiệu từ Bảng công thức vào đúng ô đang focus (đề bài/phương án/ý).
  const activeInsert = useRef(null)
  const register = (fn) => { activeInsert.current = fn }
  const chen = (s, b) => activeInsert.current?.(s, b)

  const [form, setForm] = useState({
    dang_id: '', loai_cau: 'TLN', do_kho: 'tb', de_bai: '',
    phuong_an: { A: '', B: '', C: '', D: '' },
    y: ['a', 'b', 'c', 'd'].map((k) => ({ ky_hieu: k, noi_dung_y: '' })),
  })
  const [soBuoc, setSoBuoc] = useState(1)
  const [soGoiYList, setSoGoiYList] = useState([MAC_DINH_SO_GOI_Y.tb])
  const [dangTao, setDangTao] = useState(false)
  const [error, setError] = useState('')
  const [nhap, setNhap] = useState(null) // {cau, canh_bao} bản nháp — CHƯA lưu DB
  const [dangLuu, setDangLuu] = useState(false)
  const [anhDan, setAnhDan] = useState(null) // { dataUrl, mimeType } — chỉ dùng để AI đọc, không lưu
  const [dangDocAnh, setDangDocAnh] = useState(false)

  async function nhanDangTuAnh() {
    if (!anhDan) return
    setError('')
    setDangDocAnh(true)
    try {
      const ket = await api.docDeTuAnh({
        anh_base64: anhDan.dataUrl, mime_type: anhDan.mimeType, loai_cau_ky_vong: form.loai_cau,
      })
      if (!ket.khop_loai_cau) {
        const nhanNhanDang = NHAN_LOAI_CAU[ket.loai_cau_nhan_dang] || ket.loai_cau_nhan_dang || 'không rõ'
        setError(
          `Ảnh có vẻ là dạng "${nhanNhanDang}" nhưng ô "Loại câu" đang chọn là "${NHAN_LOAI_CAU[form.loai_cau]}".` +
          (ket.ly_do_khong_khop ? ` ${ket.ly_do_khong_khop}` : '') +
          ' Vui lòng đổi lại ô Loại câu hoặc dán đúng ảnh.'
        )
        return
      }
      setForm((f) => ({
        ...f,
        de_bai: ket.de_bai || f.de_bai,
        phuong_an: f.loai_cau === 'TN4PA' && ket.meta_nhap?.phuong_an
          ? { ...f.phuong_an, ...ket.meta_nhap.phuong_an } : f.phuong_an,
        y: f.loai_cau === 'TNDS' && Array.isArray(ket.meta_nhap?.y) ? ket.meta_nhap.y : f.y,
      }))
      // Giữ ảnh lại để GV đối chiếu chữ AI đọc được với ảnh gốc — chỉ mất khi bấm
      // "Xóa ảnh" hoặc bấm "Tạo bước và gợi ý" (xem hàm tao()).
    } catch (e) {
      setError(e.message)
    } finally {
      setDangDocAnh(false)
    }
  }

  function doiLoaiCau(loai) {
    setForm((f) => ({ ...f, loai_cau: loai }))
    if (loai === 'TNDS') {
      setSoGoiYList((gy) => Array.from({ length: 4 }, (_, i) => gy[i] || MAC_DINH_SO_GOI_Y[form.do_kho] || 2))
    }
  }

  function doiSoBuoc(n) {
    const so = Math.max(1, Math.min(6, Number(n) || 1))
    setSoBuoc(so)
    setSoGoiYList((gy) => Array.from({ length: so }, (_, i) => gy[i] || MAC_DINH_SO_GOI_Y[form.do_kho] || 2))
  }

  function capCauTrucBuoc() {
    if (form.loai_cau === 'TNDS') {
      return ['a', 'b', 'c', 'd'].map((k, i) => ({ pham_vi: k, so_goi_y: Number(soGoiYList[i]) || 1 }))
    }
    return Array.from({ length: soBuoc }, (_, i) => ({ pham_vi: 'ca_bai', so_goi_y: Number(soGoiYList[i]) || 1 }))
  }

  async function tao() {
    setError('')
    if (!form.dang_id) { setError('Vui lòng chọn Chuyên đề › Dạng.'); return }
    if (!form.de_bai.trim()) { setError('Vui lòng nhập đề bài.'); return }
    if (form.loai_cau === 'TN4PA' && Object.values(form.phuong_an).some((v) => !v.trim())) {
      setError('Vui lòng nhập đủ 4 phương án A–D.'); return
    }
    if (form.loai_cau === 'TNDS' && form.y.some((y) => !y.noi_dung_y.trim())) {
      setError('Vui lòng nhập đủ nội dung 4 ý a–d.'); return
    }
    setAnhDan(null) // đã dùng ảnh xong (nếu có) — không lưu ảnh vào dữ liệu
    setDangTao(true)
    try {
      const body = {
        dang_id: Number(form.dang_id), loai_cau: form.loai_cau, do_kho: form.do_kho,
        de_bai: form.de_bai,
        meta_nhap: form.loai_cau === 'TN4PA' ? { phuong_an: form.phuong_an }
          : form.loai_cau === 'TNDS' ? { y: form.y } : {},
        cau_truc_buoc: capCauTrucBuoc(),
      }
      const ket = await api.taoBuocGoiY(body)
      setNhap(ket)
    } catch (e) {
      setError(e.message)
    } finally {
      setDangTao(false)
    }
  }

  function huyXemTruoc() {
    setNhap(null)
  }

  async function luu() {
    setError('')
    if (nhap.cau.loai_cau === 'TLN') {
      const err = kiemTraDapAnTLN(nhap.cau.meta?.dap_an_cuoi)
      if (err) { setError(err); return }
    }
    setDangLuu(true)
    try {
      await api.luuBuocGoiY({ ...nhap.cau, solution_steps: chuanHoaSteps(nhap.cau.solution_steps) })
      setNhap(null)
      setForm((f) => ({ ...f, de_bai: '', phuong_an: { A: '', B: '', C: '', D: '' },
        y: ['a', 'b', 'c', 'd'].map((k) => ({ ky_hieu: k, noi_dung_y: '' })) }))
      onLuuXong()
    } catch (e) {
      setError(e.message)
    } finally {
      setDangLuu(false)
    }
  }

  if (nhap) {
    return (
      <Card>
        <CardHeader title="Xem trước bản nháp AI vừa tạo"
          subtitle="Kiểm tra/sửa trước khi lưu — chưa có gì được ghi vào ngân hàng câu hỏi." />
        <CardBody className="flex flex-col gap-3">
          {nhap.canh_bao?.length > 0 && (
            <ul className="text-xs text-warning bg-warning-soft rounded-md px-3 py-2 list-disc pl-5">
              {nhap.canh_bao.map((w, i) => <li key={i}>{w}</li>)}
            </ul>
          )}
          {error && <p className="text-sm text-danger bg-danger-soft rounded-md px-3 py-2">{error}</p>}
          <ThanCauHoiForm
            bai={nhap.cau} setBai={(fn) => setNhap((n) => ({ ...n, cau: typeof fn === 'function' ? fn(n.cau) : fn }))}
            dangOptions={dangOptions}
            onLuu={luu} onDong={huyXemTruoc} dangLuu={dangLuu}
            nutLuuText="✅ Lưu câu hỏi (chờ duyệt)"
          />
        </CardBody>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader title="🎓 AI tạo bước và gợi ý"
        subtitle="Thầy/cô viết đề bài (và phương án/ý nếu có) — AI chỉ giải ra đáp án đúng, chia đúng số bước, viết đúng số gợi ý mỗi bước theo yêu cầu." />
      <CardBody className="grid lg:grid-cols-[1fr_18rem] gap-5">
        {/* Cột trái: form nhập */}
        <div className="flex flex-col gap-4">
          <div className="grid sm:grid-cols-3 gap-3">
            <Select
              label="Chuyên đề › Dạng"
              value={String(form.dang_id || '')}
              onChange={(e) => setForm((f) => ({ ...f, dang_id: e.target.value }))}
              options={dangOptions}
            />
            <Select
              label="Loại câu"
              value={form.loai_cau}
              onChange={(e) => doiLoaiCau(e.target.value)}
              options={[
                { value: 'TLN', label: 'Trả lời ngắn' },
                { value: 'TN4PA', label: 'Trắc nghiệm A–D' },
                { value: 'TNDS', label: 'Đúng/Sai 4 ý' },
              ]}
            />
            <Select
              label="Độ khó"
              value={form.do_kho}
              onChange={(e) => setForm((f) => ({ ...f, do_kho: e.target.value }))}
              options={[
                { value: 'de', label: 'Dễ' }, { value: 'tb', label: 'Trung bình' }, { value: 'kho', label: 'Khó' },
              ]}
            />
          </div>

          <ODanAnh
            anhDan={anhDan}
            onDanAnh={setAnhDan}
            onXoaAnh={() => setAnhDan(null)}
            onNhanDang={nhanDangTuAnh}
            dangDoc={dangDocAnh}
            loaiCau={form.loai_cau}
          />

          <TexField
            label="Đề bài — công thức đặt trong $...$ (bấm vào ô rồi chọn ký hiệu bên phải để chèn)"
            value={form.de_bai}
            onChange={(v) => setForm((f) => ({ ...f, de_bai: v }))}
            multiline
            registerActive={register}
            placeholder="VD: Một hộp có 5 bi đỏ, 3 bi xanh. Lấy ngẫu nhiên 2 bi. Tính xác suất lấy được 2 bi đỏ."
          />

          {form.loai_cau === 'TN4PA' && (
            <div className="grid sm:grid-cols-2 gap-3">
              {['A', 'B', 'C', 'D'].map((k) => (
                <TexField key={k} label={`Phương án ${k}`} value={form.phuong_an[k]}
                  onChange={(v) => setForm((f) => ({ ...f, phuong_an: { ...f.phuong_an, [k]: v } }))}
                  registerActive={register}
                />
              ))}
            </div>
          )}

          {form.loai_cau === 'TNDS' && (
            <div className="flex flex-col gap-2">
              {form.y.map((y, i) => (
                <TexField key={y.ky_hieu} label={`Ý ${y.ky_hieu})`} value={y.noi_dung_y}
                  registerActive={register}
                  onChange={(v) => setForm((f) => {
                    const yMoi = [...f.y]
                    yMoi[i] = { ...yMoi[i], noi_dung_y: v }
                    return { ...f, y: yMoi }
                  })}
                />
              ))}
            </div>
          )}

          <div className="rounded-lg bg-surface-2 px-4 py-3 flex flex-col gap-3">
            <p className="text-sm font-semibold text-ink">Cấu trúc bước & số gợi ý leo thang</p>
            {form.loai_cau !== 'TNDS' && (
              <Input label="Số bước" type="number" min={1} max={6} className="max-w-32"
                value={soBuoc} onChange={(e) => doiSoBuoc(e.target.value)} />
            )}
            <div className="flex gap-3 flex-wrap">
              {(form.loai_cau === 'TNDS' ? ['a', 'b', 'c', 'd'] : Array.from({ length: soBuoc }, (_, i) => i + 1))
                .map((nhan, i) => (
                  <Input key={i} type="number" min={1} max={8} className="w-28"
                    label={form.loai_cau === 'TNDS' ? `Số gợi ý ý ${nhan}` : `Số gợi ý bước ${nhan}`}
                    value={soGoiYList[i] ?? 2}
                    onChange={(e) => setSoGoiYList((gy) => {
                      const moi = [...gy]
                      moi[i] = e.target.value
                      return moi
                    })}
                  />
                ))}
            </div>
          </div>

          {error && <p className="text-sm text-danger bg-danger-soft rounded-md px-3 py-2">{error}</p>}
          <div>
            <Button onClick={tao} disabled={dangTao}>
              {dangTao ? 'AI đang giải và soạn gợi ý...' : '🤖 Tạo bước và gợi ý bằng AI'}
            </Button>
          </div>
        </div>

        {/* Cột phải: bảng công thức hỗ trợ nhập LaTeX */}
        <div className="sticky top-0 self-start max-h-screen overflow-y-auto">
          <BangCongThuc onChen={chen} />
        </div>
      </CardBody>
    </Card>
  )
}

export default function AISinhCauHoi() {
  const [danhMuc, setDanhMuc] = useState([])
  const [form, setForm] = useState({
    chuyen_de: '',
    dang_id: null,
    loai_cau: 'TLN',
    do_kho: 'tb',
    so_luong: 2,
  })
  const [dangSinh, setDangSinh] = useState(false)
  const [error, setError] = useState('')
  const [nhap, setNhap] = useState([])
  const [choDuyet, setChoDuyet] = useState([])
  const [sua, setSua] = useState(null)

  const dangList = useMemo(() => {
    const cd = danhMuc.find((c) => c.ten === form.chuyen_de)
    return cd ? cd.dang_list : []
  }, [danhMuc, form.chuyen_de])

  function taiChoDuyet() {
    api.listChoDuyet().then(setChoDuyet).catch(() => {})
  }
  useEffect(() => {
    api.getDanhMuc().then((dm) => {
      setDanhMuc(dm)
      if (dm.length > 0) setForm((f) => ({ ...f, chuyen_de: dm[0].ten }))
    }).catch(() => {})
    taiChoDuyet()
  }, [])

  async function sinh() {
    setDangSinh(true)
    setError('')
    try {
      const res = await api.genQuestions(form)
      setNhap(res)
      taiChoDuyet()
    } catch (e) {
      setError(e.message)
    } finally {
      setDangSinh(false)
    }
  }

  async function duyet(id, hanh_dong) {
    await api.duyetCau(id, hanh_dong)
    setNhap((ns) => ns.filter((n) => n.id !== id))
    taiChoDuyet()
  }

  async function suaXong(id) {
    setSua(null)
    try {
      const moi = await api.getProblem(id) // có meta + de_bai + loai_cau đã cập nhật
      setNhap((ns) => ns.map((n) => (n.id === id ? { ...n, ...moi } : n)))
    } catch { /* giữ nguyên nếu lỗi tải lại */ }
    taiChoDuyet()
  }

  return (
    <div className="flex flex-col gap-5">
      <TaoBuocGoiYPanel danhMuc={danhMuc} onLuuXong={taiChoDuyet} />

      <Card>
        <CardHeader title="Sinh câu hỏi bằng AI (hàng loạt)" subtitle="AI tự bịa đề — câu sinh ra ở trạng thái Chờ duyệt; chỉ Đã duyệt mới tới học sinh." />
        <CardBody className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3 items-end">
          <Select
            label="Chuyên đề"
            value={form.chuyen_de}
            onChange={(e) => setForm((f) => ({ ...f, chuyen_de: e.target.value, dang_id: null }))}
            options={danhMuc.map((c) => ({ value: c.ten, label: c.ten }))}
          />
          <Select
            label="Dạng (tùy chọn)"
            value={form.dang_id ?? ''}
            onChange={(e) => setForm((f) => ({ ...f, dang_id: e.target.value ? Number(e.target.value) : null }))}
            options={[
              { value: '', label: '— không chọn dạng —' },
              ...dangList.map((d) => ({ value: String(d.id), label: d.ten })),
            ]}
          />
          <Select
            label="Loại câu"
            value={form.loai_cau}
            onChange={(e) => setForm((f) => ({ ...f, loai_cau: e.target.value }))}
            options={[
              { value: 'TLN', label: 'Trả lời ngắn' },
              { value: 'TN4PA', label: 'Trắc nghiệm A–D' },
              { value: 'TNDS', label: 'Đúng/Sai 4 ý' },
            ]}
          />
          <Select
            label="Độ khó"
            value={form.do_kho}
            onChange={(e) => setForm((f) => ({ ...f, do_kho: e.target.value }))}
            options={[
              { value: 'de', label: 'Dễ (2 gợi ý)' },
              { value: 'tb', label: 'Trung bình (3 gợi ý)' },
              { value: 'kho', label: 'Khó (4 gợi ý)' },
            ]}
          />
          <Input
            label="Số lượng"
            type="number"
            min={1}
            max={10}
            value={form.so_luong}
            onChange={(e) => setForm((f) => ({ ...f, so_luong: Number(e.target.value) }))}
          />
          <div className="sm:col-span-4">
            <Button onClick={sinh} disabled={dangSinh}>
              {dangSinh ? 'Đang sinh...' : 'Sinh câu hỏi'}
            </Button>
          </div>
          {error && (
            <p className="sm:col-span-4 text-danger text-sm bg-danger-soft rounded-md px-3 py-2">
              {error}
            </p>
          )}
        </CardBody>
      </Card>

      {nhap.length > 0 && (
        <Card>
          <CardHeader title="Bản nháp vừa sinh" subtitle="Duyệt để đưa vào ngân hàng, hoặc loại." />
          <CardBody className="flex flex-col gap-3">
            {nhap.map((c) => (
              <div key={c.id} className="rounded-md border border-border px-3 py-3 flex flex-col gap-2">
                <div className="flex items-center gap-2">
                  <Badge tone="primary">{c.loai_cau}</Badge>
                  <Badge tone="neutral">{c.do_kho}</Badge>
                  {c.canh_bao.length === 0 ? (
                    <Badge tone="success">Hợp lệ</Badge>
                  ) : (
                    <Badge tone="warning">{c.canh_bao.length} cảnh báo</Badge>
                  )}
                </div>
                <NoiDungCauHoi c={c} />
                {c.canh_bao?.length > 0 && (
                  <ul className="text-xs text-warning list-disc pl-5">
                    {c.canh_bao.map((w, i) => (
                      <li key={i}>{w}</li>
                    ))}
                  </ul>
                )}
                <div className="flex gap-2">
                  <Button size="sm" variant="success" onClick={() => duyet(c.id, 'duyet')}>
                    Duyệt
                  </Button>
                  <Button size="sm" onClick={() => setSua(c.id)}>
                    Sửa
                  </Button>
                  <Button size="sm" variant="secondary" onClick={() => duyet(c.id, 'loai')}>
                    Loại
                  </Button>
                </div>
              </div>
            ))}
          </CardBody>
        </Card>
      )}

      <Card>
        <CardHeader title="Hàng đợi chờ duyệt" subtitle={`${choDuyet.length} câu đang chờ`} />
        <CardBody className="flex flex-col gap-2">
          {choDuyet.length === 0 ? (
            <p className="text-sm text-muted">Không còn câu nào chờ duyệt.</p>
          ) : (
            choDuyet.map((c) => (
              <div key={c.id} className="flex items-center justify-between rounded-md border border-border px-3 py-2">
                <span className="text-sm text-ink truncate mr-2">
                  <Badge tone="primary">{c.loai_cau}</Badge>{' '}
                  <b className="text-primary">{c.chuyen_de}</b>
                  {c.dang_ten ? <span className="text-muted"> › {c.dang_ten}</span> : null}
                </span>
                <div className="flex gap-2 shrink-0">
                  <Button size="sm" variant="success" onClick={() => duyet(c.id, 'duyet')}>
                    Duyệt
                  </Button>
                  <Button size="sm" onClick={() => setSua(c.id)}>
                    Sửa
                  </Button>
                  <Button size="sm" variant="secondary" onClick={() => duyet(c.id, 'loai')}>
                    Loại
                  </Button>
                </div>
              </div>
            ))
          )}
        </CardBody>
      </Card>

      {sua && (
        <SuaCauHoi
          id={sua}
          danhMuc={danhMuc}
          onDong={() => setSua(null)}
          onLuuXong={() => suaXong(sua)}
        />
      )}
    </div>
  )
}
