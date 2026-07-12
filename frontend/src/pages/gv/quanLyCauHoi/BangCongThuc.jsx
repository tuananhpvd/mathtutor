import Formula from '../../../components/Formula'

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
