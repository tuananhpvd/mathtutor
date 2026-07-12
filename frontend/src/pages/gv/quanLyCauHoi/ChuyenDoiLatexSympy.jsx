import { useEffect, useRef, useState } from 'react'
import { api } from '../../../api'
import Formula from '../../../components/Formula'
import FormulaEditor from '../../../components/FormulaEditor'
import MathPalette from '../../../components/answer/MathPalette'

// ---- Chuyển đổi LaTeX → SymPy cho ô "Biểu thức kết quả" ----
// GV gõ hoặc bấm chọn công thức bằng math-field (giống hệt ô nhập kết quả của HS trong
// phòng học — dùng lại đúng FormulaEditor + MathPalette) — hiện đồng thời công thức Toán
// (để đối chiếu đã nhập đúng ý chưa) và cú pháp SymPy tương ứng để copy dán, khỏi cần nhớ
// cú pháp. Thay cho bảng tra cứu tĩnh trước đây.
export default function ChuyenDoiLatexSympy() {
  const [latex, setLatex] = useState('')
  const [sympy, setSympy] = useState('')
  const [loi, setLoi] = useState('')
  const [dangChuyenDoi, setDangChuyenDoi] = useState(false)
  const [daSaoChep, setDaSaoChep] = useState(false)
  const wrapRef = useRef(null)

  // Reset ngay khi ô trống — đặt ở nơi thay đổi latex (sự kiện người dùng), không phải
  // trong effect, để tránh setState đồng bộ ngay đầu effect (cascading render).
  function datLatex(v) {
    setLatex(v)
    if (!v.trim()) { setSympy(''); setLoi('') }
  }
  const getMf = () => wrapRef.current?.querySelector('math-field')
  const syncFromField = () => {
    const mf = getMf()
    if (mf) datLatex(mf.value)
  }

  // Bấm nút bảng công thức (vd "logₐ", "x^n") chèn cấu trúc còn Ô TRỐNG (\placeholder{})
  // GV chưa điền — gửi dịch ngay sẽ luôn lỗi khó hiểu. Phát hiện trước, cảnh báo nhẹ
  // nhàng thay vì gọi API rồi hiện lỗi kỹ thuật.
  const conOTrong = /\\placeholder\{\}/.test(latex)

  useEffect(() => {
    const bt = latex.trim()
    if (!bt || conOTrong) return
    let huy = false
    const timer = setTimeout(() => {
      setDangChuyenDoi(true)
      setLoi('')
      api.latexSangSympy(bt)
        .then((r) => { if (!huy) setSympy(r.sympy) })
        .catch((e) => { if (!huy) { setSympy(''); setLoi(e.message) } })
        .finally(() => { if (!huy) setDangChuyenDoi(false) })
    }, 500)
    return () => { huy = true; clearTimeout(timer) }
  }, [latex, conOTrong])

  function saoChep() {
    if (!sympy) return
    navigator.clipboard.writeText(sympy).then(() => {
      setDaSaoChep(true)
      setTimeout(() => setDaSaoChep(false), 1500)
    })
  }

  return (
    <div className="rounded-md border border-border bg-surface-2 p-2.5 flex flex-col gap-2">
      <p className="text-xs font-semibold text-ink">Chuyển công thức → cú pháp SymPy</p>
      <p className="text-[11px] text-muted">
        Gõ trực tiếp hoặc bấm chọn ở bảng bên dưới — tự dịch sang cú pháp cho ô
        "Biểu thức kết quả" (KHÔNG bọc $), khỏi cần nhớ cú pháp SymPy.
      </p>
      <div ref={wrapRef} className="relative">
        <FormulaEditor value={latex} onChange={datLatex} placeholder="Nhập công thức..." />
        {latex && (
          <button
            type="button"
            onClick={() => { const mf = getMf(); if (mf) mf.value = ''; datLatex('') }}
            title="Xóa"
            className="absolute right-2 top-1/2 -translate-y-1/2 h-5 w-5 flex items-center justify-center
              rounded-full bg-surface-2 text-muted hover:bg-danger-soft hover:text-danger transition-colors"
          >
            ✕
          </button>
        )}
      </div>
      {latex.trim() && (
        <>
          <div className="rounded-md bg-surface border border-border px-2.5 py-1.5">
            <p className="text-[10px] text-muted mb-0.5">Công thức Toán</p>
            <Formula latex={latex} />
          </div>
          <div className="rounded-md bg-surface border border-border px-2.5 py-1.5">
            <div className="flex items-center justify-between gap-2">
              <p className="text-[10px] text-muted">Cú pháp SymPy</p>
              {sympy && !dangChuyenDoi && !conOTrong && (
                <button type="button" onClick={saoChep} className="text-[10px] text-primary hover:underline">
                  {daSaoChep ? '✓ Đã sao chép' : 'Sao chép'}
                </button>
              )}
            </div>
            {conOTrong ? (
              <p className="text-xs text-warning">
                ⚠ Còn ô trống (□) chưa điền trong công thức — điền xong mới dịch được.
              </p>
            ) : dangChuyenDoi ? (
              <p className="text-xs text-muted">Đang dịch...</p>
            ) : loi ? (
              <p className="text-xs text-danger">Không dịch được: {loi}</p>
            ) : (
              <code className="text-sm font-mono text-primary">{sympy}</code>
            )}
          </div>
        </>
      )}
      <MathPalette getMf={getMf} onInserted={syncFromField} />
    </div>
  )
}
