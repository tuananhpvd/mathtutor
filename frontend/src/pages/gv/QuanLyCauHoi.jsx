import { useEffect, useRef, useState } from 'react'
import { api } from '../../api'
import { Badge, Button, Card, CardBody, Input, Select, Table, useConfirm } from '../../components/ui'
import Formula from '../../components/Formula'
import ImportCauHoiDialog from '../../components/gv/ImportCauHoiDialog'

const NHAN_LOAI = { TN4PA: 'Trắc nghiệm ABCD', TNDS: 'Đúng/Sai 4 ý', TLN: 'Trả lời ngắn' }

function kiemTraDapAnTLN(v) {
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
      { label: 'x^{n}', snippet: '^{}', back: 2 },
      { label: 'x^{2}', snippet: '^2', back: 0 },
      { label: '\\dfrac{a}{b}', snippet: '\\dfrac{}{}', back: 7 },
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
      { label: '\\int_a^b f\\,dx', snippet: '\\int_{}^{}  \\, dx', back: 6 },
      { label: '\\lim_{x \\to a}', snippet: '\\lim_{ \\to } ', back: 6 },
      { label: "f'(x)", snippet: "f'()", back: 3 },
      { label: "f''(x)", snippet: "f''()", back: 4 },
      { label: '\\dfrac{d}{dx}\\!f', snippet: '\\dfrac{d}{dx}()', back: 1 },
      { label: 'F(x)', snippet: 'F()', back: 2 },
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
    ],
  },
]

