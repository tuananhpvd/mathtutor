import { useState } from 'react'
import { api } from '../../api'
import { Button } from '../ui'

export default function GuiNhanXetModal({ hsId, hoTen, onClose, onSent }) {
  const [noiDung, setNoiDung] = useState('')
  const [dangGui, setDangGui] = useState(false)
  const [dangNhap, setDangNhap] = useState(false)
  const [loi, setLoi] = useState('')

  async function goiYAi() {
    setLoi('')
    setDangNhap(true)
    try {
      const r = await api.gvNhanXetNhap(hsId)
      setNoiDung(r.noi_dung || '')
    } catch (e) {
      setLoi(e.message)
    } finally {
      setDangNhap(false)
    }
  }

  async function gui() {
    const nd = noiDung.trim()
    if (!nd) { setLoi('Nội dung nhận xét không được để trống'); return }
    setLoi('')
    setDangGui(true)
    try {
      await api.gvGuiNhanXet(hsId, nd)
      onSent?.(`Đã gửi nhận xét cho ${hoTen}`)
    } catch (e) {
      setLoi(e.message)
      setDangGui(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="bg-surface rounded-xl shadow-xl w-full max-w-lg max-h-[88vh] flex flex-col">
        <div className="px-5 pt-5 pb-3 border-b border-border shrink-0">
          <h2 className="font-bold text-lg text-ink">Gửi nhận xét cho {hoTen}</h2>
          <p className="text-sm text-muted mt-0.5">
            Lời nhắn sẽ hiện trên Trang chủ của học sinh kèm thông báo.
          </p>
        </div>

        <div className="px-5 py-4 flex flex-col gap-3 overflow-y-auto flex-1">
          <div className="flex items-center justify-between">
            <label className="text-sm font-medium text-ink">Nội dung nhận xét</label>
            <Button size="sm" variant="secondary" onClick={goiYAi} disabled={dangNhap || dangGui}>
              {dangNhap ? 'Đang lấy gợi ý...' : '✨ AI gợi ý'}
            </Button>
          </div>
          <textarea
            value={noiDung}
            onChange={(e) => setNoiDung(e.target.value)}
            rows={6}
            placeholder="Viết lời nhận xét / động viên cho học sinh. Bấm 'AI gợi ý' để có sẵn bản nháp rồi chỉnh sửa."
            className="w-full rounded-lg border border-border px-3 py-2 text-sm text-ink
              focus:outline-none focus:ring-2 focus:ring-primary/40 resize-y"
          />
          {loi && <p className="text-sm text-danger">{loi}</p>}
        </div>

        <div className="px-5 py-4 border-t border-border flex gap-2 justify-end shrink-0">
          <Button variant="secondary" onClick={onClose} disabled={dangGui}>Hủy</Button>
          <Button onClick={gui} disabled={dangGui || !noiDung.trim()}>
            {dangGui ? 'Đang gửi...' : 'Gửi nhận xét'}
          </Button>
        </div>
      </div>
    </div>
  )
}
