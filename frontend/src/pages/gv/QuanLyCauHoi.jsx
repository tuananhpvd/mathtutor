import { useCallback, useEffect, useRef, useState } from 'react'
import { api } from '../../api'
import { Badge, Button, Card, CardBody, Input, Select, Table, useConfirm } from '../../components/ui'
import Formula from '../../components/Formula'
import ImportCauHoiDialog from '../../components/gv/ImportCauHoiDialog'
import VeDoThiDialog from '../../components/gv/VeDoThiDialog'
import VeBBTDialog from '../../components/gv/VeBBTDialog'
import { CotThoiGian } from '../../components/ThoiGianPhanCach'

const NHAN_LOAI = { TN4PA: 'Trắc nghiệm ABCD', TNDS: 'Đúng/Sai 4 ý', TLN: 'Trả lời ngắn' }

export function kiemTraDapAnTLN(v) {
  const val = String(v ?? '').trim()
  if (!val) return 'Đáp án cuối không được để trống'
  if (val.length > 4) return 'Đáp án cuối tối đa 4 ký tự (gồm dấu - và dấu ,)'
  if (!/^-?\d+([.,]\d+)?$/.test(val)) return 'Đáp án cuối phải là số nguyên hoặc số thập phân (ví dụ: 3, -2, 1,5)'
  return null
}
const NHAN_KHO = { de: 'Dễ', tb: 'Trung bình', kho: 'Khó' }
const NHAN_NGUON = { gv_nhap: 'GV', ai_sinh: 'AI' }

