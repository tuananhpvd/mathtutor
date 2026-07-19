import { useEffect, useRef, useState } from 'react'
import { api } from '../../api'
import { Button, Card, CardBody, ChatBubble, TypingBubble } from '../../components/ui'
import Formula from '../../components/Formula'
import HuongDanPhongHoc from '../../components/HuongDanPhongHoc'
import MixedChatInput from '../../components/MixedChatInput'
import NoiDungLyThuyet from '../../components/NoiDungLyThuyet'
import XemLaiBai from '../../components/XemLaiBai'
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

function BangHoanThanh({
  loai, thoi_gian, thoi_gian_y, dap_an_y, so_lan_khong_hieu, tong_so_lan_sai,
  onChonBai, onTrangChu, onXemLai,
}) {
  const khongCanGoiY = !so_lan_khong_hieu && !tong_so_lan_sai
  return (
    <div className="rounded-lg border-2 border-success bg-success-soft p-4 text-center flex flex-col items-center gap-2">
      <div className="h-12 w-12 rounded-full bg-success text-white grid place-items-center text-2xl">
        ✓
      </div>
      <p className="text-lg font-semibold text-success">Trả lời đúng — Hoàn thành bài!</p>
      <p className="text-sm text-ink">
        Tổng thời gian làm bài: <b>{dinhDangThoiGian(thoi_gian)}</b>
      </p>
      <p className="text-sm text-ink">
        {khongCanGoiY ? (
          <>Em tự làm hoàn toàn không cần gợi ý — quá xuất sắc! 🌟</>
        ) : (
          <>
            Hành trình của em: dùng <b>{so_lan_khong_hieu || 0}</b> lượt xin gợi ý, thử lại{' '}
            <b>{tong_so_lan_sai || 0}</b> lần trước khi ra đúng kết quả. Cứ tiếp tục kiên trì
            như vậy nhé!
          </>
        )}
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
      <div className="flex gap-2 mt-2 flex-wrap justify-center">
        <Button onClick={onXemLai}>📖 Xem lại bài</Button>
        <Button variant="secondary" onClick={onChonBai}>Chọn bài khác</Button>
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

// Khay đáp án — biến hình theo loại câu & pha mở khóa (tái dùng 3 component nhập đáp án).
// Đây là vùng "bài làm được máy chấm" (dap_an_nhap), tách khỏi ô trò chuyện (noi_dung).
function KhayDapAn({ problem, trangThai, gui, dangGui }) {
  const loai = problem.loai_cau
  return (
    <div className="rounded-xl border border-primary/40 bg-primary-soft/40 p-3">
      <p className="text-[11px] font-bold uppercase tracking-wide text-primary mb-2">
        Khu vực trả lời
      </p>
      {loai === 'TN4PA' && (
        trangThai.cho_chon_dap_an === false ? (
          // Pha suy luận: HS nhập biểu thức kết quả của bước (CAS chấm) trước khi mở A–D
          <>
            <div className="rounded-lg border border-primary/30 bg-primary-soft/60 px-3 py-2 mb-3 text-sm text-ink">
              🔒 Các phương án A–D sẽ <b>mở khóa</b> ngay khi em tính đúng bước này —
              làm đúng để chọn được đáp án nhé!
            </div>
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
      {loai === 'TNDS' && (
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
      {loai === 'TLN' && (
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
    </div>
  )
}

export default function PhongHoc({ problemId, sessionId, onTrangChu, onChonBai, onSid }) {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [problem, setProblem] = useState(null)
  const [sid, setSid] = useState(sessionId || null)

  // Báo cho HocSinhApp biết session ĐANG active trong phòng học này (kể cả khi mở bài mới
  // chưa có sessionId ban đầu, chỉ biết sau khi tạo phiên) — để chuông thông báo xác định
  // đúng "HS có đang ở sẵn đúng bài đó không" khi bấm vào 1 thông báo trả lời.
  useEffect(() => {
    onSid?.(sid)
    return () => onSid?.(null)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sid])
  const [turns, setTurns] = useState([])
  const [xemLaiMo, setXemLaiMo] = useState(false)
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
    cap_goi_y: 0,
    so_goi_y_toi_da: null,
    so_lan_khong_hieu: 0,
    tong_so_lan_sai: 0,
  })
  const [dangGui, setDangGui] = useState(false)
  const [zoomHinh, setZoomHinh] = useState(null)
  const [hienHuongDan, setHienHuongDan] = useState(false)
  const chatRef = useRef(null)
  // Hỏi tự do (chat với gia sư — không kèm đáp án): câu hỏi khái niệm, "vì sao", bối rối...
  const [cauHoi, setCauHoi] = useState('')
  const cauHoiRef = useRef(null)
  // Nhờ thầy/cô (A2)
  const [nhoMo, setNhoMo] = useState(false)
  const [nhoText, setNhoText] = useState('')
  const [nhoDangGui, setNhoDangGui] = useState(false)
  const [nhoOk, setNhoOk] = useState('')
  // Xem lại lý thuyết (khi hết gợi ý) — popup đúng dạng/chuyên đề HS đang làm.
  const [lyThuyetMo, setLyThuyetMo] = useState(false)
  const [lyThuyetDs, setLyThuyetDs] = useState(null)
  const [lyThuyetError, setLyThuyetError] = useState('')

  async function moLyThuyet() {
    setLyThuyetMo(true)
    setLyThuyetDs(null)
    setLyThuyetError('')
    // Đánh dấu HS tự tìm lại lý thuyết khi bí (tín hiệu chẩn đoán cho GV) — best-effort,
    // không chặn mở popup nếu lỗi.
    if (sid) api.danhDauXemLyThuyet(sid).catch(() => {})
    try {
      let ds = problem.dang_id
        ? await api.hsLyThuyetDs(problem.chuyen_de_id, problem.dang_id)
        : []
      if (ds.length === 0 && problem.chuyen_de_id) {
        ds = await api.hsLyThuyetDs(problem.chuyen_de_id)
      }
      setLyThuyetDs(ds)
    } catch (e) {
      setLyThuyetError(e.message)
    }
  }

  async function guiNhoThayCo() {
    if (!sid) return
    setNhoDangGui(true)
    const nd = nhoText.trim()
    try {
      await api.hsNhoThayCo(sid, nd || null)
      setNhoMo(false)
      setNhoText('')
      // Hiện nội dung nhờ vào khung chat
      const chatNd = nd ? `🙋 Nhờ thầy/cô: ${nd}` : '🙋 Em cần thầy/cô giúp đỡ ở bước này.'
      setTurns((ts) => [...ts, { vai_tro: 'hoc_sinh', noi_dung: chatNd }])
      setNhoOk('Đã gửi yêu cầu tới thầy/cô. Em sẽ nhận được trả lời sớm nhé!')
      setTimeout(() => setNhoOk(''), 5000)
    } catch (e) {
      setError(e.message)
    } finally {
      setNhoDangGui(false)
    }
  }

  // Áp state phòng học từ chi tiết phiên đầy đủ (ChiTietPhienResponse) — dùng chung cho cả
  // "làm tiếp" lẫn "bắt đầu mới", vì backend giờ có thể TRẢ LẠI 1 phiên dang_lam có sẵn thay
  // vì luôn tạo phiên mới (tránh trùng bài ở "Bài đang làm dở") — phiên trả lại đó có thể đã
  // có nhiều lượt hội thoại từ trước, nên PHẢI tải đủ turns qua GET /sessions/{id}, không chỉ
  // dùng 1 dòng "lời chào" như trước (sẽ làm mất lịch sử đã làm dở).
  function apDungChiTietPhien(ct) {
    setProblem({ loai_cau: ct.loai_cau, de_bai: ct.de_bai, hinh_anh: ct.hinh_anh, meta: ct.meta, chuyen_de: ct.chuyen_de, chuyen_de_id: ct.chuyen_de_id, dang_id: ct.dang_id, dang_ten: ct.dang_ten })
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
      cap_goi_y: ct.cap_goi_y_hien_tai ?? 0,
      so_goi_y_toi_da: ct.so_goi_y_toi_da ?? null,
      so_lan_khong_hieu: ct.so_lan_khong_hieu ?? 0,
      tong_so_lan_sai: ct.tong_so_lan_sai ?? 0,
    })
  }

  // Khởi tạo: làm tiếp (sessionId) hoặc bắt đầu mới (problemId).
  useEffect(() => {
    let huy = false
    async function init() {
      setLoading(true)
      setError('')
      try {
        // "Bắt đầu mới" thực chất có thể trả lại 1 phiên dang_lam có sẵn (backend tránh tạo
        // trùng) — nên sau khi có session_id, luôn tải chi tiết đầy đủ giống hệt "làm tiếp".
        const sid_ = sessionId || (await api.createSession(problemId)).session_id
        const ct = await api.getSession(sid_)
        if (huy) return
        apDungChiTietPhien(ct)
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
          cap_goi_y: res.cap_goi_y ?? tt.cap_goi_y,
          so_goi_y_toi_da: res.so_goi_y_toi_da ?? tt.so_goi_y_toi_da,
          so_lan_khong_hieu: res.so_lan_khong_hieu ?? tt.so_lan_khong_hieu,
          tong_so_lan_sai: res.tong_so_lan_sai ?? tt.tong_so_lan_sai,
        }
      })
    } catch (e) {
      setError(e.message)
    } finally {
      setDangGui(false)
    }
  }

  function guiCauHoi() {
    const nd = cauHoi.trim()
    if (!nd || dangGui) return
    setCauHoi('')
    gui({ noi_dung: nd })
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
  // Hết thang gợi ý của bước/ý hiện tại → nút "Gợi ý" đổi thành mời Nhờ thầy/cô.
  const hetGoiY = trangThai.so_goi_y_toi_da != null &&
    trangThai.cap_goi_y >= trangThai.so_goi_y_toi_da - 1

  return (
    <div className="flex flex-col gap-4">
      <HuongDanPhongHoc open={hienHuongDan} onClose={() => setHienHuongDan(false)} />
      {zoomHinh && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 cursor-zoom-out"
          onClick={() => setZoomHinh(null)}
        >
          <img src={zoomHinh} alt="Hình minh họa" className="max-h-[90vh] max-w-full rounded-lg" />
        </div>
      )}
      <div>
        <div className="flex gap-2 mb-2">
          <Button onClick={onChonBai} variant="secondary" size="sm"
            className="bg-warning-soft border-warning/20 shadow-[var(--shadow-card)]">
            ← Chọn bài khác
          </Button>
          <Button onClick={() => setHienHuongDan(true)} variant="secondary" size="sm"
            className="bg-cta-soft border-cta/20 shadow-[var(--shadow-card)]">
            📖 Hướng dẫn
          </Button>
        </div>
        <div className="rounded-lg border border-primary/20 bg-primary-soft px-4 py-3">
          <p className="text-base sm:text-lg font-bold text-primary mb-1.5">
            {problem.chuyen_de}
            {problem.dang_ten && <span className="text-ink"> › {problem.dang_ten}</span>}
          </p>
          {/* Có hình → 2 cột (đề trái, hình phải); không hình → 1 cột như cũ. Mobile tự xếp dọc. */}
          <div className={problem.hinh_anh ? 'grid grid-cols-1 md:grid-cols-2 gap-4 items-start' : ''}>
            <div>
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
            {problem.hinh_anh && (
              <div className="flex justify-center md:justify-end">
                <img
                  src={problem.hinh_anh}
                  alt="Hình minh họa"
                  className="max-h-80 max-w-full rounded-md border border-border bg-surface cursor-zoom-in"
                  onClick={() => setZoomHinh(problem.hinh_anh)}
                />
              </div>
            )}
          </div>
        </div>
      </div>

      <Card>
        <CardBody className="flex flex-col gap-3 pt-5">
            <div ref={chatRef} className="flex flex-col gap-3 overflow-y-auto max-h-[48vh] min-h-[180px] rounded-lg border border-border bg-surface-2/30 p-3">
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
            {daXong ? (
              <BangHoanThanh
                loai={problem.loai_cau}
                thoi_gian={trangThai.thoi_gian_giay}
                thoi_gian_y={trangThai.thoi_gian_y}
                dap_an_y={trangThai.dap_an_y}
                so_lan_khong_hieu={trangThai.so_lan_khong_hieu}
                tong_so_lan_sai={trangThai.tong_so_lan_sai}
                onChonBai={onChonBai}
                onTrangChu={onTrangChu}
                onXemLai={() => setXemLaiMo(true)}
              />
            ) : (
              <div className="border-t border-border pt-3 flex flex-col gap-3">
                {/* Nhắc khi hết gợi ý — thay cho khối 3 nút cũ; các lối tắt đã có sẵn trong khối */}
                {hetGoiY && (
                  <div className="rounded-lg border border-warning/30 bg-warning-soft px-3 py-2 text-sm text-ink text-center">
                    Em đã dùng hết gợi ý cho bước này — thử <b>📖 xem lý thuyết</b> hoặc{' '}
                    <b>🙋 nhờ thầy/cô</b> bên dưới nhé. Em vẫn có thể hỏi gia sư hoặc thử nộp đáp án.
                  </div>
                )}

                {/* Hàng thao tác: gợi ý · nhờ thầy/cô · (lý thuyết khi hết gợi ý) · quay lại — nằm TRÊN khu vực trả lời */}
                <div className="flex flex-wrap justify-center gap-2">
                  <Button
                    variant={hetGoiY ? 'warningSoft' : 'warning'}
                    disabled={dangGui || daXong || hetGoiY}
                    onClick={() => gui({ noi_dung: 'Xin thầy/cô gợi ý thêm cho em', yeu_cau_goi_y: true })}
                  >
                    {hetGoiY
                      ? '💡 Đã dùng hết gợi ý'
                      : trangThai.so_goi_y_toi_da != null
                        ? `💡 GỢI Ý CHO EM (${Math.min(trangThai.cap_goi_y + 1, trangThai.so_goi_y_toi_da)}/${trangThai.so_goi_y_toi_da})`
                        : '💡 GỢI Ý CHO EM'}
                  </Button>
                  <Button
                    variant={hetGoiY ? 'warning' : 'secondary'}
                    disabled={!sid}
                    className={hetGoiY ? 'ring-2 ring-warning animate-pulse' : ''}
                    onClick={() => { setNhoMo((v) => !v); setNhoText('') }}
                  >
                    🙋 NHỜ THẦY/CÔ
                  </Button>
                  {hetGoiY && (
                    <Button variant="success" onClick={moLyThuyet}>
                      📖 XEM LÝ THUYẾT
                    </Button>
                  )}
                  <Button variant="indigo" onClick={onChonBai}>
                    ↩ QUAY LẠI LÀM SAU
                  </Button>
                </div>

                {/* Nhờ thầy/cô — inline ngay trong khối (không còn modal toàn màn) */}
                {nhoMo && (
                  <div className="rounded-xl border border-secondary/40 bg-secondary/5 p-3 flex flex-col gap-2">
                    <div>
                      <p className="font-semibold text-sm text-ink">🙋 Nhờ thầy/cô giúp đỡ</p>
                      <p className="text-xs text-muted mt-0.5">
                        Thầy/cô sẽ thấy em đang bí ở bước này và trả lời ngay trong khung chat.
                        Em có thể mô tả bằng chữ hoặc chèn công thức toán.
                      </p>
                    </div>
                    <MixedChatInput
                      value={nhoText}
                      onChange={setNhoText}
                      placeholder="Mô tả chỗ chưa hiểu (không bắt buộc)..."
                      rows={2}
                      luonHienBangCT={false}
                    />
                    <div className="flex gap-2 justify-end">
                      <Button size="sm" variant="secondary"
                        onClick={() => { setNhoMo(false); setNhoText('') }} disabled={nhoDangGui}>
                        Hủy
                      </Button>
                      <Button size="sm" onClick={guiNhoThayCo} disabled={nhoDangGui}>
                        {nhoDangGui ? 'Đang gửi...' : 'Gửi yêu cầu'}
                      </Button>
                    </div>
                  </div>
                )}

                {error && (
                  <p className="text-sm text-warning bg-warning-soft rounded-md px-3 py-2">{error}</p>
                )}

                {/* 2 cột: KHU VỰC TRẢ LỜI (trái, máy chấm) · TRÒ CHUYỆN với gia sư (phải, phụ) */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 items-start">
                  <KhayDapAn problem={problem} trangThai={trangThai} gui={gui} dangGui={dangGui} />

                  <div className="rounded-xl border border-[#2596be]/40 bg-success-soft/30 p-3">
                    <p className="text-[11px] font-bold uppercase tracking-wide text-success mb-1.5">
                      Trò chuyện với gia sư
                    </p>
                    <MixedChatInput
                      ref={cauHoiRef}
                      value={cauHoi}
                      onChange={setCauHoi}
                      placeholder="Có chỗ nào chưa rõ, hỏi ở đây (vd: vì sao lại làm vậy ạ?)... — bấm vào ô để nhập công thức"
                      rows={2}
                      luonHienBangCT={false}
                      textareaClassName="bg-surface border border-[#2596be]"
                      duoiO={
                        <Button size="sm" variant="indigo" className="w-full"
                          disabled={dangGui || !cauHoi.trim()} onClick={guiCauHoi}>
                          Gửi câu hỏi
                        </Button>
                      }
                    />
                  </div>
                </div>
              </div>
            )}
          </CardBody>
        </Card>

      {xemLaiMo && sid && <XemLaiBai sessionId={sid} onDong={() => setXemLaiMo(false)} />}

      {lyThuyetMo && (
        <div className="fixed inset-0 z-40 bg-black/40 overflow-y-auto flex items-start justify-center p-4">
          <Card className="max-w-2xl w-full my-8">
            <CardBody className="flex flex-col gap-3 pt-5">
              <div className="flex items-center justify-between gap-2">
                <p className="font-bold text-ink">📖 Xem lại lý thuyết</p>
                <Button size="sm" variant="secondary" onClick={() => setLyThuyetMo(false)}>
                  Đóng ✕
                </Button>
              </div>
              {lyThuyetError && (
                <p className="text-sm text-danger bg-danger-soft rounded-md px-3 py-2">{lyThuyetError}</p>
              )}
              {!lyThuyetDs && !lyThuyetError && (
                <p className="text-sm text-muted">Đang tải...</p>
              )}
              {lyThuyetDs && lyThuyetDs.length === 0 && (
                <p className="text-sm text-muted text-center py-6">
                  Thầy/cô chưa soạn tóm tắt lý thuyết cho phần này.
                </p>
              )}
              {lyThuyetDs && lyThuyetDs.length > 0 && (
                <div className="flex flex-col gap-4">
                  {lyThuyetDs.map((tt) => (
                    <div key={tt.id} className="border-t border-border pt-3 first:border-t-0 first:pt-0">
                      <p className="font-semibold text-ink">{tt.tieu_de}</p>
                      <p className="text-xs text-muted mb-2">
                        {tt.chuyen_de_ten}{tt.dang_ten && <> › {tt.dang_ten}</>}
                      </p>
                      <NoiDungLyThuyet noiDung={tt.noi_dung} />
                    </div>
                  ))}
                </div>
              )}
            </CardBody>
          </Card>
        </div>
      )}
    </div>
  )
}
