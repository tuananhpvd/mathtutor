import { useEffect, useState } from 'react'
import { api } from '../../api'
import { Badge, Button, Card, CardBody, CardHeader, ChatBubble, useConfirm } from '../../components/ui'
import Formula from '../../components/Formula'
import MixedChatInput from '../../components/MixedChatInput'
import ThoiGianPhanCach from '../../components/ThoiGianPhanCach'

const TRANG_KT = 5

function renderNoiDung(text) {
  if (!text) return null
  return String(text)
    .split(/(\$[^$]+\$)/g)
    .map((p, i) =>
      p.startsWith('$') && p.endsWith('$') ? (
        <Formula key={i} latex={p.slice(1, -1)} />
      ) : (
        <span key={i}>{p}</span>
      )
    )
}


function NganCanh({ yc }) {
  const parts = []
  if (yc.buoc) parts.push(`Bước ${yc.buoc}`)
  if (yc.y) parts.push(`ý ${yc.y}`)
  return (
    <p className="text-xs text-muted">
      {yc.bai}
      {parts.length > 0 ? ` · ${parts.join(', ')}` : ''}
    </p>
  )
}

function PhanTrang({ trang, tongTrang, onChange }) {
  if (tongTrang <= 1) return null
  return (
    <div className="flex items-center justify-center gap-2 pt-2">
      <Button size="sm" variant="secondary" disabled={trang === 1} onClick={() => onChange(trang - 1)}>
        ‹
      </Button>
      <span className="text-xs text-muted">{trang} / {tongTrang}</span>
      <Button size="sm" variant="secondary" disabled={trang === tongTrang} onClick={() => onChange(trang + 1)}>
        ›
      </Button>
    </div>
  )
}

// Popup "Xem chi tiết": toàn bộ khung chat từ đầu đến lúc HS nhờ + câu trả lời của GV (nếu
// có) nối cuối — để GV hiểu HS đã làm gì trước khi trả lời trợ giúp. Nút "Trả lời" nằm ngay
// trong popup (trước "Đóng") — GV buộc phải xem qua chi tiết mới trả lời được, đúng mục
// đích ban đầu của tính năng này.
function ModalChiTiet({
  yc, du_lieu, loading, loiTai, onDong,
  traLoiId, text, setText, loi, dangGui, onMoTraLoi, onGui,
}) {
  const dangTraLoi = traLoiId === yc.id
  return (
    <div className="fixed inset-0 z-40 bg-black/40 overflow-y-auto flex items-start justify-center p-4">
      <Card className="max-w-2xl w-full my-8">
        <CardBody className="flex flex-col gap-3 pt-5">
          <div className="flex items-center justify-between gap-2">
            <div>
              <p className="font-bold text-ink">Chi tiết yêu cầu trợ giúp</p>
              <p className="text-xs text-muted mt-0.5">{yc.hoc_sinh_ten} · {yc.bai}</p>
            </div>
            <div className="flex items-center gap-1.5 shrink-0">
              {yc.trang_thai === 'cho_xu_ly' && !dangTraLoi && (
                <Button size="sm" onClick={() => onMoTraLoi(yc)}>Trả lời</Button>
              )}
              <Button size="sm" variant="secondary" onClick={onDong} disabled={dangGui}>
                Đóng ✕
              </Button>
            </div>
          </div>

          {loiTai && (
            <p className="text-sm text-danger bg-danger-soft rounded-md px-3 py-2">{loiTai}</p>
          )}
          {loading && <p className="text-sm text-muted">Đang tải...</p>}

          {du_lieu && (
            <>
              {du_lieu.de_bai && (
                <div className="rounded-lg bg-primary-soft/40 border border-primary/20 px-3 py-2 text-sm text-ink space-y-1">
                  <div>{renderNoiDung(du_lieu.de_bai)}</div>
                  {du_lieu.loai_cau === 'TN4PA' && du_lieu.meta_hien_thi?.phuong_an &&
                    Object.entries(du_lieu.meta_hien_thi.phuong_an).map(([k, v]) => (
                      <div key={k} className="flex gap-1.5">
                        <span className="font-medium shrink-0">{k}.</span>
                        <span>{renderNoiDung(v)}</span>
                      </div>
                    ))
                  }
                  {du_lieu.loai_cau === 'TNDS' && du_lieu.meta_hien_thi?.y?.map((item) => (
                    <div key={item.ky_hieu} className="flex gap-1.5">
                      <span className="font-medium shrink-0">{item.ky_hieu})</span>
                      <span>{renderNoiDung(item.noi_dung_y)}</span>
                    </div>
                  ))}
                </div>
              )}

              <p className="text-xs font-bold text-muted uppercase tracking-wide mt-1">
                Khung chat của học sinh (đến lúc nhờ thầy/cô)
              </p>
              <div className="flex flex-col gap-3 max-h-[50vh] overflow-y-auto pr-1">
                {du_lieu.turns.length === 0 ? (
                  <p className="text-sm text-muted">Chưa có lượt trò chuyện nào.</p>
                ) : (
                  du_lieu.turns.map((t, i) => (
                    <ChatBubble key={i} vai_tro={t.vai_tro} text={t.noi_dung} />
                  ))
                )}
              </div>

              {dangTraLoi && (
                <div className="border-t border-border pt-3 flex flex-col gap-2">
                  <MixedChatInput
                    value={text}
                    onChange={setText}
                    placeholder="Viết câu trả lời / gợi ý cho học sinh... (có thể chèn công thức)"
                    rows={3}
                  />
                  {loi && <p className="text-sm text-danger">{loi}</p>}
                  <div className="flex gap-2 justify-end">
                    <Button size="sm" onClick={() => onGui(yc)} disabled={dangGui}>
                      {dangGui ? 'Đang gửi...' : 'Gửi trả lời'}
                    </Button>
                  </div>
                </div>
              )}
            </>
          )}
        </CardBody>
      </Card>
    </div>
  )
}