function BangCongThuc({ onChen }) {
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
function TexField({ value, onChange, label, multiline, registerActive, placeholder }) {
  const ref = useRef(null)
  function focusSelf() {
    registerActive((snippet, back) => {
      const el = ref.current
      const v = value || ''
      const start = el?.selectionStart ?? v.length
      const end = el?.selectionEnd ?? v.length
      const next = v.slice(0, start) + snippet + v.slice(end)
      onChange(next)
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
      {value && /\$[^$]+\$/.test(value) && (
        <p className="text-[13px] text-ink/80 mt-1 px-1">{renderTex(value)}</p>
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
function ThanCauHoiForm({ bai, setBai, dangOptions, choChonLoai, onLuu, onDong, dangLuu, nutLuuText }) {
  const activeInsert = useRef(null)
  const register = (fn) => { activeInsert.current = fn }
  const chen = (s, b) => activeInsert.current?.(s, b)

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
    <div className="fixed inset-0 z-20 bg-black/30 flex justify-end" onClick={onDong}>
      <div
        className="w-2/3 min-w-[620px] bg-surface h-full overflow-y-auto p-6 shadow-[var(--shadow-pop)]"
        onClick={(e) => e.stopPropagation()}
      >
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
function dungDangOptions(danhMuc) {
  return [
    { value: '', label: '— Chưa gán dạng —' },
    ...danhMuc.flatMap((cd) =>
      cd.dang_list.map((d) => ({ value: String(d.id), label: `${cd.ten} › ${d.ten}`, cd: cd.ten }))
    ),
  ]
}

// Chuẩn hóa payload các bước.
function chuanHoaSteps(steps) {
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
        Chọn loại câu hỏi để hiện đúng cấu trúc nhập. Câu mới được lưu <b>riêng tư và sẵn sàng dùng ngay</b> —
        bấm <b>"Chia sẻ"</b> để HS tự chọn luyện, hoặc giao thẳng cho HS qua "Giao nhiệm vụ".
      </p>
      <ThanCauHoiForm
        bai={bai} setBai={setBai} dangOptions={dangOptions} choChonLoai
        onLuu={tao} onDong={onDong} dangLuu={dangLuu} nutLuuText="Tạo câu hỏi"
      />
    </KhungModal>
  )
}

const TABS_PHAM_VI = [
  { value: '', label: 'Tất cả' },
  { value: 'cua_toi', label: 'Câu của tôi' },
  { value: 'chung', label: 'Kho chung' },
]

export default function QuanLyCauHoi() {
  const confirm = useConfirm()
  const [rows, setRows] = useState([])
  const [danhMuc, setDanhMuc] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [fTrangThai, setFTrangThai] = useState('')
  const [fPhamVi, setFPhamVi] = useState('')
  const [sua, setSua] = useState(null)
  const [taoMoi, setTaoMoi] = useState(false)
  const [importMo, setImportMo] = useState(false)
  const [importOk, setImportOk] = useState('')
  const [modalXoaVV, setModalXoaVV] = useState(null)   // { r, anhHuong }
  const [dangTaiAH, setDangTaiAH] = useState(false)
  const [dangXoaVV, setDangXoaVV] = useState(false)
  const [daXacNhan, setDaXacNhan] = useState(false)

  async function tai() {
    const [rs, dm] = await Promise.allSettled([api.listProblems(), api.getDanhMuc()])
    if (rs.status === 'fulfilled') setRows(rs.value)
    if (dm.status === 'fulfilled') setDanhMuc(dm.value)
  }

  useEffect(() => {
    tai().catch(() => {}).finally(() => setLoading(false))
  }, [])

  const loc = rows.filter((r) => {
    if (fTrangThai && r.trang_thai_duyet !== fTrangThai) return false
    if (fPhamVi === 'cua_toi') return r.la_cua_toi
    if (fPhamVi === 'chung') return r.pham_vi === 'chung'
    return true
  })

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
  async function chiaSe(r) {
    const dangChung = r.pham_vi === 'chung'
    const msg = dangChung
      ? `Thu hồi câu hỏi #${r.id} về riêng tư?\nHọc sinh sẽ không tự chọn được nữa (bài đang làm dở không bị ảnh hưởng).`
      : `Chia sẻ câu hỏi #${r.id} lên kho chung?\nMọi giáo viên đều thấy và học sinh tự chọn được.`
    if (!await confirm(msg)) return
    try { await api.chiaSeProblem(r.id); await tai() }
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
            onChange={(e) => setFTrangThai(e.target.value)}
            options={[
              { value: '', label: 'Tất cả' },
              { value: 'da_duyet', label: 'Đã duyệt' },
              { value: 'cho_duyet', label: 'Chờ duyệt' },
              { value: 'loai', label: 'Đã loại' },
            ]}
          />
          <div className="flex gap-1 pb-0.5">
            {TABS_PHAM_VI.map((t) => (
              <button key={t.value} onClick={() => setFPhamVi(t.value)}
                className={`px-3 py-1.5 rounded-full text-xs font-semibold border transition-colors ${
                  fPhamVi === t.value
                    ? 'bg-primary text-white border-primary'
                    : 'bg-surface text-ink border-border hover:border-primary'
                }`}>
                {t.label}
              </button>
            ))}
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="secondary" onClick={() => setImportMo(true)}>Import từ Excel</Button>
          <Button onClick={() => setTaoMoi(true)}>+ Tạo câu hỏi mới</Button>
        </div>
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
                    </span>
                  ),
                },
                { key: 'loai_cau', header: 'Loại', render: (r) => NHAN_LOAI[r.loai_cau] || r.loai_cau },
                { key: 'do_kho', header: 'Mức độ', render: (r) => NHAN_KHO[r.do_kho] || r.do_kho },
                {
                  key: 'nguon',
                  header: 'Nguồn / Phạm vi',
                  render: (r) => (
                    <div className="flex flex-wrap gap-1">
                      <Badge tone={r.nguon === 'ai_sinh' ? 'warning' : 'primary'}>
                        {NHAN_NGUON[r.nguon] || 'GV'}
                      </Badge>
                      <Badge tone={r.pham_vi === 'chung' ? 'success' : 'neutral'}>
                        {r.pham_vi === 'chung' ? 'Dùng chung' : 'Riêng tư'}
                      </Badge>
                    </div>
                  ),
                },
                {
                  key: 'tao_luc',
                  header: 'Ngày giờ tạo',
                  render: (r) => <span className="text-muted text-sm">{dinhDangNgay(r.tao_luc)}</span>,
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
                  render: (r) => (
                    <div className="flex justify-end gap-1 flex-wrap">
                      {r.la_cua_toi && (
                        <Button size="sm" variant="secondary" onClick={() => setSua(r.id)}>Xem / Sửa</Button>
                      )}
                      {!r.la_cua_toi && (
                        <Button size="sm" variant="secondary" onClick={() => setSua(r.id)}>Xem</Button>
                      )}
                      {r.la_cua_toi && !r.bi_an && r.trang_thai_duyet !== 'da_duyet' && (
                        <Button size="sm" variant="success" onClick={() => duyet(r)}>Duyệt</Button>
                      )}
                      {r.la_cua_toi && !r.bi_an && r.trang_thai_duyet === 'da_duyet' && (
                        <Button size="sm" variant="warning" onClick={() => huyDuyet(r)}>Hủy duyệt</Button>
                      )}
                      {r.la_cua_toi && !r.bi_an && r.trang_thai_duyet === 'da_duyet' && (
                        <Button
                          size="sm"
                          variant={r.pham_vi === 'chung' ? 'secondary' : 'success'}
                          onClick={() => chiaSe(r)}
                        >
                          {r.pham_vi === 'chung' ? 'Thu hồi' : 'Chia sẻ'}
                        </Button>
                      )}
                      {r.la_cua_toi && (
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
                  ),
                },
              ]}
              rows={loc}
              rowKey={(r) => r.id}
              empty="Chưa có câu hỏi nào."
            />
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
