/*
 * XemLaiBai — overlay toàn màn hình xem lại bài (B3, mở rộng GV ở v162):
 * lời giải chuẩn từng bước + đáp án đúng + hành trình hội thoại + thống kê.
 * Dùng chung cho HS (bắt buộc phiên đã hoàn thành) và GV/Admin (xem được cả phiên đang
 * làm dở) — prop `vaiTro` ('hs' | 'gv') chỉ đổi NHÃN hiển thị, backend mới là nơi chốt
 * chặn quyền và các trường dữ liệu nhạy cảm (component này không tự quyết định quyền).
 */

import { useEffect, useState } from 'react'
import { AlertTriangle, BookOpen, Lightbulb, X } from 'lucide-react'
import { api } from '../api'
import { Badge, Button, Card, CardBody, CardHeader, ChatBubble } from './ui'
import Formula from './Formula'
import { dinhDangThoiGian } from '../utils/format'
import { dungDongChat } from '../utils/dongChat'

function renderVanBan(text) {
  return String(text ?? '')
    .split(/(\$[^$]+\$)/g)
    .map((p, i) =>
      p.startsWith('$') ? <Formula key={i} latex={p.slice(1, -1)} /> : <span key={i}>{p}</span>
    )
}

// Nhãn lệch theo vai trò người xem — HS xưng "em", GV/Admin xem hộ nên đổi giọng. Gom hết
// vào 1 bảng để không rải if/else khắp JSX.
const NHAN = {
  hs: {
    tieuDe: () => 'Xem lại bài',
    hanhTrinh: 'Hành trình của em',
    loiGiaiSub: 'Các bước thầy/cô đã soạn - em đối chiếu với cách làm của mình nhé',
    tuLam: 'Tự làm không cần gợi ý',
  },
  gv: {
    tieuDe: (ten) => `Xem lại bài của ${ten || 'học sinh'}`,
    hanhTrinh: 'Hành trình làm bài',
    loiGiaiSub: 'Lời giải chuẩn đã soạn cho bài này',
    tuLam: 'Tự làm, không dùng gợi ý',
  },
}

// Dải phân cách bước — cùng kiểu dáng với khung chat Phòng học (PhongHoc.jsx), dùng lại ở
// đây để lịch sử xem lại cũng có "mốc chương hồi" khi bài nhiều bước.
function PhanCachBuoc({ nhan, moTa }) {
  return (
    <div className="flex items-center gap-2 py-1" role="separator">
      <span className="h-px flex-1 bg-border" />
      <span className="shrink-0 rounded-full bg-primary-soft px-3 py-1 text-center">
        <span className="text-[11px] font-bold uppercase tracking-wide text-primary">{nhan}</span>
        {moTa && <span className="text-xs text-ink"> · {renderVanBan(moTa)}</span>}
      </span>
      <span className="h-px flex-1 bg-border" />
    </div>
  )
}

function DapAnChuan({ loai_cau, dap_an }) {
  if (loai_cau === 'TN4PA') {
    return (
      <p className="text-sm text-ink">
        Đáp án đúng: <b className="text-success text-base">{dap_an.dap_an_dung}</b>
      </p>
    )
  }
  if (loai_cau === 'TNDS') {
    return (
      <div className="flex items-center gap-3 flex-wrap text-sm">
        <span className="text-ink">Đáp án đúng:</span>
        {['a', 'b', 'c', 'd'].map((k) => {
          const da = dap_an.dap_an_y?.[k]
          if (!da) return null
          return (
            <span key={k} className="text-ink">
              {k}) <b className={da === 'Dung' ? 'text-success' : 'text-danger'}>
                {da === 'Dung' ? 'Đ' : 'S'}
              </b>
            </span>
          )
        })}
      </div>
    )
  }
  return (
    <p className="text-sm text-ink">
      Đáp án: <b className="text-success text-base">{dap_an.dap_an_cuoi}</b>
      {dap_an.don_vi ? <span className="text-muted"> ({dap_an.don_vi})</span> : null}
    </p>
  )
}

