import { useEffect, useRef, useState } from 'react'
import { Button } from '../ui'
import Formula from '../Formula'
import FormulaEditor from '../FormulaEditor'
import MathPalette from './MathPalette'

// TLN: nhập biểu thức qua editor + palette công thức nhỏ gọn → xác nhận → gửi.
// Bảng công thức chỉ hiện khi HS bấm vào khối nhập (focus), tự ẩn khi bấm ra ngoài — cho gọn,
// giống hành vi ô "Trò chuyện với gia sư".
export default function AnswerInputTLN({ onGui, dang_gui }) {
  const [latex, setLatex] = useState('')
  const [daFocus, setDaFocus] = useState(false)
  const wrapRef = useRef(null)

  const getMf = () => wrapRef.current?.querySelector('math-field')
  const syncFromField = () => {
    const mf = getMf()
    if (mf) setLatex(mf.value)
  }

  // Ẩn bảng công thức khi bấm ra NGOÀI toàn khối (kể cả bảng). Dùng mousedown (xảy ra TRƯỚC
  // click) — nhưng vì bảng nằm TRONG wrapRef nên bấm nút bảng không bị coi là "ngoài", không
  // ẩn sớm trước khi kịp chèn công thức.
  useEffect(() => {
    // Cả 'focusin' lẫn 'mousedown' — để khi HS bấm sang ô "Trò chuyện với gia sư" (hay ô nhập
    // khác) thì bảng công thức của khu vực trả lời tự ẩn (không hiện đồng thời 2 bảng).
    function ngoai(e) {
      if (wrapRef.current && !wrapRef.current.contains(e.target)) setDaFocus(false)
    }
    document.addEventListener('mousedown', ngoai)
    document.addEventListener('focusin', ngoai)
    return () => {
      document.removeEventListener('mousedown', ngoai)
      document.removeEventListener('focusin', ngoai)
    }
  }, [])

  function gui() {
    const bieu_thuc = latex.trim()
    if (!bieu_thuc) return
    // Bọc $...$ để ChatBubble render thành công thức thay vì hiện LaTeX thô.
    onGui({ dap_an_nhap: bieu_thuc, noi_dung: `Em trả lời: $${bieu_thuc}$` })
    setLatex('')
    setDaFocus(false)
  }

  return (
    <div className="flex flex-col gap-3" ref={wrapRef} onFocus={() => setDaFocus(true)}>
      <FormulaEditor value={latex} onChange={setLatex} placeholder="Nhập biểu thức kết quả" />

      {latex.trim() && (
        <div className="rounded-md bg-surface-2 px-3 py-2">
          <p className="text-xs text-muted mb-1">Xác nhận em nhập:</p>
          <Formula latex={latex} block />
        </div>
      )}

      <Button disabled={!latex.trim() || dang_gui} onClick={gui}>
        Gửi câu trả lời
      </Button>

      {daFocus && (
        <>
          <p className="text-xs font-bold text-danger">Bấm vào bảng bên dưới để nhập công thức</p>
          <MathPalette getMf={getMf} onInserted={syncFromField} />
        </>
      )}
    </div>
  )
}
