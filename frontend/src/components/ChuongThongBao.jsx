import { useEffect, useRef, useState } from 'react'
import { api } from '../api'

const NHAN_LOAI = {
  nhan_xet: 'Nhận xét của thầy/cô',
  co: 'Nhắc nhở',
  nhiem_vu: 'Nhiệm vụ mới',
  tra_loi: 'Thầy/cô trả lời',
  he_thong: 'Thông báo',
}

function thoiGianGon(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  const giay = Math.floor((Date.now() - d.getTime()) / 1000)
  if (giay < 60) return 'vừa xong'
  if (giay < 3600) return `${Math.floor(giay / 60)} phút trước`
  if (giay < 86400) return `${Math.floor(giay / 3600)} giờ trước`
  if (giay < 604800) return `${Math.floor(giay / 86400)} ngày trước`
  return d.toLocaleDateString('vi-VN')
}

export default function ChuongThongBao() {
  const [mo, setMo] = useState(false)
  const [soChuaDoc, setSoChuaDoc] = useState(0)
  const [ds, setDs] = useState([])
  const [dangTai, setDangTai] = useState(false)
  const ref = useRef(null)

  function taiSo() {
    api.thongBaoChuaDoc().then((r) => setSoChuaDoc(r.so_luong || 0)).catch(() => {})
  }

  // Đếm chưa đọc khi mở app + định kỳ mỗi 60s.
  useEffect(() => {
    taiSo()
    const id = setInterval(taiSo, 60000)
    return () => clearInterval(id)
  }, [])

  // Đóng dropdown khi click ra ngoài.
  useEffect(() => {
    function onClick(e) {
      if (ref.current && !ref.current.contains(e.target)) setMo(false)
    }
    document.addEventListener('mousedown', onClick)
    return () => document.removeEventListener('mousedown', onClick)
  }, [])

  function moDropdown() {
    const sapMo = !mo
    setMo(sapMo)
    if (sapMo) {
      setDangTai(true)
      api.thongBao()
        .then((rows) => setDs(rows || []))
        .catch(() => {})
        .finally(() => setDangTai(false))
    }
  }

  async function docHet() {
    try {
      await api.thongBaoDocHet()
      setDs((cur) => cur.map((t) => ({ ...t, da_doc: true })))
      setSoChuaDoc(0)
    } catch { /* bỏ qua */ }
  }

  async function danhDau(tb) {
    if (tb.da_doc) return
    try {
      await api.thongBaoDaDoc(tb.id)
      setDs((cur) => cur.map((t) => (t.id === tb.id ? { ...t, da_doc: true } : t)))
      setSoChuaDoc((n) => Math.max(0, n - 1))
    } catch { /* bỏ qua */ }
  }

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={moDropdown}
        className="relative rounded-md p-2 text-muted hover:text-ink hover:bg-surface-2 transition-colors"
        title="Thông báo"
        aria-label="Thông báo"
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor"
          strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
          <path d="M13.73 21a2 2 0 0 1-3.46 0" />
        </svg>
        {soChuaDoc > 0 && (
          <span className="absolute -top-0.5 -right-0.5 min-w-[18px] h-[18px] px-1 rounded-full
            bg-danger text-white text-[10px] font-bold grid place-items-center">
            {soChuaDoc > 99 ? '99+' : soChuaDoc}
          </span>
        )}
      </button>

      {mo && (
        <div className="absolute right-0 mt-2 w-80 max-w-[90vw] bg-surface rounded-xl shadow-xl
          border border-border z-50 overflow-hidden">
          <div className="flex items-center justify-between px-4 py-2.5 border-b border-border">
            <span className="font-semibold text-ink text-sm">Thông báo</span>
            {soChuaDoc > 0 && (
              <button onClick={docHet} className="text-xs text-primary hover:underline">
                Đánh dấu đã đọc tất cả
              </button>
            )}
          </div>
          <div className="max-h-96 overflow-y-auto">
            {dangTai ? (
              <p className="text-sm text-muted px-4 py-6 text-center">Đang tải...</p>
            ) : ds.length === 0 ? (
              <p className="text-sm text-muted px-4 py-6 text-center">Chưa có thông báo nào.</p>
            ) : (
              ds.map((tb) => (
                <button
                  key={tb.id}
                  onClick={() => danhDau(tb)}
                  className={`w-full text-left px-4 py-3 border-b border-border last:border-0
                    hover:bg-surface-2 transition-colors ${tb.da_doc ? '' : 'bg-primary-soft/40'}`}
                >
                  <div className="flex items-center gap-2">
                    {!tb.da_doc && <span className="h-2 w-2 rounded-full bg-primary shrink-0" />}
                    <span className="text-xs font-semibold text-primary">
                      {tb.tieu_de || NHAN_LOAI[tb.loai] || 'Thông báo'}
                    </span>
                    <span className="text-[11px] text-muted ml-auto shrink-0">
                      {thoiGianGon(tb.tao_luc)}
                    </span>
                  </div>
                  <p className="text-sm text-ink mt-1 whitespace-pre-wrap break-words">{tb.noi_dung}</p>
                  {tb.nguoi_gui_ten && (
                    <p className="text-[11px] text-muted mt-1">— {tb.nguoi_gui_ten}</p>
                  )}
                </button>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  )
}
