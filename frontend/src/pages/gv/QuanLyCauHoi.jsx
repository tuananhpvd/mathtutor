import { useEffect, useRef, useState } from 'react'
import { api } from '../../api'
import { Badge, Button, Card, CardBody, Input, Select, Table } from '../../components/ui'
import Formula from '../../components/Formula'

const NHAN_LOAI = { TN4PA: 'Trắc nghiệm A–D', TNDS: 'Đúng/Sai 4 ý', TLN: 'Trả lời ngắn' }

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

function SuaCauHoi({ id, danhMuc, onDong, onLuuXong }) {
  const [bai, setBai] = useState(null)
  const [error, setError] = useState('')
  const [dangLuu, setDangLuu] = useState(false)
  const activeInsert = useRef(null)
  const register = (fn) => { activeInsert.current = fn }
  const chen = (s, b) => activeInsert.current?.(s, b)

  useEffect(() => {
    api.getProblem(id).then(setBai).catch((e) => setError(e.message))
  }, [id])

  const dangOptions = [
    { value: '', label: '— Chưa gán dạng —' },
    ...danhMuc.flatMap((cd) =>
      cd.dang_list.map((d) => ({ value: String(d.id), label: `${cd.ten} › ${d.ten}`, cd: cd.ten }))
    ),
  ]

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

  async function luu() {
    setDangLuu(true)
    setError('')
    try {
      const opt = dangOptions.find((o) => o.value === String(bai.dang_id || ''))
      const payload = {
        de_bai: bai.de_bai,
        do_kho: bai.do_kho,
        dang_id: bai.dang_id ? Number(bai.dang_id) : null,
        chuyen_de: opt?.cd || bai.chuyen_de,
        meta: bai.meta,
        solution_steps: bai.solution_steps.map((s) => ({
          thu_tu: s.thu_tu,
          pham_vi: s.pham_vi || 'ca_bai',
          mo_ta: s.mo_ta || '',
          bieu_thuc_ket_qua: s.bieu_thuc_ket_qua || '',
          danh_sach_goi_y: (s.danh_sach_goi_y || []).filter((g) => g.trim()),
        })),
      }
      await api.updateProblem(id, payload)
      onLuuXong()
    } catch (e) {
      setError(e.message)
    } finally {
      setDangLuu(false)
    }
  }

  return (
    <div className="fixed inset-0 z-20 bg-black/30 flex justify-end" onClick={onDong}>
      <div
        className="w-2/3 min-w-[620px] bg-surface h-full overflow-y-auto p-6 shadow-[var(--shadow-pop)]"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-ink">Sửa câu hỏi #{id}</h3>
          <button onClick={onDong} className="text-muted hover:text-ink text-lg">✕</button>
        </div>
        {error && <p className="text-danger text-sm bg-danger-soft rounded-md px-3 py-2 mb-3">{error}</p>}
        {!bai ? (
          <p className="text-muted text-sm">Đang tải...</p>
        ) : (
          <div className="grid grid-cols-[1fr_18rem] gap-5">
            {/* Cột trái: form */}
            <div className="flex flex-col gap-4">
              <div className="grid sm:grid-cols-2 gap-3">
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
                <Input
                  label="Đáp án cuối (để máy đối chiếu)"
                  value={bai.meta?.dap_an_cuoi ?? ''}
                  onChange={(e) => setMeta({ dap_an_cuoi: e.target.value })}
                />
              )}

              {/* Các bước lời giải */}
              <div className="flex flex-col gap-3">
                <div className="flex items-center justify-between">
                  <p className="text-xs text-muted">Các bước & gợi ý</p>
                  <Button size="sm" variant="ghost" onClick={themBuoc}>+ Thêm bước</Button>
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
                <Button onClick={luu} disabled={dangLuu}>{dangLuu ? 'Đang lưu...' : 'Lưu thay đổi'}</Button>
                <Button variant="secondary" onClick={onDong}>Hủy</Button>
              </div>
            </div>

            {/* Cột phải: bảng công thức (sticky) */}
            <div className="sticky top-0 self-start">
              <BangCongThuc onChen={chen} />
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default function QuanLyCauHoi() {
  const [rows, setRows] = useState([])
  const [danhMuc, setDanhMuc] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [fTrangThai, setFTrangThai] = useState('')
  const [sua, setSua] = useState(null)

  async function tai() {
    const [rs, dm] = await Promise.allSettled([api.listProblems(), api.getDanhMuc()])
    if (rs.status === 'fulfilled') setRows(rs.value)
    if (dm.status === 'fulfilled') setDanhMuc(dm.value)
  }

  useEffect(() => {
    tai().catch(() => {}).finally(() => setLoading(false))
  }, [])

  const loc = rows.filter((r) => !fTrangThai || r.trang_thai_duyet === fTrangThai)

  async function duyet(r) {
    try { await api.duyetCau(r.id, 'duyet'); await tai() }
    catch (e) { setError(e.message) }
  }
  async function xoa(r) {
    if (!window.confirm(`Xóa câu hỏi #${r.id}? Hành động này không hoàn tác.`)) return
    try { await api.deleteProblem(r.id); await tai() }
    catch (e) { setError(e.message) }
  }

  return (
    <div className="flex flex-col gap-4">
      {error && (
        <p className="text-danger text-sm bg-danger-soft rounded-md px-3 py-2">
          {error}
          <button onClick={() => setError('')} className="ml-2 font-bold">✕</button>
        </p>
      )}
      <div className="flex items-end justify-between gap-3 flex-wrap">
        <Select
          label="Lọc trạng thái duyệt"
          className="w-56"
          value={fTrangThai}
          onChange={(e) => setFTrangThai(e.target.value)}
          options={[
            { value: '', label: 'Tất cả' },
            { value: 'da_duyet', label: 'Đã duyệt' },
            { value: 'cho_duyet', label: 'Chờ duyệt' },
            { value: 'loai', label: 'Đã loại' },
          ]}
        />
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
                { key: 'do_kho', header: 'Mức độ' },
                {
                  key: 'trang_thai_duyet',
                  header: 'Trạng thái',
                  render: (r) => <Badge trang_thai={r.trang_thai_duyet} />,
                },
                {
                  key: 'actions',
                  header: '',
                  render: (r) => (
                    <div className="flex justify-end gap-1">
                      <Button size="sm" variant="ghost" onClick={() => setSua(r.id)}>Xem / Sửa</Button>
                      {r.trang_thai_duyet !== 'da_duyet' && (
                        <Button size="sm" variant="ghost" onClick={() => duyet(r)}>Duyệt</Button>
                      )}
                      <Button size="sm" variant="ghost" onClick={() => xoa(r)}>
                        <span className="text-danger">Xóa</span>
                      </Button>
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
    </div>
  )
}
