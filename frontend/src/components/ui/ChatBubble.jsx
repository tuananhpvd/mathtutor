import Formula from '../Formula'

// Tách $...$ thành công thức KaTeX, còn lại là chữ thường.
function renderNoiDung(text) {
  const parts = String(text).split(/(\$[^$]+\$)/g)
  return parts.map((part, i) =>
    part.startsWith('$') && part.endsWith('$') ? (
      <Formula key={i} latex={part.slice(1, -1)} />
    ) : (
      <span key={i}>{part}</span>
    )
  )
}

/**
 * Bong bóng hội thoại. vai_tro: 'gia_su' | 'hoc_sinh' | 'giao_vien'.
 * 'giao_vien' = lời thầy/cô trả lời trực tiếp (A2) — nổi bật để phân biệt với gia sư AI.
 */
export default function ChatBubble({ vai_tro, children, text }) {
  const laHocSinh = vai_tro === 'hoc_sinh'
  const laGiaoVien = vai_tro === 'giao_vien'
  return (
    <div className={`flex ${laHocSinh ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
          laHocSinh
            ? 'bg-primary text-white rounded-br-sm'
            : laGiaoVien
              ? 'bg-gv/10 border border-gv/40 text-ink rounded-bl-sm'
              : 'bg-surface border border-border text-ink rounded-bl-sm'
        }`}
      >
        {laGiaoVien && (
          <p className="text-[11px] font-bold text-gv mb-1">👩‍🏫 Thầy/cô trả lời</p>
        )}
        {text != null ? renderNoiDung(text) : children}
      </div>
    </div>
  )
}

export function TypingBubble() {
  return (
    <div className="flex justify-start">
      <div className="bg-surface border border-border rounded-2xl rounded-bl-sm px-4 py-3">
        <div className="flex gap-1">
          {[0, 1, 2].map((i) => (
            <span
              key={i}
              className="h-2 w-2 rounded-full bg-muted animate-bounce"
              style={{ animationDelay: `${i * 0.15}s` }}
            />
          ))}
        </div>
      </div>
    </div>
  )
}
