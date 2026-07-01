import { useEffect, useRef, useState } from 'react'
import { api } from '../../api'
import { Button, Card, CardBody, ChatBubble, TypingBubble } from '../../components/ui'
import Formula from '../../components/Formula'
import AnswerInputTN4PA from '../../components/answer/AnswerInputTN4PA'
import AnswerInputTNDS from '../../components/answer/AnswerInputTNDS'
import AnswerInputTLN from '../../components/answer/AnswerInputTLN'
import { NHAN_LOAI_CAU, dinhDangThoiGian } from '../../utils/format'

function renderDeBai(text) {
  return String(text)
    .split(/(\$[^$]+\$)/g)
    .map((p, i) =>
      p.startsWith('$') ? <Formula key={i} latex={p.slice(1, -1)} /> : <span key={i}>{p}</span>
    )
}

function trangThaiYBanDau(meta) {
  const tt = {}
  ;(meta?.y || []).forEach((item, i) => {
    tt[item.ky_hieu] = i === 0 ? 'dang_lam' : 'chua'
  })
  return tt
}

function BangHoanThanh({ loai, thoi_gian, thoi_gian_y, dap_an_y, onChonBai, onTrangChu }) {
  return (
    <div className="rounded-lg border-2 border-success bg-success-soft p-4 text-center flex flex-col items-center gap-2">
      <div className="h-12 w-12 rounded-full bg-success text-white grid place-items-center text-2xl">
        ✓
      </div>
      <p className="text-lg font-semibold text-success">Trả lời đúng — Hoàn thành bài!</p>
      <p className="text-sm text-ink">
        Tổng thời gian làm bài: <b>{dinhDangThoiGian(thoi_gian)}</b>
      </p>
      {loai === 'TNDS' && thoi_gian_y && Object.keys(thoi_gian_y).length > 0 && (
        <table className="text-sm w-full max-w-sm border-collapse bg-surface rounded-md overflow-hidden">
          <thead>
            <tr className="bg-surface-2 text-muted text-xs">
              <th className="px-3 py-1.5 text-left font-medium border border-border">Ý</th>
              <th className="px-3 py-1.5 text-center font-medium border border-border">Đáp án đúng</th>
              <th className="px-3 py-1.5 text-right font-medium border border-border">Thời gian hoàn thành</th>
            </tr>
          </thead>
          <tbody>
            {['a', 'b', 'c', 'd'].map((k) => {
              const da = dap_an_y?.[k]
              return (
                <tr key={k}>
                  <td className="px-3 py-1.5 text-left border border-border">{k})</td>
                  <td className="px-3 py-1.5 text-center border border-border">
                    {da === 'Dung' ? (
                      <b className="text-success">Đ</b>
                    ) : da === 'Sai' ? (
                      <b className="text-danger">S</b>
                    ) : (
                      '—'
                    )}
                  </td>
                  <td className="px-3 py-1.5 text-right border border-border">
                    {thoi_gian_y[k] != null ? dinhDangThoiGian(thoi_gian_y[k]) : '—'}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      )}
      <div className="flex gap-2 mt-2">
        <Button onClick={onChonBai}>Chọn bài khác</Button>
        <Button variant="secondary" onClick={onTrangChu}>
          Về trang chủ
        </Button>
      </div>
    </div>
  )
}

// Card hiện thị bước hiện tại + mô tả (chỉ dùng cho TLN)
function CardBuoc({ buoc_hien_tai, tong_buoc, buoc_mo_ta }) {
  if (!buoc_mo_ta) return null
  return (
    <div className="rounded-lg border border-primary/30 bg-primary-soft px-4 py-3 mb-3">
      <p className="text-xs font-bold tracking-wide text-primary uppercase mb-1">
        Bước {buoc_hien_tai}{tong_buoc ? `/${tong_buoc}` : ''}
      </p>
      <p className="text-sm font-semibold text-ink leading-relaxed">
        {renderDeBai(buoc_mo_ta)}
      </p>
    </div>
  )
}

export default function PhongHoc({ problemId, sessionId, onTrangChu, onChonBai }) {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [problem, setProblem] = useState(null)
  const [sid, setSid] = useState(sessionId || null)
  const [turns, setTurns] = useState([])
  const [trangThai, setTrangThai] = useState({
    buoc_hien_tai: 1,
    y_hien_tai: null,
    trang_thai_y: {},
    da_xong: false,
    diem: null,
    so_y_dung: null,
    thoi_gian_giay: null,
    buoc_mo_ta: null,
    tong_buoc: null,
    cho_chon_dap_an: null,
    cho_chon_dung_sai: null,
    thoi_gian_y: null,
    dap_an_y: null,
  })
  const [dangGui, setDangGui] = useState(false)
  const chatRef = useRef(null)
  // Nhờ thầy/cô (A2)
  const [nhoMo, setNhoMo] = useState(false)
  const [nhoText, setNhoText] = useState('')
  const [nhoDangGui, setNhoDangGui] = useState(false)
  const [nhoOk, setNhoOk] = useState('')

  async function guiNhoThayCo() {
    if (!sid) return
    setNhoDangGui(true)
    try {
      await api.hsNhoThayCo(sid, nhoText.trim() || null)
      setNhoMo(false)
      setNhoText('')
      setNhoOk('Đã gửi yêu cầu tới thầy/cô. Em sẽ nhận được trả lời sớm nhé!')
      setTimeout(() => setNhoOk(''), 5000)
    } catch (e) {
      setError(e.message)
    } finally {
      setNhoDangGui(false)
    }
  }

  // Khởi tạo: làm tiếp (sessionId) hoặc bắt đầu mới (problemId).
  useEffect(() => {
    let huy = false
    async function init() {
      setLoading(true)
      setError('')
      try {
        if (sessionId) {
          const ct = await api.getSession(sessionId)
          if (huy) return
          setProblem({ loai_cau: ct.loai_cau, de_bai: ct.de_bai, meta: ct.meta, chuyen_de: ct.chuyen_de, dang_ten: ct.dang_ten })
          setSid(ct.session_id)
          setTurns(ct.turns.map((t) => ({ vai_tro: t.vai_tro, noi_dung: t.noi_dung })))
          setTrangThai({
            buoc_hien_tai: ct.buoc_hien_tai,
            y_hien_tai: ct.y_hien_tai,
            trang_thai_y: ct.trang_thai_y || trangThaiYBanDau(ct.meta),
            da_xong: ct.trang_thai === 'hoan_thanh',
            diem: ct.diem,
            so_y_dung: null,
            thoi_gian_giay: ct.thoi_gian_giay,
            buoc_mo_ta: ct.buoc_mo_ta ?? null,
            tong_buoc: ct.tong_buoc ?? null,
            cho_chon_dap_an: ct.cho_chon_dap_an ?? null,
            cho_chon_dung_sai: ct.cho_chon_dung_sai ?? null,
            thoi_gian_y: ct.thoi_gian_y ?? null,
            dap_an_y: ct.dap_an_y ?? null,
          })
        } else {
          const p = await api.getProblem(problemId)
          const phien = await api.createSession(problemId)
          if (huy) return
          setProblem({ loai_cau: p.loai_cau, de_bai: p.de_bai, meta: p.meta, chuyen_de: p.chuyen_de, dang_ten: p.dang_ten })
          setSid(phien.session_id)
          setTurns([{ vai_tro: 'gia_su', noi_dung: phien.van_ban }])
          setTrangThai({
            buoc_hien_tai: phien.buoc_hien_tai,
            y_hien_tai: phien.y_hien_tai,
            trang_thai_y: trangThaiYBanDau(p.meta),
            da_xong: false,
            diem: null,
            so_y_dung: null,
            thoi_gian_giay: null,
            buoc_mo_ta: phien.buoc_mo_ta ?? null,
            tong_buoc: phien.tong_buoc ?? null,
            cho_chon_dap_an: phien.cho_chon_dap_an ?? null,
            cho_chon_dung_sai: phien.cho_chon_dung_sai ?? null,
            thoi_gian_y: null,
            dap_an_y: null,
          })
        }
      } catch (e) {
        if (!huy) setError(e.message)
      } finally {
        if (!huy) setLoading(false)
      }
    }
    init()
    return () => {
      huy = true
    }
  }, [problemId, sessionId])

  // Cuộn xuống cuối khi có lượt mới
  useEffect(() => {
    chatRef.current?.scrollTo({ top: chatRef.current.scrollHeight, behavior: 'smooth' })
  }, [turns, dangGui])

  async function gui({ dap_an_nhap = null, noi_dung = '', yeu_cau_goi_y = false }) {
    if (dangGui || !sid) return
    setDangGui(true)
    setError('')

    const hsText = noi_dung || (dap_an_nhap != null ? `Em chọn: ${dap_an_nhap}` : '')
    if (hsText) setTurns((ts) => [...ts, { vai_tro: 'hoc_sinh', noi_dung: hsText }])

    const yTruoc = trangThai.y_hien_tai
    try {
      const res = await api.sendMessage(sid, { dap_an_nhap, noi_dung, yeu_cau_goi_y })
      setTurns((ts) => [...ts, { vai_tro: 'gia_su', noi_dung: res.van_ban }])
      setTrangThai((tt) => {
        const ttY = { ...tt.trang_thai_y }
        if (problem?.loai_cau === 'TNDS' && dap_an_nhap != null && yTruoc) {
          ttY[yTruoc] = 'xong'
          if (res.y_hien_tai && res.y_hien_tai !== yTruoc) ttY[res.y_hien_tai] = 'dang_lam'
        }
        return {
          buoc_hien_tai: res.buoc_hien_tai,
          y_hien_tai: res.y_hien_tai,
          trang_thai_y: ttY,
          da_xong: res.da_xong,
          diem: res.diem,
          so_y_dung: res.so_y_dung,
          thoi_gian_giay: res.thoi_gian_giay,
          buoc_mo_ta: res.buoc_mo_ta ?? tt.buoc_mo_ta,
          tong_buoc: res.tong_buoc ?? tt.tong_buoc,
          cho_chon_dap_an: res.cho_chon_dap_an ?? tt.cho_chon_dap_an,
          cho_chon_dung_sai: res.cho_chon_dung_sai ?? tt.cho_chon_dung_sai,
          thoi_gian_y: res.thoi_gian_y ?? tt.thoi_gian_y,
          dap_an_y: res.dap_an_y ?? tt.dap_an_y,
        }
      })
    } catch (e) {
      setError(e.message)
    } finally {
      setDangGui(false)
    }
  }

  if (loading) return <p className="text-muted text-sm">Đang vào phòng học...</p>
  if (error && !problem) {
    return (
      <div className="flex flex-col gap-3">
        <p className="text-danger text-sm bg-danger-soft rounded-md px-3 py-2">{error}</p>
        <Button variant="secondary" onClick={onChonBai}>
          Quay lại chọn bài
        </Button>
      </div>
    )
  }

  const daXong = trangThai.da_xong

  return (
    <div className="flex flex-col gap-4">
      <div>
        <button onClick={onChonBai} className="text-sm text-muted hover:text-ink mb-2">
          ← Chọn bài khác
        </button>
        <div className="rounded-lg border border-primary/20 bg-primary-soft px-4 py-3">
          <p className="text-base sm:text-lg font-bold text-primary mb-1.5">
            {problem.chuyen_de}
            {problem.dang_ten && <span className="text-ink"> › {problem.dang_ten}</span>}
          </p>
          <span className="inline-block text-xs font-bold tracking-wide text-primary bg-surface rounded px-2 py-0.5 mb-1.5">
            [{NHAN_LOAI_CAU[problem.loai_cau] || problem.loai_cau}]
          </span>
          <p className="text-base text-ink leading-relaxed">
            {renderDeBai(problem.de_bai)}
          </p>
          {problem.loai_cau === 'TN4PA' && problem.meta?.phuong_an && (
            <div className="mt-2 flex flex-wrap gap-x-6 gap-y-1">
              {Object.entries(problem.meta.phuong_an).map(([k, v]) => (
                <span key={k} className="text-sm text-ink leading-relaxed whitespace-nowrap">
                  <span className="font-semibold text-primary">{k}.</span> {renderDeBai(v)}
                </span>
              ))}
            </div>
          )}
          {problem.loai_cau === 'TNDS' && problem.meta?.y && (
            <div className="mt-2 flex flex-col gap-1">
              {problem.meta.y.map((item) => (
                <p key={item.ky_hieu} className="text-sm text-ink leading-relaxed">
                  <span className="font-semibold text-primary">{item.ky_hieu})</span>{' '}
                  {renderDeBai(item.noi_dung_y)}
                </p>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="grid lg:grid-cols-5 gap-4">
        {/* Khung hội thoại */}
        <Card className="lg:col-span-3">
          <CardBody className="flex flex-col gap-3 pt-5">
            <div ref={chatRef} className="flex flex-col gap-3 overflow-y-auto max-h-[48vh] min-h-[180px] pr-1">
              {turns.map((t, i) => (
                <ChatBubble key={i} vai_tro={t.vai_tro} text={t.noi_dung} />
              ))}
              {dangGui && <TypingBubble />}
            </div>
            {nhoOk && (
              <div className="rounded-lg bg-success-soft text-success text-sm px-3 py-2 text-center">
                ✓ {nhoOk}
              </div>
            )}
            <div className="border-t border-border pt-2 flex flex-wrap justify-center gap-2">
              <Button
                variant="warning"
                disabled={dangGui || daXong}
                onClick={() => gui({ noi_dung: 'Xin thầy/cô gợi ý thêm cho em', yeu_cau_goi_y: true })}
              >
                💡 GỢI Ý CHO EM
              </Button>
              <Button variant="secondary" disabled={!sid} onClick={() => setNhoMo(true)}>
                🙋 NHỜ THẦY/CÔ
              </Button>
              <Button variant="primary" onClick={onChonBai}>
                ↩ QUAY LẠI LÀM SAU
              </Button>
            </div>
          </CardBody>
        </Card>

        {nhoMo && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
            <div className="bg-white rounded-xl shadow-xl w-full max-w-md flex flex-col">
              <div className="px-5 pt-5 pb-3 border-b border-border">
                <h2 className="font-bold text-lg text-ink">Nhờ thầy/cô giúp đỡ</h2>
                <p className="text-sm text-muted mt-0.5">
                  Thầy/cô sẽ thấy em đang bí ở bước này và trả lời ngay trong bài.
                </p>
              </div>
              <div className="px-5 py-4">
                <textarea
                  value={nhoText}
                  onChange={(e) => setNhoText(e.target.value)}
                  rows={4}
                  placeholder="Em có thể mô tả chỗ chưa hiểu (không bắt buộc)..."
                  className="w-full rounded-lg border border-border px-3 py-2 text-sm text-ink
                    focus:outline-none focus:ring-2 focus:ring-primary/40 resize-y"
                />
              </div>
              <div className="px-5 py-4 border-t border-border flex gap-2 justify-end">
                <Button variant="secondary" onClick={() => setNhoMo(false)} disabled={nhoDangGui}>
                  Hủy
                </Button>
                <Button onClick={guiNhoThayCo} disabled={nhoDangGui}>
                  {nhoDangGui ? 'Đang gửi...' : 'Gửi yêu cầu'}
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* Vùng trả lời / banner hoàn thành */}
        <Card className="lg:col-span-2">
          <CardBody className="pt-5">
            {daXong ? (
              <BangHoanThanh
                loai={problem.loai_cau}
                thoi_gian={trangThai.thoi_gian_giay}
                thoi_gian_y={trangThai.thoi_gian_y}
                dap_an_y={trangThai.dap_an_y}
                onChonBai={onChonBai}
                onTrangChu={onTrangChu}
              />
            ) : (
              <>
                {problem.loai_cau === 'TN4PA' && (
                  trangThai.cho_chon_dap_an === false ? (
                    // Pha suy luận: HS nhập biểu thức kết quả của bước (CAS chấm)
                    <>
                      <CardBuoc
                        buoc_hien_tai={trangThai.buoc_hien_tai}
                        tong_buoc={trangThai.tong_buoc}
                        buoc_mo_ta={trangThai.buoc_mo_ta}
                      />
                      <p className="text-sm font-medium text-ink mb-3">Tính kết quả của bước này</p>
                      <AnswerInputTLN onGui={gui} dang_gui={dangGui} />
                    </>
                  ) : (
                    // Pha chọn đáp án: A/B/C/D đã mở khóa
                    <>
                      <p className="text-sm font-medium text-ink mb-3">Câu trả lời của em</p>
                      <AnswerInputTN4PA phuong_an={problem.meta?.phuong_an} onGui={gui} dang_gui={dangGui} />
                    </>
                  )
                )}
                {problem.loai_cau === 'TNDS' && (
                  <>
                    <p className="text-sm font-medium text-ink mb-3">Câu trả lời của em</p>
                    <AnswerInputTNDS
                      y={problem.meta?.y}
                      y_hien_tai={trangThai.y_hien_tai}
                      trang_thai_y={trangThai.trang_thai_y}
                      cho_chon={trangThai.cho_chon_dung_sai}
                      buoc_mo_ta={trangThai.buoc_mo_ta}
                      onGui={gui}
                      dang_gui={dangGui}
                    />
                  </>
                )}
                {problem.loai_cau === 'TLN' && (
                  <>
                    <CardBuoc
                      buoc_hien_tai={trangThai.buoc_hien_tai}
                      tong_buoc={trangThai.tong_buoc}
                      buoc_mo_ta={trangThai.buoc_mo_ta}
                    />
                    <p className="text-sm font-medium text-ink mb-3">Câu trả lời của em</p>
                    <AnswerInputTLN onGui={gui} dang_gui={dangGui} />
                  </>
                )}

                {error && (
                  <p className="text-sm text-warning bg-warning-soft rounded-md px-3 py-2 mt-3">{error}</p>
                )}
              </>
            )}
          </CardBody>
        </Card>
      </div>
    </div>
  )
}
