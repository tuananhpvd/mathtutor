import { createContext } from 'react'

// Tách riêng khỏi ConfirmDialog.jsx (component) và useConfirm.js (hook) — 1 file chỉ export
// component thì Fast Refresh mới hoạt động đúng khi sửa code lúc dev.
export const ConfirmContext = createContext(null)
