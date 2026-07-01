/**
 * Ô nhập hỗn hợp: text thường + công thức $latex$.
 * - Gõ thẳng → text thường.
 * - Bấm MathPalette → chèn $latex$ tại vị trí con trỏ.
 * - Preview render $...$ thành KaTeX khi có nội dung.
 */
import { useRef } from 'react'
import Formula from './Formula'
import MathPalette from './answer/MathPalette'

function renderPreview(text) {
  return String(text)
    .split(/(\$[^$]+\$)/g)
    .map((p, i) =>
      p.startsWith('$') && p.endsWith('$') ? (
        <Formula key={i} latex={p.slice(1, -1)} />
      ) : (
        <span key={i}>{p}</span>
      )
    )
}

export default function MixedChatInput({ value, onChange, placeholder = 'Nhập nội dung...', rows = 3 }) {
  const textareaRef = useRef(null)
  // Ref để adapter luôn đọc được giá trị mới nhất (tránh stale closure).
  const valueRef = useRef(value)
  valueRef.current = value

  function getMf() {
    const el = textareaRef.current
    if (!el) return null
    return {
      focus() { el.focus() },
      insert(latex) {
        const clean = latex.replace(/\\placeholder\{\}/g, '')
        const toInsert = `$${clean}$`
        const start = el.selectionStart ?? valueRef.current.length
        const end = el.selectionEnd ?? valueRef.current.length
        const v = valueRef.current
        onChange(v.substring(0, start) + toInsert + v.substring(end))
        // Đặt lại con trỏ sau ký tự vừa chèn (sau khi React re-render).
        requestAnimationFrame(() => {
          if (!textareaRef.current) return
          const pos = start + toInsert.length
          textareaRef.current.setSelectionRange(pos, pos)
          textareaRef.current.focus()
        })
      },
      executeCommand(cmd) {
        if (cmd !== 'deleteBackward') return
        const start = el.selectionStart ?? valueRef.current.length
        const end = el.selectionEnd ?? valueRef.current.length
        const v = valueRef.current
        const newStart = start === end ? Math.max(0, start - 1) : start
        onChange(v.substring(0, newStart) + v.substring(end))
        requestAnimationFrame(() => {
          if (!textareaRef.current) return
          textareaRef.current.setSelectionRange(newStart, newStart)
          textareaRef.current.focus()
        })
      },
      get value() { return valueRef.current },
      set value(v) { onChange(v) },
    }
  }

  return (
    <div className="flex flex-col gap-2">
      <textarea
        ref={textareaRef}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        rows={rows}
        placeholder={placeholder}
        className="w-full rounded-lg border border-border px-3 py-2 text-sm text-ink
          focus:outline-none focus:ring-2 focus:ring-primary/40 resize-y"
      />

      {value.trim() && (
        <div className="rounded-md bg-surface-2 px-3 py-2">
          <p className="text-[11px] text-muted mb-1">Xem trước:</p>
          <div className="text-sm text-ink leading-relaxed">{renderPreview(value)}</div>
        </div>
      )}

      <p className="text-xs font-bold text-danger">Bấm vào bảng bên dưới để chèn công thức</p>
      <MathPalette getMf={getMf} onInserted={() => {}} />
    </div>
  )
}
