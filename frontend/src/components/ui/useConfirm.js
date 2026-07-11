import { useContext } from 'react'
import { ConfirmContext } from './ConfirmContext'

export function useConfirm() {
  return useContext(ConfirmContext)
}