function dinhDangNgay(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  if (isNaN(d)) return '—'
  return d.toLocaleString('vi-VN', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

function renderTex(text) {
  return String(text || '')
    .split(/(\$[^$]+\$)/g)
    .map((p, i) =>
      p.startsWith('$') ? <Formula key={i} latex={p.slice(1, -1)} /> : <span key={i}>{p}</span>
    )
}

// ---- Bảng công thức: chèn LaTeX vào ô đang focus ----
const NHOM_CONG_THUC = [
  {
    ten: 'Hay dùng',
    keys: [
      { label: '$\\cdots$', text: '$…$', snippet: '$ $', back: 1 },
      { label: 'x^{n}', snippet: '^{}', back: 1 },
      { label: 'x^{2}', snippet: '^2', back: 0 },
      { label: '\\dfrac{a}{b}', snippet: '\\dfrac{}{}', back: 3 },
      { label: '\\sqrt{x}', snippet: '\\sqrt{}', back: 1 },
      { label: '\\sqrt[3]{x}', snippet: '\\sqrt[3]{}', back: 1 },
      { label: '(\\;)', snippet: '()', back: 1 },
      { label: "y'", snippet: "y'", back: 0 },
    ],
  },
  {
    ten: 'Giải tích',
    keys: [
      { label: '\\int f\\,dx', snippet: '\\int  \\, dx', back: 5 },
      { label: '\\int_a^b f\\,dx', snippet: '\\int_{}^{}  \\, dx', back: 11 },
      { label: '\\lim_{x \\to a}', snippet: '\\lim_{ \\to } ', back: 6 },
      { label: "f'(x)", snippet: "f'()", back: 1 },
      { label: "f''(x)", snippet: "f''()", back: 1 },
      { label: '\\dfrac{d}{dx}\\!f', snippet: '\\dfrac{d}{dx}()', back: 1 },
      { label: 'F(x)', snippet: 'F()', back: 1 },
    ],
  },
  {
    ten: 'Ký hiệu',
    keys: [
      { label: '\\le', snippet: '\\le ', back: 0 },
      { label: '\\ge', snippet: '\\ge ', back: 0 },
      { label: '\\ne', snippet: '\\ne ', back: 0 },
      { label: '\\infty', snippet: '\\infty ', back: 0 },
      { label: '\\pm', snippet: '\\pm ', back: 0 },
      { label: '\\pi', snippet: '\\pi ', back: 0 },
      { label: '\\to', snippet: '\\to ', back: 0 },
      { label: '\\cdot', snippet: '\\cdot ', back: 0 },
      { label: '\\approx', snippet: '\\approx ', back: 0 },
      { label: '90^\\circ', snippet: '^\\circ ', back: 0 },
    ],
  },
  {
    ten: 'Hàm sơ cấp',
    keys: [
      { label: '\\sin x', snippet: '\\sin ', back: 0 },
      { label: '\\cos x', snippet: '\\cos ', back: 0 },
      { label: '\\tan x', snippet: '\\tan ', back: 0 },
      { label: '\\cot x', snippet: '\\cot ', back: 0 },
      { label: '\\ln x', snippet: '\\ln ', back: 0 },
      { label: '\\log_a x', snippet: '\\log_{}', back: 1 },
      { label: 'e^{x}', snippet: 'e^{}', back: 1 },
      { label: '|x|', snippet: '||', back: 1 },
    ],
  },
  {
    ten: 'Tập hợp - Logic',
    keys: [
      { label: '\\in', snippet: '\\in ', back: 0 },
      { label: '\\notin', snippet: '\\notin ', back: 0 },
      { label: '\\subset', snippet: '\\subset ', back: 0 },
      { label: '\\emptyset', snippet: '\\emptyset ', back: 0 },
      { label: '\\cap', snippet: '\\cap ', back: 0 },
      { label: '\\cup', snippet: '\\cup ', back: 0 },
      { label: '\\forall', snippet: '\\forall ', back: 0 },
      { label: '\\exists', snippet: '\\exists ', back: 0 },
    ],
  },
  {
    ten: 'Tổ hợp - Xác suất',
    keys: [
      { label: 'C_n^k', snippet: 'C_{}^{}', back: 4 },
      { label: 'A_n^k', snippet: 'A_{}^{}', back: 4 },
      { label: 'n!', snippet: '!', back: 0 },
      { label: 'P(A)', snippet: 'P()', back: 1 },
      { label: '\\mid', snippet: ' \\mid ', back: 0 },
      { label: '\\sum_{i}^{n}', snippet: '\\sum_{}^{}', back: 4 },
    ],
  },
]

export function BangCongThuc({ onChen }) {
  return (
    <div className="rounded-md border border-border bg-surface-2 p-2.5 flex flex-col gap-3">
      <p className="text-[11px] text-muted">
        Bấm vào ô cần sửa (đề/gợi ý/…) rồi chọn ký hiệu để chèn. Công thức phải nằm trong <b>$...$</b>.
      </p>
      {NHOM_CONG_THUC.map((g) => (
        <div key={g.ten}>
          <p className="text-[10px] text-muted uppercase tracking-wide mb-1.5">{g.ten}</p>
          <div className="flex flex-wrap gap-1.5">
            {g.keys.map((k, i) => (
              <button
                key={i}
                type="button"
                onMouseDown={(e) => e.preventDefault()}
                onClick={() => onChen(k.snippet, k.back)}
                title={k.snippet}
                className="rounded border border-border bg-surface min-w-[2.5rem] px-2 py-1.5 text-center
                  text-ink hover:bg-primary-soft hover:border-primary transition-colors"
              >
                {k.text
                  ? <span className="text-xs font-mono font-bold">{k.text}</span>
                  : <Formula latex={k.label} />}
              </button>
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}

// ---- Bảng tra cú pháp SymPy cho ô "Biểu thức kết quả" ----
const NHOM_SYMPY = [
  {
    ten: 'Cơ bản',
    rows: [
      { toan: '$x^2$, $x^n$', sympy: 'x**2, x**n', ghi: 'Lũy thừa dùng **' },
      { toan: '$x \\cdot y$', sympy: 'x*y', ghi: 'Luôn ghi dấu * khi nhân' },
      { toan: '$2x$', sympy: '2*x', ghi: 'Phải có *, không viết 2x' },
      { toan: '$\\dfrac{a}{b}$', sympy: 'a/b', ghi: 'Phép chia' },
      { toan: '$\\dfrac{x+1}{x-2}$', sympy: '(x+1)/(x-2)', ghi: 'Nhớ bọc ngoặc' },
    ],
  },
  {
    ten: 'Căn & lũy thừa',
    rows: [
      { toan: '$\\sqrt{x}$', sympy: 'sqrt(x)', ghi: 'Căn bậc hai' },
      { toan: '$\\sqrt[3]{x}$', sympy: 'x**(Rational(1,3))', ghi: 'Hoặc cbrt(x)' },
      { toan: '$\\sqrt[n]{x}$', sympy: 'x**(1/n)', ghi: 'Căn bậc n' },
      { toan: '$e^x$', sympy: 'exp(x)', ghi: 'Hàm mũ cơ số e' },
      { toan: '$a^x$', sympy: 'a**x', ghi: 'Mũ cơ số bất kỳ' },
    ],
  },
  {
    ten: 'Mũ & log',
    rows: [
      { toan: '$\\ln x$', sympy: 'log(x)', ghi: 'log() là ln (cơ số e)' },
      { toan: '$\\log_{10} x$', sympy: 'log(x, 10)', ghi: 'Log cơ số 10' },
      { toan: '$\\log_a x$', sympy: 'log(x, a)', ghi: 'Log cơ số a' },
    ],
  },
  {
    ten: 'Lượng giác',
    rows: [
      { toan: '$\\sin x,\\ \\cos x$', sympy: 'sin(x), cos(x)', ghi: '' },
      { toan: '$\\tan x,\\ \\cot x$', sympy: 'tan(x), cot(x)', ghi: '' },
      { toan: '$\\sin^2 x$', sympy: 'sin(x)**2', ghi: 'Không viết sin^2 x' },
      { toan: '$\\arcsin x$', sympy: 'asin(x)', ghi: 'acos, atan tương tự' },
    ],
  },
  {
    ten: 'Hằng số & ký hiệu',
    rows: [
      { toan: '$\\pi$', sympy: 'pi', ghi: 'Số pi' },
      { toan: '$e$', sympy: 'E', ghi: 'Cơ số tự nhiên (E hoa)' },
      { toan: '$\\infty$', sympy: 'oo', ghi: 'Vô cực (hai chữ o)' },
      { toan: '$|x|$', sympy: 'Abs(x)', ghi: 'Giá trị tuyệt đối' },
      { toan: '$\\dfrac{1}{2}$', sympy: 'Rational(1,2)', ghi: 'Phân số chính xác' },
    ],
  },
  {
    ten: 'Giải tích',
    rows: [
      { toan: "$f'(x)$", sympy: 'diff(f, x)', ghi: 'Đạo hàm theo x' },
      { toan: "$f''(x)$", sympy: 'diff(f, x, 2)', ghi: 'Đạo hàm cấp 2' },
      { toan: '$\\int f\\,dx$', sympy: 'integrate(f, x)', ghi: 'Nguyên hàm' },
      { toan: '$\\int_a^b f\\,dx$', sympy: 'integrate(f,(x,a,b))', ghi: 'Tích phân xác định' },
      { toan: '$\\lim_{x\\to a} f$', sympy: 'limit(f, x, a)', ghi: 'Giới hạn' },
    ],
  },
]

function BangCuPhapSymPy() {
  const [mo, setMo] = useState(true)
  return (
    <div className="rounded-md border border-border bg-surface-2 p-2.5 flex flex-col gap-2">
      <button
        type="button"
        onClick={() => setMo((m) => !m)}
        className="flex items-center justify-between text-left"
      >
        <span className="text-xs font-semibold text-ink">Cú pháp SymPy (ô "Biểu thức kết quả")</span>
        <span className="text-muted text-xs">{mo ? '▲' : '▼'}</span>
      </button>
      {mo && (
        <>
          <p className="text-[11px] text-muted">
            Ô "Biểu thức kết quả" để máy chấm (CAS), <b>KHÔNG bọc $</b> và <b>không phải LaTeX</b>.
            Đây là cú pháp Python/SymPy của các biểu thức hay gặp.
          </p>
          {NHOM_SYMPY.map((g) => (
            <div key={g.ten}>
              <p className="text-[10px] text-muted uppercase tracking-wide mb-1">{g.ten}</p>
              <div className="flex flex-col gap-1">
                {g.rows.map((r, i) => (
                  <div key={i} className="rounded border border-border bg-surface px-2 py-1.5 text-[12px]">
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-ink">{renderTex(r.toan)}</span>
                      <code className="font-mono text-[11px] text-primary bg-primary-soft rounded px-1.5 py-0.5 whitespace-nowrap">
                        {r.sympy}
                      </code>
                    </div>
                    {r.ghi && <p className="text-[10px] text-muted mt-0.5">{r.ghi}</p>}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </>
      )}
    </div>
  )
}

// Ô nhập có xem trước công thức + đăng ký làm ô đang focus để chèn ký hiệu.
export function TexField({ value, onChange, label, multiline, registerActive, placeholder }) {
  const ref = useRef(null)
  // Bug đã sửa: focusSelf chỉ chạy 1 lần khi Focus (không chạy lại khi gõ chữ), nên closure
  // đăng ký từng "chốt cứng" value/onChange tại thời điểm focus. Gõ thêm chữ rồi mới bấm chèn
  // công thức sẽ đọc lại giá trị CŨ đó, xóa mất toàn bộ chữ vừa gõ. Dùng ref để luôn đọc giá
  // trị MỚI NHẤT tại thời điểm bấm chèn, bất kể closure được tạo từ lúc nào.
  const valueRef = useRef(value)
  const onChangeRef = useRef(onChange)
  useEffect(() => {
    valueRef.current = value
    onChangeRef.current = onChange
  })

  function focusSelf() {
    registerActive((snippet, back) => {
      const el = ref.current
      const v = valueRef.current || ''
      const start = el?.selectionStart ?? v.length
      const end = el?.selectionEnd ?? v.length
      const next = v.slice(0, start) + snippet + v.slice(end)
      onChangeRef.current(next)
      const caret = start + snippet.length - (back || 0)
      setTimeout(() => {
        if (ref.current) {
          ref.current.focus()
          ref.current.setSelectionRange(caret, caret)
        }
      }, 0)
    })
  }
  const common = {
    ref,
    value: value || '',
    onChange: (e) => onChange(e.target.value),
    onFocus: focusSelf,
    placeholder,
    className:
      'w-full rounded-md border border-border bg-surface px-2.5 py-1.5 text-sm text-ink ' +
      'focus:border-primary focus:outline-none',
  }
  return (
    <div>
      {label && <p className="text-xs text-muted mb-1">{label}</p>}
      {multiline ? <textarea rows={2} {...common} /> : <input {...common} />}
      {value && (
        <p className="text-[13px] text-ink/80 mt-1 px-2.5 py-1.5 rounded-lg bg-primary-soft border border-primary/30">
          {renderTex(value)}
        </p>
      )}
    </div>
  )
}

// Cấu trúc mặc định cho từng loại câu khi tạo mới.
function templateTheoLoai(loai) {
  if (loai === 'TN4PA') {
    return {
      meta: { phuong_an: { A: '', B: '', C: '', D: '' }, dap_an_dung: 'A', bat_buoc_suy_luan: false },
      solution_steps: [
        { thu_tu: 1, pham_vi: 'ca_bai', mo_ta: '', bieu_thuc_ket_qua: '', danh_sach_goi_y: [''] },
      ],
    }
  }
  if (loai === 'TNDS') {
    return {
      meta: {
        y: ['a', 'b', 'c', 'd'].map((k) => ({
          ky_hieu: k, noi_dung_y: '', dap_an: 'Dung', bat_buoc_suy_luan: false,
        })),
      },
      solution_steps: ['a', 'b', 'c', 'd'].map((k) => ({
        thu_tu: 1, pham_vi: k, mo_ta: '', bieu_thuc_ket_qua: '', danh_sach_goi_y: [''],
      })),
    }
  }
  // TLN
  return {
    meta: { dap_an_cuoi: '', quy_tac_lam_tron: null, don_vi: null },
    solution_steps: [
      { thu_tu: 1, pham_vi: 'ca_bai', mo_ta: '', bieu_thuc_ket_qua: '', danh_sach_goi_y: [''] },
    ],
  }
}

// Thân form chung cho cả Sửa và Tạo câu hỏi.
export function ThanCauHoiForm({ bai, setBai, dangOptions, choChonLoai, onLuu, onDong, dangLuu, nutLuuText }) {
  const activeInsert = useRef(null)
  const register = (fn) => { activeInsert.current = fn }
  const chen = (s, b) => activeInsert.current?.(s, b)

  const [dangUpload, setDangUpload] = useState(false)
  const [loiUpload, setLoiUpload] = useState('')
  // Uploader dùng chung cho cả chọn file lẫn dán clipboard. Xóa hinh_spec cũ (nếu có) vì ảnh
  // mới không còn phải là đồ thị đã vẽ — tránh nút "Vẽ lại" áp nhầm cho ảnh không liên quan.
  const taiLenFile = useCallback(async (file) => {
    if (!file) return
    setLoiUpload('')
    setDangUpload(true)
    try {
      const { url } = await api.uploadHinh(file)
      setBai((b) => {
        const meta = { ...b.meta }
        delete meta.hinh_spec
        return { ...b, hinh_anh: url, meta }
      })
    } catch (err) {
      setLoiUpload(err.message)
    } finally {
      setDangUpload(false)
    }
  }, [setBai])
  function chonHinh(e) {
    const file = e.target.files?.[0]
    e.target.value = ''
    taiLenFile(file)
  }
  // Dán ảnh chụp màn hình bằng Ctrl+V (Win+Shift+S): bắt paste cấp document khi form mở.
  // Chỉ xử lý khi clipboard có ảnh → dán chữ vào ô đề bài vẫn hoạt động bình thường.
  useEffect(() => {
    function danAnh(e) {
      const item = [...(e.clipboardData?.items || [])].find((i) => i.type.startsWith('image/'))
      if (!item) return
      e.preventDefault()
      const file = item.getAsFile()
      if (file) taiLenFile(file)
    }
    document.addEventListener('paste', danAnh)
    return () => document.removeEventListener('paste', danAnh)
  }, [taiLenFile])

  // Vẽ đồ thị (GĐ3A) / bảng biến thiên (GĐ3B) từ hàm số — CAS tự phân tích, GV chỉ nhập f(x).
  const [veDoThiMo, setVeDoThiMo] = useState(false)
  const [veBBTMo, setVeBBTMo] = useState(false)
  function xongVeHinh(url, spec) {
    setBai((b) => ({ ...b, hinh_anh: url, meta: { ...b.meta, hinh_spec: spec } }))
    setVeDoThiMo(false)
    setVeBBTMo(false)
  }

  function doiLoai(loai) {
    const t = templateTheoLoai(loai)
    setBai((b) => ({ ...b, loai_cau: loai, meta: t.meta, solution_steps: t.solution_steps }))
  }

  function setMeta(patch) {
    setBai((b) => ({ ...b, meta: { ...b.meta, ...patch } }))
  }
  function setY(idx, patch) {
    setBai((b) => {
      const y = [...(b.meta.y || [])]
      y[idx] = { ...y[idx], ...patch }
      return { ...b, meta: { ...b.meta, y } }
    })
  }
  function setStep(idx, patch) {
    setBai((b) => {
      const steps = [...b.solution_steps]
      steps[idx] = { ...steps[idx], ...patch }
      return { ...b, solution_steps: steps }
    })
  }
  function setGoiY(si, gi, val) {
    setBai((b) => {
      const steps = [...b.solution_steps]
      const gs = [...(steps[si].danh_sach_goi_y || [])]
      gs[gi] = val
      steps[si] = { ...steps[si], danh_sach_goi_y: gs }
      return { ...b, solution_steps: steps }
    })
  }
  function themGoiY(si) {
    setBai((b) => {
      const steps = [...b.solution_steps]
      steps[si] = { ...steps[si], danh_sach_goi_y: [...(steps[si].danh_sach_goi_y || []), ''] }
      return { ...b, solution_steps: steps }
    })
  }
  function xoaGoiY(si, gi) {
    setBai((b) => {
      const steps = [...b.solution_steps]
      steps[si] = {
        ...steps[si],
        danh_sach_goi_y: steps[si].danh_sach_goi_y.filter((_, i) => i !== gi),
      }
      return { ...b, solution_steps: steps }
    })
  }
  function themBuoc() {
    setBai((b) => ({
      ...b,
      solution_steps: [
        ...b.solution_steps,
        { thu_tu: b.solution_steps.length + 1, pham_vi: 'ca_bai', mo_ta: '', bieu_thuc_ket_qua: '', danh_sach_goi_y: [''] },
      ],
    }))
  }
  function xoaBuoc(si) {
    setBai((b) => ({ ...b, solution_steps: b.solution_steps.filter((_, i) => i !== si) }))
  }

  return (
    <div className="grid grid-cols-[1fr_18rem] gap-5">
      {/* Cột trái: form */}
            <div className="flex flex-col gap-4">
              <div className="grid sm:grid-cols-3 gap-3">
                {choChonLoai && (
                  <Select
                    label="Loại câu hỏi"
                    value={bai.loai_cau}
                    onChange={(e) => doiLoai(e.target.value)}
                    options={[
                      { value: 'TN4PA', label: NHAN_LOAI.TN4PA },
                      { value: 'TNDS', label: NHAN_LOAI.TNDS },
                      { value: 'TLN', label: NHAN_LOAI.TLN },
                    ]}
                  />
                )}
                <Select
                  label="Chuyên đề › Dạng"
                  value={String(bai.dang_id || '')}
                  onChange={(e) => setBai((b) => ({ ...b, dang_id: e.target.value || null }))}
                  options={dangOptions}
                />
                <Select
                  label="Mức độ"
                  value={bai.do_kho}
                  onChange={(e) => setBai((b) => ({ ...b, do_kho: e.target.value }))}
                  options={[
                    { value: 'de', label: 'Dễ' },
                    { value: 'tb', label: 'Trung bình' },
                    { value: 'kho', label: 'Khó' },
                  ]}
                />
              </div>

              <TexField
                label={`Đề bài (loại: ${NHAN_LOAI[bai.loai_cau] || bai.loai_cau})`}
                value={bai.de_bai}
                onChange={(v) => setBai((b) => ({ ...b, de_bai: v }))}
                multiline
                registerActive={register}
              />

              {/* Hình minh họa (tùy chọn) — hiện ở cột phải màn HS làm bài */}
              <div className="flex flex-col gap-1.5">
                <p className="text-xs text-muted">
                  Hình minh họa (không bắt buộc — PNG/JPG/WebP, tối đa 3MB)
                </p>
                {bai.hinh_anh ? (
                  <div className="flex items-start gap-3">
                    <img
                      src={bai.hinh_anh}
                      alt="Hình minh họa"
                      className="max-h-40 max-w-full rounded-md border border-border"
                    />
                    <div className="flex flex-col gap-1.5">
                      <Button
                        type="button"
                        size="sm"
                        variant="secondary"
                        onClick={() => setBai((b) => {
                          const meta = { ...b.meta }
                          delete meta.hinh_spec
                          return { ...b, hinh_anh: null, meta }
                        })}
                      >
                        Gỡ ảnh
                      </Button>
                      {bai.meta?.hinh_spec?.loai === 'do_thi' && (
                        <Button type="button" size="sm" variant="secondary" onClick={() => setVeDoThiMo(true)}>
                          📈 Vẽ lại
                        </Button>
                      )}
                      {bai.meta?.hinh_spec?.loai === 'bang_bien_thien' && (
                        <Button type="button" size="sm" variant="secondary" onClick={() => setVeBBTMo(true)}>
                          📋 Vẽ lại
                        </Button>
                      )}
                    </div>
                  </div>
                ) : (
                  <div className="flex flex-col gap-2">
                    <div className="flex flex-wrap items-center gap-3">
                      <label className="inline-flex w-fit cursor-pointer items-center gap-2 rounded-md border border-dashed border-border px-3 py-2 text-sm text-primary hover:border-primary">
                        <input
                          type="file"
                          accept="image/png,image/jpeg,image/webp"
                          className="hidden"
                          onChange={chonHinh}
                          disabled={dangUpload}
                        />
                        {dangUpload ? 'Đang tải ảnh...' : '＋ Chọn ảnh minh họa'}
                      </label>
                      <span className="text-xs text-muted">
                        hoặc chụp màn hình rồi <b>Ctrl&nbsp;+&nbsp;V</b> để dán
                      </span>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      <Button type="button" size="sm" variant="secondary" onClick={() => setVeDoThiMo(true)}>
                        📈 Vẽ đồ thị từ hàm số
                      </Button>
                      <Button type="button" size="sm" variant="secondary" onClick={() => setVeBBTMo(true)}>
                        📋 Vẽ bảng biến thiên
                      </Button>
                    </div>
                  </div>
                )}
                {loiUpload && <p className="text-xs text-danger">{loiUpload}</p>}
                {veDoThiMo && (
                  <VeDoThiDialog
                    initialSpec={bai.meta?.hinh_spec?.loai === 'do_thi' ? bai.meta.hinh_spec : null}
                    onDong={() => setVeDoThiMo(false)}
                    onXongHinh={xongVeHinh}
                  />
                )}
                {veBBTMo && (
                  <VeBBTDialog
                    initialSpec={bai.meta?.hinh_spec?.loai === 'bang_bien_thien' ? bai.meta.hinh_spec : null}
                    onDong={() => setVeBBTMo(false)}
                    onXongHinh={xongVeHinh}
                  />
                )}
              </div>

              {/* Đáp án theo loại câu */}
              {bai.loai_cau === 'TN4PA' && bai.meta?.phuong_an && (
                <div className="flex flex-col gap-2">
                  <p className="text-xs text-muted">Phương án & đáp án đúng</p>
                  {['A', 'B', 'C', 'D'].map((k) => (
                    <div key={k} className="flex items-center gap-2">
                      <label className="flex items-center gap-1 text-sm font-bold w-8">
                        <input
                          type="radio"
                          name="dapan"
                          checked={bai.meta.dap_an_dung === k}
                          onChange={() => setMeta({ dap_an_dung: k })}
                        />
                        {k}
                      </label>
                      <div className="flex-1">
                        <TexField
                          value={bai.meta.phuong_an[k]}
                          onChange={(v) => setMeta({ phuong_an: { ...bai.meta.phuong_an, [k]: v } })}
                          registerActive={register}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {bai.loai_cau === 'TN4PA' && (
                <div className="rounded-md border border-border bg-surface-2 px-3 py-2.5">
                  <Select
                    label="Trước khi chọn đáp án, học sinh:"
                    value={bai.meta?.bat_buoc_suy_luan ? 'co' : 'khong'}
                    onChange={(e) => setMeta({ bat_buoc_suy_luan: e.target.value === 'co' })}
                    options={[
                      { value: 'khong', label: 'Được chọn đáp án ngay' },
                      { value: 'co', label: 'Phải làm đúng tối thiểu 1 bước suy luận' },
                    ]}
                  />
                  <p className="text-[11px] text-muted mt-1">
                    Nếu bắt buộc suy luận: học sinh phải nhập đúng kết quả của bước (máy chấm bằng
                    CAS) thì nút A/B/C/D mới mở. Cần điền "Biểu thức kết quả" ở bước bên dưới.
                  </p>
                </div>
              )}

              {bai.loai_cau === 'TNDS' && bai.meta?.y && (
                <div className="flex flex-col gap-2">
                  <p className="text-xs text-muted">4 mệnh đề (chọn Đúng/Sai + cấu hình suy luận từng ý)</p>
                  {bai.meta.y.map((item, idx) => (
                    <div key={item.ky_hieu} className="rounded-md border border-border p-2.5 flex flex-col gap-2">
                      <div className="flex items-start gap-2">
                        <span className="text-sm font-bold w-5 pt-2">{item.ky_hieu})</span>
                        <div className="flex-1">
                          <TexField
                            value={item.noi_dung_y}
                            onChange={(v) => setY(idx, { noi_dung_y: v })}
                            registerActive={register}
                          />
                        </div>
                        <Select
                          className="w-24"
                          value={item.dap_an}
                          onChange={(e) => setY(idx, { dap_an: e.target.value })}
                          options={[
                            { value: 'Dung', label: 'Đúng' },
                            { value: 'Sai', label: 'Sai' },
                          ]}
                        />
                      </div>
                      <label className="flex items-center gap-2 text-xs text-ink pl-5">
                        <input
                          type="checkbox"
                          checked={!!item.bat_buoc_suy_luan}
                          onChange={(e) => setY(idx, { bat_buoc_suy_luan: e.target.checked })}
                        />
                        Bắt buộc suy luận (nhập biểu thức, CAS chấm) trước khi chốt Đúng/Sai —
                        cần điền "Biểu thức kết quả" ở bước ý {item.ky_hieu} bên dưới.
                      </label>
                    </div>
                  ))}
                </div>
              )}

              {bai.loai_cau === 'TLN' && (
                <div>
                  <Input
                    label="Đáp án cuối (để máy đối chiếu)"
                    value={bai.meta?.dap_an_cuoi ?? ''}
                    onChange={(e) => setMeta({ dap_an_cuoi: e.target.value })}
                  />
                  <p className="text-[11px] text-muted mt-1">
                    Số nguyên hoặc thập phân, tối đa 4 ký tự (ví dụ: <code>3</code>, <code>-2</code>, <code>1,5</code>)
                  </p>
                </div>
              )}

              {/* Các bước lời giải */}
              <div className="flex flex-col gap-3">
                <div className="flex items-center justify-between">
                  <p className="text-xs text-muted">Các bước & gợi ý</p>
                  <Button size="sm" variant="secondary" onClick={themBuoc}>+ Thêm bước</Button>
                </div>
                {bai.solution_steps.map((s, si) => (
                  <div key={si} className="rounded-md border border-border p-3 flex flex-col gap-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-primary">
                        Bước {s.thu_tu}{s.pham_vi && s.pham_vi !== 'ca_bai' ? ` · ý ${s.pham_vi}` : ''}
                      </span>
                      <button onClick={() => xoaBuoc(si)} className="text-danger text-xs hover:underline">
                        Xóa bước
                      </button>
                    </div>
                    <TexField
                      label="Mô tả bước"
                      value={s.mo_ta}
                      onChange={(v) => setStep(si, { mo_ta: v })}
                      registerActive={register}
                    />
                    <div>
                      <p className="text-xs text-muted mb-1">Biểu thức kết quả (cú pháp SymPy — KHÔNG bọc $)</p>
                      <input
                        value={s.bieu_thuc_ket_qua || ''}
                        onChange={(e) => setStep(si, { bieu_thuc_ket_qua: e.target.value })}
                        placeholder="vd: 3*x**2 - 6*x"
                        className="w-full rounded-md border border-border bg-surface px-2.5 py-1.5 text-sm font-mono focus:border-primary focus:outline-none"
                      />
                    </div>
                    <div className="flex flex-col gap-1.5">
                      <div className="flex items-center justify-between">
                        <p className="text-xs text-muted">Gợi ý (leo thang)</p>
                        <button onClick={() => themGoiY(si)} className="text-primary text-xs hover:underline">
                          + Gợi ý
                        </button>
                      </div>
                      {(s.danh_sach_goi_y || []).map((g, gi) => (
                        <div key={gi} className="flex items-start gap-2">
                          <span className="text-xs text-muted pt-2 w-4">{gi + 1}.</span>
                          <div className="flex-1">
                            <TexField
                              value={g}
                              onChange={(v) => setGoiY(si, gi, v)}
                              multiline
                              registerActive={register}
                            />
                          </div>
                          <button
                            onClick={() => xoaGoiY(si, gi)}
                            className="text-danger text-xs hover:underline pt-2"
                          >
                            ✕
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>

              <div className="flex gap-2 pt-1">
                <Button onClick={onLuu} disabled={dangLuu}>
                  {dangLuu ? 'Đang lưu...' : (nutLuuText || 'Lưu thay đổi')}
                </Button>
                <Button variant="secondary" onClick={onDong}>Hủy</Button>
              </div>
            </div>

            {/* Cột phải: bảng công thức + cú pháp SymPy (sticky) */}
            <div className="sticky top-0 self-start max-h-screen overflow-y-auto flex flex-col gap-3 pb-4">
              <BangCongThuc onChen={chen} />
              <BangCuPhapSymPy />
            </div>
    </div>
  )
}

// Vỏ modal chung (overlay phải) cho Sửa / Tạo.
function KhungModal({ tieu_de, error, children, onDong }) {
  return (
    <div className="fixed inset-0 z-20 bg-black/30 flex justify-end">
      <div className="w-2/3 min-w-[620px] bg-surface h-full overflow-y-auto p-6 shadow-[var(--shadow-pop)]">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-ink">{tieu_de}</h3>
          <button onClick={onDong} className="text-muted hover:text-ink text-lg">✕</button>
        </div>
        {error && <p className="text-danger text-sm bg-danger-soft rounded-md px-3 py-2 mb-3">{error}</p>}
        {children}
      </div>
    </div>
  )
}

// Tập hợp danh sách dạng → options (dùng chung).
export function dungDangOptions(danhMuc) {
  return [
    { value: '', label: '— Chưa gán dạng —' },
    ...danhMuc.flatMap((cd) =>
      cd.dang_list.map((d) => ({ value: String(d.id), label: `${cd.ten} › ${d.ten}`, cd: cd.ten }))
    ),
  ]
}

// Chuẩn hóa payload các bước.
export function chuanHoaSteps(steps) {
  return steps.map((s) => ({
    thu_tu: s.thu_tu,
    pham_vi: s.pham_vi || 'ca_bai',
    mo_ta: s.mo_ta || '',
    bieu_thuc_ket_qua: s.bieu_thuc_ket_qua || '',
    danh_sach_goi_y: (s.danh_sach_goi_y || []).filter((g) => g.trim()),
  }))
}

export function SuaCauHoi({ id, danhMuc, onDong, onLuuXong }) {
  const [bai, setBai] = useState(null)
  const [error, setError] = useState('')
  const [dangLuu, setDangLuu] = useState(false)

  useEffect(() => {
    api.getProblem(id).then(setBai).catch((e) => setError(e.message))
  }, [id])

  const dangOptions = dungDangOptions(danhMuc)

  async function luu() {
    setError('')
    if (bai.loai_cau === 'TLN') {
      const err = kiemTraDapAnTLN(bai.meta?.dap_an_cuoi)
      if (err) { setError(err); return }
    }
    setDangLuu(true)
    try {
      const opt = dangOptions.find((o) => o.value === String(bai.dang_id || ''))
      await api.updateProblem(id, {
        de_bai: bai.de_bai,
        do_kho: bai.do_kho,
        dang_id: bai.dang_id ? Number(bai.dang_id) : null,
        chuyen_de: opt?.cd || bai.chuyen_de,
        hinh_anh: bai.hinh_anh ?? null,
        meta: bai.meta,
        solution_steps: chuanHoaSteps(bai.solution_steps),
      })
      onLuuXong()
    } catch (e) {
      setError(e.message)
    } finally {
      setDangLuu(false)
    }
  }

  return (
    <KhungModal tieu_de={`Sửa câu hỏi #${id}`} error={error} onDong={onDong}>
      {!bai ? (
        <p className="text-muted text-sm">Đang tải...</p>
      ) : (
        <ThanCauHoiForm
          bai={bai} setBai={setBai} dangOptions={dangOptions}
          onLuu={luu} onDong={onDong} dangLuu={dangLuu} nutLuuText="Lưu thay đổi"
        />
      )}
    </KhungModal>
  )
}

function TaoCauHoi({ danhMuc, onDong, onLuuXong }) {
  const [bai, setBai] = useState(() => ({
    loai_cau: 'TN4PA', do_kho: 'tb', dang_id: null, de_bai: '',
    ...templateTheoLoai('TN4PA'),
  }))
  const [error, setError] = useState('')
  const [dangLuu, setDangLuu] = useState(false)

  const dangOptions = dungDangOptions(danhMuc)

  async function tao() {
    setError('')
    if (!bai.de_bai.trim()) { setError('Vui lòng nhập đề bài.'); return }
    if (!bai.dang_id) { setError('Vui lòng chọn Chuyên đề › Dạng.'); return }
    if (bai.loai_cau === 'TLN') {
      const err = kiemTraDapAnTLN(bai.meta?.dap_an_cuoi)
      if (err) { setError(err); return }
    }
    setDangLuu(true)
    try {
      const opt = dangOptions.find((o) => o.value === String(bai.dang_id || ''))
      await api.createProblem({
        loai_cau: bai.loai_cau,
        do_kho: bai.do_kho,
        dang_id: Number(bai.dang_id),
        chuyen_de: opt?.cd || '',
        de_bai: bai.de_bai,
        hinh_anh: bai.hinh_anh || null,
        meta: bai.meta,
        solution_steps: chuanHoaSteps(bai.solution_steps),
      })
      onLuuXong()
    } catch (e) {
      setError(e.message)
    } finally {
      setDangLuu(false)
    }
  }

  return (
    <KhungModal tieu_de="Tạo câu hỏi mới" error={error} onDong={onDong}>
      <p className="text-[12px] text-muted bg-surface-2 rounded-md px-3 py-2 mb-3">
        Chọn loại câu hỏi để hiện đúng cấu trúc nhập. Câu mới được lưu <b>đã duyệt, sẵn sàng dùng ngay</b> —
        học sinh trong lớp em phụ trách tự chọn luyện được, hoặc giao thẳng qua "Giao nhiệm vụ".
      </p>
      <ThanCauHoiForm
        bai={bai} setBai={setBai} dangOptions={dangOptions} choChonLoai
        onLuu={tao} onDong={onDong} dangLuu={dangLuu} nutLuuText="Tạo câu hỏi"
      />
    </KhungModal>
  )
}

const MOI_TRANG_CH = 20

export default function QuanLyCauHoi({ gvId = null, toanQuyen = false }) {
  const confirm = useConfirm()
  const [rows, setRows] = useState([])
  const [danhMuc, setDanhMuc] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [fTrangThai, setFTrangThai] = useState('')
  const [trangCH, setTrangCH] = useState(1)
  const [sua, setSua] = useState(null)
  const [taoMoi, setTaoMoi] = useState(false)
  const [importMo, setImportMo] = useState(false)
  const [importOk, setImportOk] = useState('')
  const [modalXoaVV, setModalXoaVV] = useState(null)   // { r, anhHuong }
  const [dangTaiAH, setDangTaiAH] = useState(false)
  const [dangXoaVV, setDangXoaVV] = useState(false)
  const [daXacNhan, setDaXacNhan] = useState(false)

  async function tai() {
    const [rs, dm] = await Promise.allSettled([api.listProblems(gvId), api.getDanhMuc(gvId)])
    if (rs.status === 'fulfilled') setRows(rs.value)
    if (dm.status === 'fulfilled') setDanhMuc(dm.value)
  }

  useEffect(() => {
    setLoading(true)
    tai().catch(() => {}).finally(() => setLoading(false))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [gvId])

  const loc = rows.filter((r) => {
    if (fTrangThai && r.trang_thai_duyet !== fTrangThai) return false
    return true
  })
  const tongTrangCH = Math.max(1, Math.ceil(loc.length / MOI_TRANG_CH))
  const locTrang = loc.slice((trangCH - 1) * MOI_TRANG_CH, trangCH * MOI_TRANG_CH)

  async function duyet(r) {
    try { await api.duyetCau(r.id, 'duyet'); await tai() }
    catch (e) { setError(e.message) }
  }
  async function xoa(r) {
    const msg = r.bi_an
      ? `Câu hỏi #${r.id} đang bị ẩn. Xóa vĩnh viễn?`
      : `Xóa câu hỏi #${r.id}?\n\nNếu đã có dữ liệu học sinh, câu hỏi sẽ được ẩn (không xóa vĩnh viễn, HS không thấy nữa).`
    if (!await confirm(msg)) return
    try {
      const res = await api.deleteProblem(r.id)
      if (res?.an) setError('Câu hỏi đã có phiên học của HS — đã ẩn khỏi danh sách HS (dữ liệu được giữ lại).')
      await tai()
    } catch (e) { setError(e.message) }
  }
  async function khoiPhuc(r) {
    if (!await confirm(`Khôi phục câu hỏi #${r.id}? Câu hỏi sẽ hiển thị lại cho HS.`)) return
    try { await api.khoiPhucProblem(r.id); await tai() }
    catch (e) { setError(e.message) }
  }
  async function huyDuyet(r) {
    if (!await confirm(`Hủy duyệt câu hỏi #${r.id}?\nCâu hỏi sẽ trở về trạng thái "Chờ duyệt".`)) return
    try { await api.updateProblem(r.id, { trang_thai_duyet: 'cho_duyet' }); await tai() }
    catch (e) { setError(e.message) }
  }

  async function moModalXoaVV(r) {
    setDangTaiAH(true)
    setDaXacNhan(false)
    try {
      const ah = await api.anhHuongProblem(r.id)
      setModalXoaVV({ r, anhHuong: ah })
    } catch (e) { setError(e.message) }
    finally { setDangTaiAH(false) }
  }
  async function thucHienXoaVV() {
    if (!modalXoaVV) return
    setDangXoaVV(true)
    try {
      await api.xoaVinhVienProblem(modalXoaVV.r.id)
      setModalXoaVV(null)
      await tai()
    } catch (e) { setError(e.message) }
    finally { setDangXoaVV(false) }
  }

  return (
    <div className="flex flex-col gap-4">
      {importOk && (
        <p className="text-success text-sm bg-success-soft rounded-md px-3 py-2">
          ✓ {importOk}
          <button onClick={() => setImportOk('')} className="ml-2 font-bold">✕</button>
        </p>
      )}
      {error && (
        <p className="text-danger text-sm bg-danger-soft rounded-md px-3 py-2">
          {error}
          <button onClick={() => setError('')} className="ml-2 font-bold">✕</button>
        </p>
      )}
      <div className="flex items-end justify-between gap-3 flex-wrap">
        <div className="flex flex-wrap items-end gap-3">
          <Select
            label="Lọc trạng thái duyệt"
            className="w-48"
            value={fTrangThai}
            onChange={(e) => { setFTrangThai(e.target.value); setTrangCH(1) }}
            options={[
              { value: '', label: 'Tất cả' },
              { value: 'da_duyet', label: 'Đã duyệt' },
              { value: 'cho_duyet', label: 'Chờ duyệt' },
              { value: 'loai', label: 'Đã loại' },
            ]}
          />
        </div>
        {!toanQuyen && (
          <div className="flex gap-2">
            <Button variant="secondary" onClick={() => setImportMo(true)}>Import từ Excel</Button>
            <Button onClick={() => setTaoMoi(true)}>+ Tạo câu hỏi mới</Button>
          </div>
        )}
      </div>

      <Card>
        <CardBody className="pt-5">
          {loading ? (
            <p className="text-muted text-sm">Đang tải...</p>
          ) : (
            <Table
              columns={[
                { key: 'id', header: '#', className: 'w-12' },
                {
                  key: 'chuyen_de',
                  header: 'Chuyên đề / Dạng',
                  render: (r) => (
                    <span>
                      {r.chuyen_de}
                      {r.dang_ten && <span className="text-muted"> › {r.dang_ten}</span>}
                      {r.hinh_anh && <span title="Có hình minh họa" className="ml-1">🖼️</span>}
                    </span>
                  ),
                },
                { key: 'loai_cau', header: 'Loại', render: (r) => NHAN_LOAI[r.loai_cau] || r.loai_cau },
                { key: 'do_kho', header: 'Mức độ', render: (r) => NHAN_KHO[r.do_kho] || r.do_kho },
                {
                  key: 'nguon',
                  header: 'Nguồn',
                  render: (r) => (
                    <Badge tone={r.nguon === 'ai_sinh' ? 'warning' : 'primary'}>
                      {NHAN_NGUON[r.nguon] || 'GV'}
                    </Badge>
                  ),
                },
                {
                  key: 'tao_luc',
                  header: 'Ngày giờ tạo',
                  render: (r) => <CotThoiGian iso={r.tao_luc} />,
                },
                {
                  key: 'trang_thai_duyet',
                  header: 'Trạng thái',
                  render: (r) => (
                    <div className="flex flex-wrap gap-1">
                      <Badge trang_thai={r.trang_thai_duyet} />
                      {r.bi_an && <Badge tone="neutral">Đã ẩn</Badge>}
                    </div>
                  ),
                },
                {
                  key: 'actions',
                  header: '',
                  render: (r) => {
                    const coQuyen = r.la_cua_toi || toanQuyen
                    return (
                    <div className="flex justify-end gap-1 flex-wrap">
                      <Button size="sm" variant="secondary" onClick={() => setSua(r.id)}>
                        {coQuyen ? 'Xem / Sửa' : 'Xem'}
                      </Button>
                      {coQuyen && !r.bi_an && r.trang_thai_duyet !== 'da_duyet' && (
                        <Button size="sm" variant="success" onClick={() => duyet(r)}>Duyệt</Button>
                      )}
                      {coQuyen && !r.bi_an && r.trang_thai_duyet === 'da_duyet' && (
                        <Button size="sm" variant="warning" onClick={() => huyDuyet(r)}>Hủy duyệt</Button>
                      )}
                      {coQuyen && (
                        r.bi_an ? (
                          <>
                            <Button size="sm" variant="primary" onClick={() => khoiPhuc(r)}>Khôi phục</Button>
                            <Button size="sm" variant="danger" onClick={() => moModalXoaVV(r)} disabled={dangTaiAH}>Xóa vĩnh viễn</Button>
                          </>
                        ) : (
                          <Button size="sm" variant="danger" onClick={() => xoa(r)}>Xóa</Button>
                        )
                      )}
                    </div>
                    )
                  },
                },
              ]}
              rows={locTrang}
              rowKey={(r) => r.id}
              empty="Chưa có câu hỏi nào."
            />
          )}
          {!loading && tongTrangCH > 1 && (
            <div className="flex items-center justify-between gap-2 pt-3 border-t border-border mt-2">
              <span className="text-xs text-muted">
                {loc.length} câu hỏi · Trang {trangCH}/{tongTrangCH}
              </span>
              <div className="flex items-center gap-1">
                <Button size="sm" variant="secondary" disabled={trangCH === 1}
                  onClick={() => setTrangCH(1)}>«</Button>
                <Button size="sm" variant="secondary" disabled={trangCH === 1}
                  onClick={() => setTrangCH(t => t - 1)}>‹</Button>
                <Button size="sm" variant="secondary" disabled={trangCH === tongTrangCH}
                  onClick={() => setTrangCH(t => t + 1)}>›</Button>
                <Button size="sm" variant="secondary" disabled={trangCH === tongTrangCH}
                  onClick={() => setTrangCH(tongTrangCH)}>»</Button>
              </div>
            </div>
          )}
        </CardBody>
      </Card>

      {sua && (
        <SuaCauHoi
          id={sua}
          danhMuc={danhMuc}
          onDong={() => setSua(null)}
          onLuuXong={() => { setSua(null); tai() }}
        />
      )}

      {taoMoi && (
        <TaoCauHoi
          danhMuc={danhMuc}
          onDong={() => setTaoMoi(false)}
          onLuuXong={() => { setTaoMoi(false); tai() }}
        />
      )}

      {importMo && (
        <ImportCauHoiDialog
          onClose={() => setImportMo(false)}
          onSaved={(msg) => { setImportMo(false); setImportOk(msg); tai() }}
        />
      )}

      {modalXoaVV && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6 flex flex-col gap-4">
            <h2 className="text-lg font-bold text-danger">⚠️ Xóa vĩnh viễn câu hỏi #{modalXoaVV.r.id}</h2>
            <p className="text-sm text-muted">
              Hành động này <strong>không thể hoàn tác</strong>. Toàn bộ dữ liệu liên quan sẽ bị xóa:
            </p>
            <div className="bg-danger-soft rounded-lg px-4 py-3 text-sm flex flex-col gap-1">
              <span>🗂 <strong>{modalXoaVV.anhHuong.so_phien}</strong> phiên học</span>
              <span>👤 <strong>{modalXoaVV.anhHuong.so_hoc_sinh}</strong> học sinh bị ảnh hưởng</span>
              <span>💬 <strong>{modalXoaVV.anhHuong.so_luot}</strong> lượt hội thoại</span>
              <span>🚩 <strong>{modalXoaVV.anhHuong.so_co}</strong> cờ theo dõi</span>
            </div>
            <label className="flex items-start gap-2 text-sm cursor-pointer">
              <input
                type="checkbox"
                className="mt-0.5"
                checked={daXacNhan}
                onChange={(e) => setDaXacNhan(e.target.checked)}
              />
              <span>Tôi hiểu rằng dữ liệu sẽ bị xóa vĩnh viễn và không thể khôi phục</span>
            </label>
            <div className="flex justify-end gap-2">
              <Button variant="secondary" onClick={() => { setModalXoaVV(null); setDaXacNhan(false) }}>
                Hủy
              </Button>
              <Button
                onClick={thucHienXoaVV}
                disabled={!daXacNhan || dangXoaVV}
                className="bg-danger text-white hover:bg-danger/90 disabled:opacity-40"
              >
                {dangXoaVV ? 'Đang xóa...' : 'Xóa vĩnh viễn'}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
