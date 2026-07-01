import { useEffect, useState } from 'react'
import { api } from '../../api'
import { Badge, Button, Card, CardBody, CardHeader } from '../../components/ui'
import Formula from '../../components/Formula'
import MixedChatInput from '../../components/MixedChatInput'

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

export default function HoTroHocSinh() {
  const [ds, setDs] = useState([])
  const [loading, setLoading] = useState(true)
  const [traLoiId, setTraLoiId] = useState(null)
  const [text, setText] = useState('')
  const [dangGui, setDangGui] = useState(false)
  const [ok, setOk] = useState('')
  const [loi, setLoi] = useState('')

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

  const choXuLy = ds.filter((y) => y.trang_thai === 'cho_xu_ly')
  const daTraLoi = ds.filter((y) => y.trang_thai === 'da_tra_loi')

  return (
    <div className="flex flex-col gap-4">
      {ok && (
        <div className="rounded-lg bg-success-soft text-success text-sm px-4 py-2.5">✓ {ok}</div>
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
            choXuLy.map((yc) => (
              <div key={yc.id} className="rounded-xl border border-warning/40 bg-warning-soft/40 px-4 py-3">
                <div className="flex items-center justify-between gap-2">
                  <span className="font-semibold text-ink">{yc.hoc_sinh_ten}</span>
                  <span className="text-xs text-muted">{thoiGian(yc.tao_luc)}</span>
                </div>
                <NganCanh yc={yc} />
                {yc.noi_dung && (
                  <p className="text-sm text-ink mt-2 italic">
                    "{renderNoiDung(yc.noi_dung)}"
                  </p>
                )}
                {traLoiId === yc.id ? (
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
                )}
              </div>
            ))
          )}
        </CardBody>
      </Card>

      {daTraLoi.length > 0 && (
        <Card>
          <CardHeader title="Đã trả lời" subtitle={`${daTraLoi.length} yêu cầu`} />
          <CardBody className="flex flex-col gap-3">
            {daTraLoi.map((yc) => (
              <div key={yc.id} className="rounded-xl border border-border px-4 py-3">
                <div className="flex items-center justify-between gap-2">
                  <span className="font-semibold text-ink">{yc.hoc_sinh_ten}</span>
                  <Badge tone="success">Đã trả lời</Badge>
                </div>
                <NganCanh yc={yc} />
                {yc.noi_dung && (
                  <p className="text-sm text-muted mt-1.5 italic">
                    "{renderNoiDung(yc.noi_dung)}"
                  </p>
                )}
                {yc.tra_loi && (
                  <p className="text-sm text-ink mt-1.5">
                    <span className="font-medium text-gv">Trả lời: </span>
                    {renderNoiDung(yc.tra_loi)}
                  </p>
                )}
              </div>
            ))}
          </CardBody>
        </Card>
      )}
    </div>
  )
}