export default function XemLaiBai({ sessionId, onDong, vaiTro = 'hs' }) {
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  const nhan = NHAN[vaiTro] || NHAN.hs

  useEffect(() => {
    let con = true
    setTimeout(() => {
      if (!con) return
      setData(null)
      setError('')
      api.xemLaiPhien(sessionId).then((d) => con && setData(d)).catch((e) => con && setError(e.message))
    }, 0)
    return () => {
      con = false
    }
  }, [sessionId])

  const tk = data?.thong_ke

  return (
    <div className="fixed inset-0 z-40 bg-black/40 overflow-y-auto">
      <div className="mx-auto w-full max-w-3xl min-h-full bg-bg p-4 sm:p-6 flex flex-col gap-4">
        <div className="flex items-center justify-between gap-3 flex-wrap">
          <h2 className="text-lg font-semibold text-ink inline-flex items-center gap-2">
            <BookOpen size={18} strokeWidth={2.2} />
            {nhan.tieuDe(data?.hoc_sinh_ten)}
            {data && data.trang_thai !== 'hoan_thanh' && (
              <Badge tone="warning">
                <AlertTriangle size={12} strokeWidth={2.4} /> Đang làm dở
              </Badge>
            )}
          </h2>
          <Button variant="secondary" onClick={onDong}>
            Đóng <X size={14} strokeWidth={2.4} />
          </Button>
        </div>

        {error && (
          <p className="text-sm text-danger bg-danger-soft rounded-md px-3 py-2">{error}</p>
        )}
        {!data && !error && <p className="text-sm text-muted">Đang tải...</p>}

        {data && (
          <>
            {/* Đề bài + đáp án chuẩn */}
            <Card>
              <CardHeader title={data.problem.chuyen_de}
                subtitle={data.problem.dang_ten || undefined} />
              <CardBody className="flex flex-col gap-3">
                <div className="text-sm text-ink leading-relaxed">
                  {renderVanBan(data.problem.de_bai)}
                </div>
                {data.problem.hinh_anh && (
                  <img src={data.problem.hinh_anh} alt="Hình minh họa"
                    className="max-w-full sm:max-w-md rounded-md border border-border" />
                )}
                {data.problem.loai_cau === 'TN4PA' && (
                  <div className="flex flex-col gap-1 text-sm">
                    {Object.entries(data.problem.meta?.phuong_an || {}).map(([k, v]) => (
                      <p key={k}>
                        <span className="font-semibold text-primary">{k}.</span>{' '}
                        {renderVanBan(v)}
                      </p>
                    ))}
                  </div>
                )}
                {data.problem.loai_cau === 'TNDS' && (
                  <div className="flex flex-col gap-1 text-sm">
                    {(data.problem.meta?.y || []).map((item) => (
                      <p key={item.ky_hieu}>
                        <span className="font-semibold text-primary">{item.ky_hieu})</span>{' '}
                        {renderVanBan(item.noi_dung_y)}
                      </p>
                    ))}
                  </div>
                )}
                <div className="rounded-md bg-success-soft px-3 py-2">
                  <DapAnChuan loai_cau={data.problem.loai_cau} dap_an={data.dap_an} />
                </div>
              </CardBody>
            </Card>

            {/* Lời giải chuẩn từng bước */}
            <Card>
              <CardHeader title="Gợi ý các bước làm" subtitle={nhan.loiGiaiSub} />
              <CardBody className="flex flex-col gap-3">
                {data.loi_giai.length === 0 && (
                  <p className="text-sm text-muted">Bài này không có bước lời giải chi tiết.</p>
                )}
                {data.loi_giai.map((b) => (
                  <div key={`${b.pham_vi}-${b.thu_tu}`}
                    className="rounded-md border border-border px-3 py-2 flex flex-col gap-1">
                    <p className="text-xs font-semibold text-muted">
                      Bước {b.thu_tu}
                      {b.pham_vi && b.pham_vi !== 'ca_bai' ? ` - ý ${b.pham_vi})` : ''}
                    </p>
                    <div className="text-sm text-ink">{renderVanBan(b.mo_ta)}</div>
                    {b.bieu_thuc_ket_qua && (
                      <div className="text-sm">
                        <span className="text-muted">Kết quả bước: </span>
                        <Formula latex={b.bieu_thuc_ket_qua} />
                      </div>
                    )}
                  </div>
                ))}
              </CardBody>
            </Card>

            {/* Thống kê hành trình */}
            {tk && (
              <Card>
                <CardHeader title={nhan.hanhTrinh} />
                <CardBody className="flex flex-col gap-3">
                  <div className="flex gap-2 flex-wrap">
                    {tk.diem != null && <Badge tone="primary">Điểm: {tk.diem}</Badge>}
                    <Badge tone={tk.cap_goi_y_max === 0 ? 'success' : 'neutral'}>
                      {tk.cap_goi_y_max === 0
                        ? nhan.tuLam
                        : `Gợi ý cao nhất: mức ${tk.cap_goi_y_max}`}
                    </Badge>
                    <Badge tone="neutral">{tk.so_luot_hs} lượt trả lời</Badge>
                    {tk.thoi_gian_hoat_dong_giay != null && (
                      <Badge tone="neutral">
                        Thời gian: {dinhDangThoiGian(tk.thoi_gian_hoat_dong_giay)}
                      </Badge>
                    )}
                    {!!tk.so_lan_khong_hieu && (
                      <Badge tone="neutral">Đã xin gợi ý: {tk.so_lan_khong_hieu} lần</Badge>
                    )}
                    {!!tk.tong_so_lan_sai && (
                      <Badge tone="neutral">Thử lại: {tk.tong_so_lan_sai} lần</Badge>
                    )}
                    {/* diem_qua_trinh chỉ backend trả cho GV/Admin — HS không thấy trường này */}
                    {tk.diem_qua_trinh != null && (
                      <Badge tone="primary">Điểm quá trình (GV): {tk.diem_qua_trinh}</Badge>
                    )}
                  </div>
                  <div className="flex flex-col gap-2 max-h-96 overflow-y-auto pr-1">
                    {dungDongChat(data.hanh_trinh, {
                      loaiCau: data.problem?.loai_cau,
                      tongBuoc: data.tong_buoc,
                      moTaCacBuoc: data.mo_ta_cac_buoc,
                    }).map((d, i) =>
                      d.kieu === 'phan_cach' ? (
                        <PhanCachBuoc key={i} nhan={d.nhan} moTa={d.moTa} />
                      ) : (
                        <div key={i} className="flex flex-col gap-0.5">
                          {d.turn.vai_tro === 'gia_su' && d.turn.cap_goi_y > 0 && (
                            <p className="text-[11px] text-muted pl-1 inline-flex items-center gap-1">
                              <Lightbulb size={11} strokeWidth={2.4} /> gợi ý mức {d.turn.cap_goi_y}
                            </p>
                          )}
                          {/* co_bi_chot_chan chỉ backend trả cho GV/Admin — dấu vết lượt AI bị
                              chốt chặn rò rỉ, giúp GV hiểu vì sao có cờ ro_ri_dap_an. */}
                          {d.turn.co_bi_chot_chan && (
                            <p className="text-[11px] text-danger pl-1 inline-flex items-center gap-1">
                              <AlertTriangle size={11} strokeWidth={2.4} /> lượt này đã bị chốt chặn rò rỉ đáp án
                            </p>
                          )}
                          <ChatBubble vai_tro={d.turn.vai_tro}>
                            {renderVanBan(d.turn.noi_dung)}
                          </ChatBubble>
                        </div>
                      )
                    )}
                  </div>
                </CardBody>
              </Card>
            )}

            {/* Lời giải chi tiết — chỉ hiện nếu GV bật cho phép (backend đã lọc theo cấu
                hình, ở đây chỉ cần kiểm có nội dung hay không). */}
            {data.loi_giai_chi_tiet && (
              <Card>
                <CardHeader title="Lời giải chi tiết" />
                <CardBody>
                  <div className="text-sm text-ink leading-relaxed whitespace-pre-wrap">
                    {renderVanBan(data.loi_giai_chi_tiet)}
                  </div>
                </CardBody>
              </Card>
            )}

            <div className="flex justify-end pb-4">
              <Button variant="secondary" onClick={onDong}>Đóng</Button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