// Tách hẳn khỏi render của HoTroHocSinh (KHÔNG định nghĩa trong thân hàm component cha) —
// nếu không, mỗi lần gõ vào ô trả lời (setText đổi state cha) sẽ khiến CardYeuCau bị coi là
// 1 KIỂU COMPONENT MỚI ở mỗi lần render, React unmount/remount lại toàn bộ cây con bên trong
// (kể cả <textarea> của MixedChatInput) — mất focus, chỉ gõ được đúng 1 ký tự rồi bật ra.
function CardYeuCau({ yc, tone, dangXoa, onXoa, onXemChiTiet, noiBat }) {
  const borderClass = tone === 'warning'
    ? 'border-warning/40 bg-warning-soft/40'
    : 'border-border'
  return (
    <div
      id={`yc-tro-giup-${yc.id}`}
      className={`rounded-xl border px-4 py-3 transition-shadow ${
        noiBat ? 'border-primary ring-2 ring-primary' : borderClass
      }`}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-1 flex-wrap text-sm">
            <span className="font-semibold text-ink">{yc.hoc_sinh_ten}</span>
            {tone === 'done' && <Badge tone="success">Đã trả lời</Badge>}
            <ThoiGianPhanCach iso={yc.tao_luc} />
          </div>
          <NganCanh yc={yc} />
        </div>
        <div className="flex items-center gap-1.5 shrink-0">
          <Button size="sm" variant="secondary" onClick={() => onXemChiTiet(yc)}>
            Xem chi tiết
          </Button>
          <Button
            size="sm" variant="danger-ghost"
            disabled={dangXoa === yc.id}
            onClick={() => onXoa(yc)}
          >
            {dangXoa === yc.id ? '...' : 'Xóa'}
          </Button>
        </div>
      </div>

      {/* Đề bài đầy đủ + phương án / ý */}
      {yc.de_bai && (
        <div className="mt-2 rounded-lg bg-primary-soft/40 border border-primary/20 px-3 py-2 text-sm text-ink space-y-1">
          <div>{renderNoiDung(yc.de_bai)}</div>
          {yc.loai_cau === 'TN4PA' && yc.meta_hien_thi?.phuong_an &&
            Object.entries(yc.meta_hien_thi.phuong_an).map(([k, v]) => (
              <div key={k} className="flex gap-1.5">
                <span className="font-medium shrink-0">{k}.</span>
                <span>{renderNoiDung(v)}</span>
              </div>
            ))
          }
          {yc.loai_cau === 'TNDS' && yc.meta_hien_thi?.y?.map((item) => (
            <div key={item.ky_hieu} className="flex gap-1.5">
              <span className="font-medium shrink-0">{item.ky_hieu})</span>
              <span>{renderNoiDung(item.noi_dung_y)}</span>
            </div>
          ))}
        </div>
      )}

      {/* Câu hỏi của học sinh */}
      {yc.noi_dung && (
        <div className="mt-2 rounded-lg bg-warning-soft border border-warning/30 px-3 py-2 text-sm text-ink">
          <span className="font-medium text-warning">Học sinh hỏi: </span>
          <span className="italic">"{renderNoiDung(yc.noi_dung)}"</span>
        </div>
      )}

      {/* Câu trả lời của GV (mục Đã trả lời) */}
      {yc.tra_loi && (
        <div className="mt-2 rounded-lg bg-success-soft border border-success/30 px-3 py-2 text-sm text-ink">
          <span className="font-medium text-success">Trả lời: </span>
          {renderNoiDung(yc.tra_loi)}
        </div>
      )}

    </div>
  )
}

