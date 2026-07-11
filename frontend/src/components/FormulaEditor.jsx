import { useEffect, useRef, useState } from 'react'

/**
 * Editor nhập công thức LaTeX dùng MathLive.
 * Chỉ render <math-field> SAU khi mathlive đã đăng ký custom element, để listener
 * 'input' luôn gắn vào phần tử đã "upgrade" (nếu không, gõ sẽ không cập nhật giá trị).
 * Props: value (string LaTeX), onChange(latex), placeholder
 */
export default function FormulaEditor({ value = '', onChange, placeholder = 'Nhập công thức...' }) {
  const ref = useRef(null)
  const [ready, setReady] = useState(false)
  const [loiTai, setLoiTai] = useState(false)
  const [thuLai, setThuLai] = useState(0)

  // Tải & đăng ký custom element math-field
  useEffect(() => {
    let con = true
    import('mathlive')
      .then(() => {
        if (con) setReady(true)
      })
      .catch(() => {
        if (con) setLoiTai(true)
      })
    return () => {
      con = false
    }
  }, [thuLai])

  // Gắn listener sau khi phần tử đã render & upgrade
  useEffect(() => {
    if (!ready) return
    const mf = ref.current
    if (!mf) return
    // Tắt bàn phím overlay mặc định — dùng palette công thức nhỏ gọn riêng.
    mf.mathVirtualKeyboardPolicy = 'manual'
    // Ẩn menu ngữ cảnh của MathLive.
    mf.menuItems = []
    // Placeholder bọc \text{} để tiếng Việt có dấu hiển thị đúng (không bị math-font làm dính).
    if (placeholder) mf.setAttribute('placeholder', `\\text{${placeholder}}`)
    if (value && mf.value !== value) mf.value = value

    const handler = (e) => onChange && onChange(e.target.value)
    mf.addEventListener('input', handler)
    return () => mf.removeEventListener('input', handler)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ready])

  // Đồng bộ giá trị từ ngoài (vd reset về rỗng sau khi gửi)
  useEffect(() => {
    const mf = ref.current
    if (ready && mf && value !== mf.value) mf.value = value
  }, [ready, value])

  const cls =
    'w-full border border-border rounded-md px-3 py-2 text-base bg-surface ' +
    'focus:outline-none focus:ring-2 focus:ring-primary/40 min-h-[44px]'

  if (loiTai) {
    return (
      <div className={`${cls} flex items-center justify-between gap-2 text-danger`}>
        <span>Không tải được bộ soạn công thức. Kiểm tra kết nối mạng.</span>
        <button
          type="button"
          className="shrink-0 rounded border border-danger px-2 py-0.5 text-xs hover:bg-danger-soft"
          onClick={() => {
            setLoiTai(false)
            setThuLai((n) => n + 1)
          }}
        >
          Thử lại
        </button>
      </div>
    )
  }
  if (!ready) {
    return <div className={`${cls} text-muted animate-pulse`}>Đang tải bộ soạn công thức…</div>
  }
  return <math-field ref={ref} class={cls} />
}
