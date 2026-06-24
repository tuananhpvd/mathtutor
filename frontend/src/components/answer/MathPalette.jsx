/*
 * Palette công thức — chèn ký hiệu toán vào math-field theo nhóm.
 * getMf: hàm trả về phần tử <math-field>; onInserted: callback đồng bộ giá trị.
 */
export default function MathPalette({ getMf, onInserted }) {
  function ins(latex) {
    const mf = getMf()
    if (!mf) return
    mf.focus()
    if (typeof mf.insert === 'function') mf.insert(latex, { focus: true })
    else mf.executeCommand?.(['insert', latex])
    onInserted?.()
  }
  function cmd(name) {
    const mf = getMf()
    if (!mf) return
    mf.focus()
    mf.executeCommand?.(name)
    onInserted?.()
  }
  function clear() {
    const mf = getMf()
    if (mf) mf.value = ''
    onInserted?.()
  }

  const sections = [
    {
      title: 'Số & phép tính',
      cols: 6,
      keys: [
        { label: '7', run: () => ins('7') },
        { label: '8', run: () => ins('8') },
        { label: '9', run: () => ins('9') },
        { label: '÷', run: () => ins('\\div') },
        { label: '( )', run: () => ins('(\\placeholder{})') },
        { label: '[ ]', run: () => ins('[\\placeholder{}]') },
        { label: '4', run: () => ins('4') },
        { label: '5', run: () => ins('5') },
        { label: '6', run: () => ins('6') },
        { label: '×', run: () => ins('\\times') },
        { label: '√', run: () => ins('\\sqrt{\\placeholder{}}') },
        { label: '∛', run: () => ins('\\sqrt[3]{\\placeholder{}}') },
        { label: '1', run: () => ins('1') },
        { label: '2', run: () => ins('2') },
        { label: '3', run: () => ins('3') },
        { label: '−', run: () => ins('-') },
        { label: 'x²', run: () => ins('^{2}') },
        { label: 'x³', run: () => ins('^{3}') },
        { label: '0', run: () => ins('0') },
        { label: '.', run: () => ins('.') },
        { label: '±', run: () => ins('\\pm') },
        { label: '+', run: () => ins('+') },
        { label: 'a/b', run: () => ins('\\frac{\\placeholder{}}{\\placeholder{}}') },
        { label: 'xⁿ', run: () => ins('^{\\placeholder{}}') },
      ],
    },
    {
      title: 'Hàm & hằng số',
      cols: 6,
      keys: [
        { label: 'sin', run: () => ins('\\sin(\\placeholder{})') },
        { label: 'cos', run: () => ins('\\cos(\\placeholder{})') },
        { label: 'tan', run: () => ins('\\tan(\\placeholder{})') },
        { label: 'cot', run: () => ins('\\cot(\\placeholder{})') },
        { label: 'log', run: () => ins('\\log(\\placeholder{})') },
        { label: 'ln', run: () => ins('\\ln(\\placeholder{})') },
        { label: 'sin²', run: () => ins('\\sin^{2}(\\placeholder{})') },
        { label: 'cos²', run: () => ins('\\cos^{2}(\\placeholder{})') },
        { label: '|x|', run: () => ins('\\left|\\placeholder{}\\right|') },
        { label: 'π', run: () => ins('\\pi') },
        { label: 'e', run: () => ins('e') },
        { label: '∞', run: () => ins('\\infty') },
      ],
    },
    {
      title: 'Giải tích',
      cols: 6,
      keys: [
        { label: 'lim', run: () => ins('\\lim_{\\placeholder{} \\to \\placeholder{}} \\placeholder{}') },
        { label: 'lim→∞', run: () => ins('\\lim_{x \\to \\infty} \\placeholder{}') },
        { label: '∫dx', run: () => ins('\\int \\placeholder{} \\, dx') },
        { label: '∫_a^b', run: () => ins('\\int_{\\placeholder{}}^{\\placeholder{}} \\placeholder{} \\, dx') },
        { label: 'Σ', run: () => ins('\\sum_{k=\\placeholder{}}^{\\placeholder{}} \\placeholder{}') },
        { label: 'd/dx', run: () => ins('\\frac{d}{dx}(\\placeholder{})') },
        { label: 'logₐ', run: () => ins('\\log_{\\placeholder{}}(\\placeholder{})') },
        { label: 'eˣ', run: () => ins('e^{\\placeholder{}}') },
        { label: 'aˣ', run: () => ins('a^{\\placeholder{}}') },
        { label: "f'", run: () => ins("f'(\\placeholder{})") },
        { label: "f''", run: () => ins("f''(\\placeholder{})") },
        { label: 'F(x)', run: () => ins('F(\\placeholder{})') },
      ],
    },
    {
      title: 'Ký hiệu',
      cols: 6,
      keys: [
        { label: '≤', run: () => ins('\\le') },
        { label: '≥', run: () => ins('\\ge') },
        { label: '≠', run: () => ins('\\ne') },
        { label: '≈', run: () => ins('\\approx') },
        { label: '°', run: () => ins('^{\\circ}') },
        { label: '!', run: () => ins('!') },
        { label: 'x', run: () => ins('x') },
        { label: 'y', run: () => ins('y') },
        { label: 'n', run: () => ins('n') },
        { label: 'k', run: () => ins('k') },
        { label: '⌫', run: () => cmd('deleteBackward') },
        { label: 'Xóa', run: clear, danger: true },
      ],
    },
  ]

  return (
    <div className="rounded-md border border-border bg-surface-2 p-2 flex flex-col gap-2">
      {sections.map((sec) => (
        <div key={sec.title}>
          <p className="text-[10px] text-muted uppercase tracking-wide mb-1">{sec.title}</p>
          <div
            className="grid gap-1"
            style={{ gridTemplateColumns: `repeat(${sec.cols}, minmax(0, 1fr))` }}
          >
            {sec.keys.map((k, i) => (
              <button
                key={i}
                type="button"
                onClick={k.run}
                className={`rounded border border-border bg-surface py-1.5 text-sm font-bold hover:bg-primary-soft
                  hover:border-primary transition-colors ${k.danger ? 'text-danger' : 'text-ink'}`}
              >
                {k.label}
              </button>
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}