// focusYc: { id, ts } | null — GV bấm thông báo "Học sinh nhờ trợ giúp" ở chuông thông báo,
// cần nhảy tới đúng yêu cầu đó (kể cả phải đổi trang phân trang) rồi làm nổi bật tạm thời.
// "ts" đổi mỗi lần bấm để ép hiệu ứng chạy lại kể cả bấm trùng đúng yêu cầu đã focus trước đó.
export default function HoTroHocSinh({ focusYc, onFocusDone }) {
  const confirm = useConfirm()
  const [ds, setDs] = useState([])
  const [loading, setLoading] = useState(true)
  const [traLoiId, setTraLoiId] = useState(null)
  const [text, setText] = useState('')
  const [dangGui, setDangGui] = useState(false)
  const [ok, setOk] = useState('')
  const [loi, setLoi] = useState('')
  const [dangXoa, setDangXoa] = useState(null)
  const [trangCho, setTrangCho] = useState(1)
  const [trangDa, setTrangDa] = useState(1)
  const [noiBatId, setNoiBatId] = useState(null)
  // Popup "Xem chi tiết" — chứa luôn nút/form "Trả lời" (yc = yêu cầu đang xem, để biết
  // trạng thái + hiển thị đúng tên HS ngay cả lúc du_lieu chưa tải xong).
  const [chiTiet, setChiTiet] = useState(null) // {yc, du_lieu, loading, loiTai} | null

  function tai() {
    setTimeout(() => {
      setLoading(true)
      api.gvTroGiup()
        .then((rows) => setDs(rows || []))
        .catch(() => {})
        .finally(() => setLoading(false))
    }, 0)
  }
  useEffect(tai, [])

  function moTraLoi(yc) {
    setTraLoiId(yc.id)
    setText('')
    setLoi('')
  }

  async function gui(yc) {
    const nd = text.trim()
    if (!nd) { setLoi('Nội dung trả lời không được để trống'); return }
    setDangGui(true)
    setLoi('')
    try {
      await api.gvTraLoiTroGiup(yc.id, nd)
      setTraLoiId(null)
      setText('')
      setChiTiet(null)  // trả lời xong → đóng popup, danh sách tự cập nhật bên dưới
      setOk(`Đã trả lời ${yc.hoc_sinh_ten}. Câu trả lời đã hiện trong bài của học sinh.`)
      setTimeout(() => setOk(''), 4000)
      tai()
    } catch (e) {
      setLoi(e.message)
    } finally {
      setDangGui(false)
    }
  }

  async function xemChiTiet(yc) {
    setChiTiet({ yc, du_lieu: null, loading: true, loiTai: '' })
    try {
      const d = await api.gvChiTietTroGiup(yc.id)
      setChiTiet({ yc, du_lieu: d, loading: false, loiTai: '' })
    } catch (e) {
      setChiTiet({ yc, du_lieu: null, loading: false, loiTai: e.message })
    }
  }

  function dongChiTiet() {
    setChiTiet(null)
    setTraLoiId(null)
    setText('')
    setLoi('')
  }

  async function xoa(yc) {
    if (!await confirm(`Xóa yêu cầu trợ giúp của ${yc.hoc_sinh_ten}?`)) return
    setDangXoa(yc.id)
    try {
      await api.gvXoaTroGiup(yc.id)
      tai()
    } catch (e) {
      setOk('')
      setLoi(e.message)
    } finally {
      setDangXoa(null)
    }
  }

  const choXuLy = ds.filter((y) => y.trang_thai === 'cho_xu_ly')
  const daTraLoi = ds.filter((y) => y.trang_thai === 'da_tra_loi')

  // Nhảy tới + làm nổi bật đúng yêu cầu khi được yêu cầu focus từ chuông thông báo — đợi
  // danh sách tải xong (loading=false) rồi mới tìm, tránh tìm hụt lúc ds còn rỗng.
  useEffect(() => {
    if (!focusYc || loading) return
    let cuonTimeout, tatNoiBat
    const batDau = setTimeout(() => {
      const idxCho = choXuLy.findIndex((y) => y.id === focusYc.id)
      const idxDa = idxCho < 0 ? daTraLoi.findIndex((y) => y.id === focusYc.id) : -1
      if (idxCho >= 0) setTrangCho(Math.floor(idxCho / TRANG_KT) + 1)
      else if (idxDa >= 0) setTrangDa(Math.floor(idxDa / TRANG_KT) + 1)
      else { onFocusDone?.(); return }  // không còn tồn tại (vd đã bị xóa) — bỏ qua

      setNoiBatId(focusYc.id)
      cuonTimeout = setTimeout(() => {
        document.getElementById(`yc-tro-giup-${focusYc.id}`)
          ?.scrollIntoView({ behavior: 'smooth', block: 'center' })
      }, 150)
      tatNoiBat = setTimeout(() => setNoiBatId(null), 3000)
      onFocusDone?.()
    }, 0)
    return () => {
      clearTimeout(batDau)
      clearTimeout(cuonTimeout)
      clearTimeout(tatNoiBat)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [focusYc, loading, ds])

  const tongTrangCho = Math.max(1, Math.ceil(choXuLy.length / TRANG_KT))
  const tongTrangDa = Math.max(1, Math.ceil(daTraLoi.length / TRANG_KT))
  const choHienThi = choXuLy.slice((trangCho - 1) * TRANG_KT, trangCho * TRANG_KT)
  const daHienThi = daTraLoi.slice((trangDa - 1) * TRANG_KT, trangDa * TRANG_KT)

  return (
    <div className="flex flex-col gap-4">
      {ok && (
        <div className="rounded-lg bg-success-soft text-success text-sm px-4 py-2.5">✓ {ok}</div>
      )}
      {loi && !traLoiId && (
        <div className="rounded-lg bg-danger-soft text-danger text-sm px-4 py-2.5">{loi}</div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 items-start">
        <Card>
          <CardHeader title="Yêu cầu cần trả lời"
            subtitle={`${choXuLy.length} học sinh đang chờ thầy/cô giúp`} />
          <CardBody className="flex flex-col gap-3">
            {loading ? (
              <p className="text-sm text-muted">Đang tải...</p>
            ) : choXuLy.length === 0 ? (
              <p className="text-sm text-muted">Không có yêu cầu nào đang chờ. 👍</p>
            ) : (
              <>
                {choHienThi.map((yc) => (
                  <CardYeuCau
                    key={yc.id} yc={yc} tone="warning"
                    dangXoa={dangXoa} onXoa={xoa} onXemChiTiet={xemChiTiet}
                    noiBat={noiBatId === yc.id}
                  />
                ))}
                <PhanTrang trang={trangCho} tongTrang={tongTrangCho} onChange={setTrangCho} />
              </>
            )}
          </CardBody>
        </Card>

        <Card>
          <CardHeader title="Đã trả lời" subtitle={`${daTraLoi.length} yêu cầu`} />
          <CardBody className="flex flex-col gap-3">
            {loading ? (
              <p className="text-sm text-muted">Đang tải...</p>
            ) : daTraLoi.length === 0 ? (
              <p className="text-sm text-muted">Chưa có yêu cầu nào được trả lời.</p>
            ) : (
              <>
                {daHienThi.map((yc) => (
                  <CardYeuCau
                    key={yc.id} yc={yc} tone="done" dangXoa={dangXoa} onXoa={xoa}
                    onXemChiTiet={xemChiTiet}
                    noiBat={noiBatId === yc.id}
                  />
                ))}
                <PhanTrang trang={trangDa} tongTrang={tongTrangDa} onChange={setTrangDa} />
              </>
            )}
          </CardBody>
        </Card>
      </div>

      {chiTiet && (
        <ModalChiTiet
          yc={chiTiet.yc} du_lieu={chiTiet.du_lieu} loading={chiTiet.loading}
          loiTai={chiTiet.loiTai} onDong={dongChiTiet}
          traLoiId={traLoiId} text={text} setText={setText} loi={loi} dangGui={dangGui}
          onMoTraLoi={moTraLoi} onGui={gui}
        />
      )}
    </div>
  )
}
