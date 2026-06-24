import { useEffect, useRef } from 'react'
import katex from 'katex'
import 'katex/dist/katex.min.css'

export default function Formula({ latex, block = false }) {
  const ref = useRef(null)

  useEffect(() => {
    if (!ref.current) return
    try {
      katex.render(latex || '', ref.current, {
        displayMode: block,
        throwOnError: false,
        output: 'html',
      })
    } catch {
      ref.current.textContent = latex
    }
  }, [latex, block])

  return <span ref={ref} className={block ? 'block overflow-x-auto py-1' : 'inline'} />
}
