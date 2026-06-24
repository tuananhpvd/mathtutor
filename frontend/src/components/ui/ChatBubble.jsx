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
 * Bong bóng hội thoại. vai_tro: 'gia_su' | 'hoc_sinh'.
 */
export default function ChatBubble({ vai_tro, children, text }) {
  const laGiaSu = vai_tro === 'gia_su'
  return (
    <div className={`flex ${laGiaSu ? 'justify-start' : 'justify-end'}`}>
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
          laGiaSu
            ? 'bg-surface border border-border text-ink rounded-bl-sm'
            : 'bg-primary text-white rounded-br-sm'
        }`}
      >
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
