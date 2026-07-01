import { useEffect, useState } from 'react'
import { api } from '../../api'
import { Badge, Button, Card, CardBody, CardHeader, useConfirm } from '../../components/ui'
import Formula from '../../components/Formula'
import MixedChatInput from '../../components/MixedChatInput'

const TRANG_KT = 10

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

function thoiGian(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleString('vi-VN')
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

export default function HoTroHocSinh() {
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

  function tai() {
    setLoading(true)
    api.gvTroGiup()
      .then((rows) => setDs(rows || []))
      .catch(() => {})
      .finally(() => setLoading(false))
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
      setOk(`Đã trả lời ${yc.hoc_sinh_ten}. Câu trả lời đã hiện trong bài của học sinh.`)
      setTimeout(() => setOk(''), 4000)
      tai()
    } catch (e) {
      setLoi(e.message)
    } finally {
      setDangGui(false)
    }
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

  const tongTrangCho = Math.max(1, Math.ceil(choXuLy.length / TRANG_KT))
  const tongTrangDa = Math.max(1, Math.ceil(daTraLoi.length / TRANG_KT))
  const choHienThi = choXuLy.slice((trangCho - 1) * TRANG_KT, trangCho * TRANG_KT)
  const daHienThi = daTraLoi.slice((trangDa - 1) * TRANG_KT, trangDa * TRANG_KT)

  function CardYeuCau({ yc, tone }) {
    const borderClass = tone === 'warning'
      ? 'border-warning/40 bg-warning-soft/40'
      : 'border-border'
    return (
      <div key={yc.id} className={`rounded-xl border ${borderClass} px-4 py-3`}>
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="font-semibold text-ink">{yc.hoc_sinh_ten}</span>
              {tone === 'done' && <Badge tone="success">Đã trả lời</Badge>}
              <span className="text-xs text-muted">{thoiGian(yc.tao_luc)}</span>
            </div>
            <NganCanh yc={yc} />
          </div>
          <Button
            size="sm" variant="danger-ghost"
            disabled={dangXoa === yc.id}
            onClick={() => xoa(yc)}
          >
            {dangXoa === yc.id ? '...' : 'Xóa'}
          </Button>
        </div>

        {/* Đề bài đầy đủ + phương án / ý */}
        {yc.de_bai && (
          <div className="mt-2 rounded-lg bg-surface border border-border px-3 py-2 text-sm text-ink space-y-1">
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
          <p className="text-sm text-ink mt-2 italic">
            <span className="font-medium not-italic">Học sinh hỏi: </span>
            "{renderNoiDung(yc.noi_dung)}"
          </p>
        )}

        {/* Câu trả lời của GV (mục Đã trả lời) */}
        {yc.tra_loi && (
          <p className="text-sm text-ink mt-1.5">
            <span className="font-medium text-gv">Trả lời: </span>
            {renderNoiDung(yc.tra_loi)}
          </p>
        )}

        {/* Form trả lời (mục Chờ xử lý) */}
        {tone === 'warning' && (
          traLoiId === yc.id ? (
            <div className="mt-3 flex flex-col gap-2">
              <MixedChatInput
                value={text}
                onChange={setText}
                placeholder="Viết câu trả lời / gợi ý cho học sinh... (có thể chèn công thức)"
                rows={3}
              />
              {loi && <p className="text-sm text-danger">{loi}</p>}
              <div className="flex gap-2 justify-end">
                <Button size="sm" variant="secondary"
                  onClick={() => setTraLoiId(null)} disabled={dangGui}>Hủy</Button>
                <Button size="sm" onClick={() => gui(yc)} disabled={dangGui}>
                  {dangGui ? 'Đang gửi...' : 'Gửi trả lời'}
                </Button>
              </div>
            </div>
          ) : (
            <div className="mt-2">
              <Button size="sm" onClick={() => moTraLoi(yc)}>Trả lời</Button>
            </div>
          )
        )}
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-4">
      {ok && (
        <div className="rounded-lg bg-success-soft text-success text-sm px-4 py-2.5">✓ {ok}</div>
      )}
      {loi && !traLoiId && (
        <div className="rounded-lg bg-danger-soft text-danger text-sm px-4 py-2.5">{loi}</div>
      )}

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
                <CardYeuCau key={yc.id} yc={yc} tone="warning" />
              ))}
              <PhanTrang trang={trangCho} tongTrang={tongTrangCho} onChange={setTrangCho} />
            </>
          )}
        </CardBody>
      </Card>

      {daTraLoi.length > 0 && (
        <Card>
          <CardHeader title="Đã trả lời" subtitle={`${daTraLoi.length} yêu cầu`} />
          <CardBody className="flex flex-col gap-3">
            {daHienThi.map((yc) => (
              <CardYeuCau key={yc.id} yc={yc} tone="done" />
            ))}
            <PhanTrang trang={trangDa} tongTrang={tongTrangDa} onChange={setTrangDa} />
          </CardBody>
        </Card>
      )}
    </div>
  )
}
