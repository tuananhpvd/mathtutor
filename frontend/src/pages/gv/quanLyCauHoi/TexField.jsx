import { useEffect, useRef } from 'react'
import Formula from '../../../components/Formula'

function renderTex(text) {
  return String(text || '')
    .split(/(\$[^$]+\$)/g)
    .map((p, i) =>
      p.startsWith('$') ? <Formula key={i} latex={p.slice(1, -1)} /> : <span key={i}>{p}</span>
    )
}

// Ô nhập có xem trước công thức + đăng ký làm ô đang focus để chèn ký hiệu.
export function TexField({ value, onChange, label, multiline, rows, registerActive, placeholder }) {
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
      {multiline ? <textarea rows={rows || 2} {...common} /> : <input {...common} />}
      {value && (
        <p className="text-[13px] text-ink/80 mt-1 px-2.5 py-1.5 rounded-lg bg-primary-soft border border-primary/30 whitespace-pre-wrap">
          {renderTex(value)}
        </p>
      )}
    </div>
  )
}
