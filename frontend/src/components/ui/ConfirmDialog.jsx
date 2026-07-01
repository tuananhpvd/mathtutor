import { createContext, useCallback, useContext, useRef, useState } from 'react'
import Button from './Button'

const ConfirmContext = createContext(null)

export function ConfirmProvider({ children }) {
  const [state, setState] = useState(null)
  const resolveRef = useRef(null)

  const confirm = useCallback((message, { title = 'Xác nhận' } = {}) => {
    return new Promise((resolve) => {
      resolveRef.current = resolve
      setState({ message, title })
    })
  }, [])

  function handle(ok) {
    setState(null)
    const res = resolveRef.current
    resolveRef.current = null
    res?.(ok)
  }

  return (
    <ConfirmContext.Provider value={confirm}>
      {children}
      {state && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center"
          style={{ background: 'rgba(0,0,0,0.45)' }}
          onMouseDown={(e) => { if (e.target === e.currentTarget) handle(false) }}
        >
          <div className="bg-surface rounded-xl shadow-2xl p-6 max-w-sm w-full mx-4 border border-border">
            <p className="font-semibold text-ink text-base mb-2">{state.title}</p>
            <p className="text-ink-2 text-sm whitespace-pre-line mb-6">{state.message}</p>
            <div className="flex justify-end gap-2">
              <Button variant="secondary" onClick={() => handle(false)}>Hủy</Button>
              <Button variant="primary" onClick={() => handle(true)}>OK</Button>
            </div>
          </div>
        </div>
      )}
    </ConfirmContext.Provider>
  )
}

export function useConfirm() {
  return useContext(ConfirmContext)
}
