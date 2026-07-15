/**
 * Ô nhập hỗn hợp: text thường + công thức $latex$.
 * - Gõ thẳng → text thường.
 * - Bấm MathPalette → chèn $latex$ tại vị trí con trỏ.
 * - Preview render $...$ thành KaTeX khi có nội dung.
 */
import { forwardRef, useEffect, useImperativeHandle, useRef, useState } from 'react'
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

const MixedChatInput = forwardRef(function MixedChatInput({
  value, onChange, placeholder = 'Nhập nội dung...', rows = 3,
  // luonHienBangCT=true (mặc định, giữ nguyên hành vi cũ ở "Nhờ thầy/cô"): bảng công thức
  // luôn hiện. false: chỉ hiện khi bấm vào ô (gọn hơn cho ô hỏi ngắn) — ẩn lại khi bấm ra
  // ngoài toàn bộ khối (kể cả bảng), KHÔNG dùng onBlur vì sẽ ẩn bảng ngay trước khi kịp
  // nhận click vào 1 nút trong bảng (mousedown xảy ra trước click).
  luonHienBangCT = true,
  // Không đặt sẵn "border border-border" ở class gốc (mới đây cần bỏ viền cho 1 chỗ dùng
  // riêng) — mặc định giữ NGUYÊN giao diện có viền cũ, chỗ nào cần khác tự truyền đè.
  textareaClassName = 'border border-border',
  // Nội dung hiện NGAY DƯỚI ô nhập, rộng bằng ô (vd nút Gửi) — luôn sát ô, không bị đẩy
  // xuống dưới cùng bảng công thức khi bảng hiện ra (nằm TRƯỚC phần xem trước/bảng công thức).
  duoiO = null,
}, ref) {
  const textareaRef = useRef(null)
  const wrapRef = useRef(null)
  const [daFocus, setDaFocus] = useState(luonHienBangCT)

  useImperativeHandle(ref, () => ({
    focus() { textareaRef.current?.focus() },
  }))
  // Ref để adapter luôn đọc được giá trị mới nhất (tránh stale closure).
  const valueRef = useRef(value)
  useEffect(() => {
    valueRef.current = value
  }, [value])

  useEffect(() => {
    if (luonHienBangCT) return
    function ngoaiClick(e) {
      if (wrapRef.current && !wrapRef.current.contains(e.target)) setDaFocus(false)
    }
    document.addEventListener('mousedown', ngoaiClick)
    return () => document.removeEventListener('mousedown', ngoaiClick)
  }, [luonHienBangCT])

  const hienBang = luonHienBangCT || daFocus

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
    <div className="flex flex-col gap-2" ref={wrapRef}>
      <textarea
        ref={textareaRef}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onFocus={() => setDaFocus(true)}
        rows={rows}
        placeholder={placeholder}
        className={`w-full rounded-lg px-3 py-2 text-sm text-ink
          focus:outline-none focus:ring-2 focus:ring-primary/40 resize-y ${textareaClassName}`}
      />

      {duoiO}

      {value.trim() && (
        <div className="rounded-md bg-surface-2 px-3 py-2">
          <p className="text-[11px] text-muted mb-1">Xem trước:</p>
          <div className="text-sm text-ink leading-relaxed">{renderPreview(value)}</div>
        </div>
      )}

      {hienBang && (
        <>
          <p className="text-xs font-bold text-danger">Bấm vào bảng bên dưới để chèn công thức</p>
          <MathPalette getMf={getMf} onInserted={() => {}} />
        </>
      )}
    </div>
  )
})

export default MixedChatInput
