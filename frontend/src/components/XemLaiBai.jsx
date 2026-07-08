/*
 * XemLaiBai — overlay toàn màn hình xem lại bài ĐÃ HOÀN THÀNH (B3):
 * lời giải chuẩn từng bước + đáp án đúng + hành trình hội thoại của HS + thống kê.
 * Backend chốt chặn: chỉ trả dữ liệu khi phiên hoan_thanh — component này không
 * quyết định quyền, chỉ hiển thị.
 */

import { useEffect, useState } from 'react'
import { api } from '../api'
import { Badge, Button, Card, CardBody, CardHeader, ChatBubble } from './ui'
import Formula from './Formula'
import { dinhDangThoiGian } from '../utils/format'

function renderVanBan(text) {
  return String(text ?? '')
    .split(/(\$[^$]+\$)/g)
    .map((p, i) =>
      p.startsWith('$') ? <Formula key={i} latex={p.slice(1, -1)} /> : <span key={i}>{p}</span>
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

export default function XemLaiBai({ sessionId, onDong }) {
  const [data, setData] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    setData(null)
    setError('')
    api.xemLaiPhien(sessionId).then(setData).catch((e) => setError(e.message))
  }, [sessionId])

  const tk = data?.thong_ke

  return (
    <div className="fixed inset-0 z-40 bg-black/40 overflow-y-auto">
      <div className="mx-auto w-full max-w-3xl min-h-full bg-bg p-4 sm:p-6 flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-ink">📖 Xem lại bài</h2>
          <Button variant="secondary" onClick={onDong}>Đóng ✕</Button>
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
              <CardHeader title="Gợi ý các bước làm"
                subtitle="Các bước thầy/cô đã soạn — em đối chiếu với cách làm của mình nhé" />
              <CardBody className="flex flex-col gap-3">
                {data.loi_giai.length === 0 && (
                  <p className="text-sm text-muted">Bài này không có bước lời giải chi tiết.</p>
                )}
                {data.loi_giai.map((b) => (
                  <div key={`${b.pham_vi}-${b.thu_tu}`}
                    className="rounded-md border border-border px-3 py-2 flex flex-col gap-1">
                    <p className="text-xs font-semibold text-muted">
                      Bước {b.thu_tu}
                      {b.pham_vi && b.pham_vi !== 'ca_bai' ? ` — ý ${b.pham_vi})` : ''}
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
                <CardHeader title="Hành trình của em" />
                <CardBody className="flex flex-col gap-3">
                  <div className="flex gap-2 flex-wrap">
                    {tk.diem != null && <Badge tone="primary">Điểm: {tk.diem}</Badge>}
                    <Badge tone={tk.cap_goi_y_max === 0 ? 'success' : 'neutral'}>
                      {tk.cap_goi_y_max === 0
                        ? 'Tự làm không cần gợi ý 🎉'
                        : `Gợi ý cao nhất: mức ${tk.cap_goi_y_max}`}
                    </Badge>
                    <Badge tone="neutral">{tk.so_luot_hs} lượt trả lời</Badge>
                    {tk.thoi_gian_hoat_dong_giay != null && (
                      <Badge tone="neutral">
                        Thời gian: {dinhDangThoiGian(tk.thoi_gian_hoat_dong_giay)}
                      </Badge>
                    )}
                  </div>
                  <div className="flex flex-col gap-2 max-h-96 overflow-y-auto pr-1">
                    {data.hanh_trinh.map((t, i) => (
                      <div key={i} className="flex flex-col gap-0.5">
                        {t.vai_tro === 'gia_su' && t.cap_goi_y > 0 && (
                          <p className="text-[11px] text-muted pl-1">💡 gợi ý mức {t.cap_goi_y}</p>
                        )}
                        <ChatBubble vai_tro={t.vai_tro}>
                          {renderVanBan(t.noi_dung)}
                          {t.dap_an_nhap && (
                            <p className="text-xs opacity-80 mt-1">↳ đáp án nhập: {t.dap_an_nhap}</p>
                          )}
                        </ChatBubble>
                      </div>
                    ))}
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
