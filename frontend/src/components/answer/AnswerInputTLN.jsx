import { useRef, useState } from 'react'
import { Button } from '../ui'
import Formula from '../Formula'
import FormulaEditor from '../FormulaEditor'
import MathPalette from './MathPalette'

// TLN: nhập biểu thức qua editor + palette công thức nhỏ gọn → xác nhận → gửi.
export default function AnswerInputTLN({ onGui, dang_gui }) {
  const [latex, setLatex] = useState('')
  const wrapRef = useRef(null)

  const getMf = () => wrapRef.current?.querySelector('math-field')
  const syncFromField = () => {
    const mf = getMf()
    if (mf) setLatex(mf.value)
  }

  function gui() {
    const bieu_thuc = latex.trim()
    if (!bieu_thuc) return
    // Bọc $...$ để ChatBubble render thành công thức thay vì hiện LaTeX thô.
    onGui({ dap_an_nhap: bieu_thuc, noi_dung: `Em trả lời: $${bieu_thuc}$` })
    setLatex('')
  }

  return (
    <div className="flex flex-col gap-3">
      <div ref={wrapRef}>
        <FormulaEditor value={latex} onChange={setLatex} placeholder="Nhập biểu thức kết quả" />
      </div>

      {latex.trim() && (
        <div className="rounded-md bg-surface-2 px-3 py-2">
          <p className="text-xs text-muted mb-1">Xác nhận em nhập:</p>
          <Formula latex={latex} block />
        </div>
      )}

      <Button disabled={!latex.trim() || dang_gui} onClick={gui}>
        Gửi câu trả lời
      </Button>

      <p className="text-xs font-bold text-danger">Bấm vào bảng bên dưới để nhập công thức</p>
      <MathPalette getMf={getMf} onInserted={syncFromField} />
    </div>
  )
}
