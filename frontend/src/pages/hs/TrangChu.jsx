import { useEffect, useState } from 'react'
import { api } from '../../api'
import { getSession } from '../../auth'
import { Badge, Button, Card, CardBody, CardHeader } from '../../components/ui'
import Formula from '../../components/Formula'
import ThoiGianPhanCach from '../../components/ThoiGianPhanCach'
import { dinhDangThoiGian } from '../../utils/format'

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

const NHAN_LOAI = { TN4PA: 'Trắc nghiệm', TNDS: 'Đúng/Sai', TLN: 'Trả lời ngắn' }
const pct = (n, t) => (t > 0 ? Math.round((n / t) * 100) : 0)
const MOI_TRANG = 3
const MUC = [
  { key: 'de', ten: 'Dễ', tone: 'success' },
  { key: 'tb', ten: 'Trung bình', tone: 'warning' },
  { key: 'kho', ten: 'Khó', tone: 'danger' },
]

const minNonNull = (arr) => {
  const v = arr.filter((x) => x != null)
  return v.length ? Math.min(...v) : null
}
const maxNonNull = (arr) => {
  const v = arr.filter((x) => x != null)
  return v.length ? Math.max(...v) : null
}

function TheTongQuan({ label, value, sub, tone }) {
  const cls = {
    primary: 'bg-surface-2 text-ink',
    success: 'bg-success-soft text-success',
    warning: 'bg-warning-soft text-warning',
    danger: 'bg-danger-soft text-danger',
  }[tone]
  return (
    <div className={`rounded-xl px-4 py-4 ${cls}`}>
      <p className="text-xs font-medium opacity-80">{label}</p>
      <p className="text-3xl font-bold mt-1">
        {value}
        {sub != null && <span className="text-base font-semibold ml-1">({sub}%)</span>}
      </p>
    </div>
  )
}

// Thẻ thống kê thời gian — nổi bật, hiện đại.
function TheThoiGian({ icon, label, value, tone }) {
  const cls = {
    primary: 'from-primary/10 to-primary/5 text-primary',
    success: 'from-success/15 to-success/5 text-success',
    danger: 'from-danger/15 to-danger/5 text-danger',
  }[tone]
  return (
    <div className={`rounded-xl bg-gradient-to-br ${cls} px-4 py-3.5 flex items-center gap-3`}>
      <span className="text-2xl">{icon}</span>
      <div className="min-w-0">
        <p className="text-[11px] font-medium text-muted">{label}</p>
        <p className="text-lg font-bold text-ink truncate">{value}</p>
      </div>
    </div>
  )
}

export default function TrangChu({ onChonBai, onLamTiep }) {
  const { ho_ten } = getSession() || {}
  const [baiDo, setBaiDo] = useState([])
  const [tk, setTk] = useState(null)
  const [loading, setLoading] = useState(true)
  const [trang, setTrang] = useState(1)
  const [nhanXet, setNhanXet] = useState([])
  const [traLoi, setTraLoi] = useState([])
  const [trangNx, setTrangNx] = useState(1)
  const [trangTl, setTrangTl] = useState(1)
  const [chuoi, setChuoi] = useState(null) // {chuoi_ngay, tong_bai_hoan_thanh, cot_moc_da_dat}
  const MOI_TRANG_TB = 3
  // Date.now() không được gọi trong thân render (impure) — tính 1 lần trong effect lúc mount.
  const [bayNgayTruoc, setBayNgayTruoc] = useState(null)
  useEffect(() => {
    setTimeout(() => setBayNgayTruoc(new Date(Date.now() - 7 * 24 * 60 * 60 * 1000)), 0)
  }, [])

  useEffect(() => {
    Promise.all([api.getDangDo(), api.getThongKeMe()])
      .then(([dd, thongKe]) => {
        setBaiDo(dd)
        setTk(thongKe || null)
      })
      .catch(() => {})
      .finally(() => setLoading(false))
    api.thongBao()
      .then((rows) => {
        const all = rows || []
        setNhanXet(all.filter((t) => t.loai === 'nhan_xet'))
        setTraLoi(all.filter((t) => t.loai === 'tra_loi'))
      })
      .catch(() => {})
    api.hsChuoiNgay().then(setChuoi).catch(() => {})
  }, [])

  const tongTrang = Math.max(1, Math.ceil(baiDo.length / MOI_TRANG))
  const trangAnToan = Math.min(trang, tongTrang)
  const baiTrang = baiDo.slice((trangAnToan - 1) * MOI_TRANG, trangAnToan * MOI_TRANG)

  const tongTrangNx = Math.max(1, Math.ceil(nhanXet.length / MOI_TRANG_TB))
  const nxTrang = nhanXet.slice((trangNx - 1) * MOI_TRANG_TB, trangNx * MOI_TRANG_TB)
  const tongTrangTl = Math.max(1, Math.ceil(traLoi.length / MOI_TRANG_TB))
  const tlTrang = traLoi.slice((trangTl - 1) * MOI_TRANG_TB, trangTl * MOI_TRANG_TB)

  const tq = tk?.tong_quan
  const tg = tk?.thoi_gian
  const nhanhNhat = tg ? minNonNull([tg.nhanh_nhat?.de, tg.nhanh_nhat?.tb, tg.nhanh_nhat?.kho]) : null
  const chamNhat = tg ? maxNonNull([tg.cham_nhat?.de, tg.cham_nhat?.tb, tg.cham_nhat?.kho]) : null
  const theoMuc = (k) => (tk?.theo_do_kho || []).find((r) => r.do_kho === k) || { hoan_thanh: 0, tong: 0 }

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h2 className="text-xl font-semibold text-black">Chào em{ho_ten ? `, ${ho_ten}` : ''}!</h2>
        <p className="text-black/90 text-sm mt-1">
          Gia sư sẽ dẫn dắt bằng câu hỏi gợi mở — em tự tìm ra lời giải nhé.
        </p>
      </div>

      {/* Chuỗi ngày học + cột mốc mới */}
      {chuoi && (chuoi.chuoi_ngay > 0 || chuoi.cot_moc_da_dat?.length > 0) && (
        <div className="flex flex-wrap gap-3 items-start">
          {chuoi.chuoi_ngay > 0 && (
            <div className="flex items-center gap-2 rounded-xl border border-warning/40 bg-warning-soft px-4 py-2.5 shrink-0">
              <span className="text-xl">🔥</span>
              <div>
                <p className="text-sm font-bold text-warning leading-tight">{chuoi.chuoi_ngay} ngày liên tiếp</p>
                <p className="text-[11px] text-muted">Chuỗi ngày học của em</p>
              </div>
            </div>
          )}
          {(() => {
            const moi = bayNgayTruoc ? (chuoi.cot_moc_da_dat || []).filter(
              (m) => m.dat_luc && new Date(m.dat_luc) >= bayNgayTruoc
            ).slice(0, 2) : []
            return moi.map((m) => (
              <div key={m.loai}
                className="flex items-center gap-2 rounded-xl border border-success/40 bg-success-soft px-4 py-2.5">
                <div>
                  <p className="text-sm font-bold text-success leading-tight">{m.tieu_de}</p>
                  <p className="text-[11px] text-muted">{m.mo_ta}</p>
                </div>
              </div>
            ))
          })()}
        </div>
      )}

      {/* Nút bắt đầu làm bài mới — to & nổi bật */}
      <Button onClick={onChonBai}
        className="w-full py-4 text-lg font-bold shadow-[var(--shadow-pop)]">
        ✏️ BẮT ĐẦU LÀM BÀI MỚI
      </Button>

      {/* 2 cột: trái = bài đang làm dở · phải = thống kê */}
      <div className="grid lg:grid-cols-2 gap-4 items-stretch">
        {/* Cột trái */}
        <Card className="h-full flex flex-col">
          <CardHeader title="Bài đang làm dở" subtitle="Tiếp tục đúng chỗ em dừng lại" />
          <CardBody className="flex flex-col gap-3">
            {loading ? (
              <p className="text-sm text-muted">Đang tải...</p>
            ) : baiDo.length === 0 ? (
              <p className="text-sm text-muted">Em chưa có bài nào đang làm dở.</p>
            ) : (
              <>
                {baiTrang.map((b) => (
                  <div
                    key={b.session_id}
                    className="rounded-md border border-border px-3 py-2.5 flex flex-col gap-2"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0 flex-1">
                        <p className="text-xs font-semibold text-primary truncate">
                          {b.chuyen_de}
                          {b.dang_ten ? <> › <span className="text-ink">{b.dang_ten}</span></> : null}
                        </p>
                        <p className="text-sm text-ink leading-snug mt-1 line-clamp-2">
                          {renderNoiDung(b.de_bai)}
                        </p>
                      </div>
                      <Button size="sm" variant="warning" className="shrink-0"
                        onClick={() => onLamTiep(b.session_id)}>
                        Làm tiếp
                      </Button>
                    </div>
                    <p className="text-xs text-muted flex items-center gap-2">
                      <Badge tone="primary">{NHAN_LOAI[b.loai_cau] || b.loai_cau}</Badge>
                      <span>Bước {b.buoc_hien_tai}</span>
                      {b.cap_nhat_luc && (
                        <span>· {new Date(b.cap_nhat_luc).toLocaleDateString('vi-VN')}</span>
                      )}
                    </p>
                  </div>
                ))}

                {tongTrang > 1 && (
                  <div className="flex items-center justify-center gap-3 pt-1">
                    <Button size="sm" variant="secondary" disabled={trangAnToan <= 1}
                      onClick={() => setTrang((t) => Math.max(1, t - 1))}>
                      ← Trước
                    </Button>
                    <span className="text-sm text-muted">
                      Trang {trangAnToan}/{tongTrang}
                    </span>
                    <Button size="sm" variant="secondary" disabled={trangAnToan >= tongTrang}
                      onClick={() => setTrang((t) => Math.min(tongTrang, t + 1))}>
                      Sau →
                    </Button>
                  </div>
                )}
              </>
            )}
          </CardBody>
        </Card>

        {/* Cột phải: thống kê */}
        <Card className="h-full flex flex-col">
          <CardHeader title="Thành tích của em" subtitle="Thời gian, nhiệm vụ & mục tiêu" />
          <CardBody className="flex flex-col gap-4 flex-1">
            {loading || !tg ? (
              <p className="text-sm text-muted">Đang tải...</p>
            ) : (
              <>
                <div className="flex flex-col gap-3">
                  <TheThoiGian icon="⏱️" label="Tổng thời gian làm bài"
                    value={dinhDangThoiGian(tg.tong_thoi_gian_giay)} tone="primary" />
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <TheThoiGian icon="⚡" label="Hoàn thành nhanh nhất"
                      value={dinhDangThoiGian(nhanhNhat)} tone="success" />
                    <TheThoiGian icon="🐢" label="Hoàn thành chậm nhất"
                      value={dinhDangThoiGian(chamNhat)} tone="danger" />
                  </div>
                </div>

                {/* Nhiệm vụ + Mục tiêu */}
                <div className="grid grid-cols-2 gap-3">
                  {[
                    {
                      icon: '📋', label: 'Nhiệm vụ hoàn thành',
                      val: tk?.nhiem_vu?.hoan_thanh ?? 0,
                      tong: tk?.nhiem_vu?.tong ?? 0,
                      tone: 'primary',
                    },
                    {
                      icon: '🎯', label: 'Mục tiêu đạt được',
                      val: tk?.muc_tieu?.dat ?? 0,
                      tong: tk?.muc_tieu?.tong ?? 0,
                      tone: 'success',
                    },
                  ].map(({ icon, label, val, tong, tone }) => {
                    const bg = { primary: 'bg-primary-soft', success: 'bg-success-soft' }[tone]
                    const txt = { primary: 'text-primary', success: 'text-success' }[tone]
                    return (
                      <div key={label} className={`rounded-xl ${bg} px-4 py-3 flex items-center gap-3`}>
                        <span className="text-2xl">{icon}</span>
                        <div className="min-w-0">
                          <p className="text-[11px] text-muted">{label}</p>
                          <p className={`text-xl font-bold ${txt}`}>
                            {val}
                            <span className="text-sm font-normal text-muted"> / {tong}</span>
                          </p>
                        </div>
                      </div>
                    )
                  })}
                </div>

                <div>
                  <p className="text-sm font-semibold text-ink mb-2">
                    Số bài đã hoàn thành theo mức độ
                  </p>
                  <div className="grid grid-cols-3 gap-3">
                    {MUC.map(({ key, ten, tone }) => {
                      const r = theoMuc(key)
                      const cls = {
                        success: 'border-success/40 bg-success-soft',
                        warning: 'border-warning/40 bg-warning-soft',
                        danger: 'border-danger/40 bg-danger-soft',
                      }[tone]
                      const txt = {
                        success: 'text-success', warning: 'text-warning', danger: 'text-danger',
                      }[tone]
                      return (
                        <div key={key} className={`rounded-xl border ${cls} px-3 py-3 text-center`}>
                          <p className={`text-[11px] font-bold uppercase tracking-wide ${txt}`}>{ten}</p>
                          <p className="text-2xl font-bold text-ink mt-1">{r.hoan_thanh}</p>
                          <p className="text-xs text-muted">/{r.tong} bài</p>
                          <p className={`text-sm font-bold mt-0.5 ${txt}`}>
                            {pct(r.hoan_thanh, r.tong)}%
                          </p>
                        </div>
                      )
                    })}
                  </div>
                </div>
              </>
            )}
          </CardBody>
        </Card>
      </div>

      {/* Tổng quan tiến độ */}
      <Card>
        <CardHeader title="Tiến độ của em" subtitle="Tổng quan tình hình luyện tập" />
        <CardBody>
          {loading || !tq ? (
            <p className="text-sm text-muted">Đang tải...</p>
          ) : (
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
              <TheTongQuan label="Tổng số bài" value={tq.tong} tone="primary" />
              <TheTongQuan label="Đã hoàn thành" value={tq.hoan_thanh}
                sub={pct(tq.hoan_thanh, tq.tong)} tone="success" />
              <TheTongQuan label="Đang làm dở" value={tq.dang_lam}
                sub={pct(tq.dang_lam, tq.tong)} tone="warning" />
              <TheTongQuan label="Chưa làm" value={tq.chua_lam}
                sub={pct(tq.chua_lam, tq.tong)} tone="danger" />
            </div>
          )}
        </CardBody>
      </Card>

      {/* Nhận xét + Trả lời — 2 cột, luôn hiện kể cả khi rỗng (báo trạng thái rõ ràng) */}
      <div className="grid lg:grid-cols-2 gap-4">
        {/* Cột trái: Nhận xét */}
        <Card className="h-full">
          <CardHeader title="💬 Nhận xét của thầy/cô"
            subtitle={nhanXet.length > 0 ? `${nhanXet.length} lời nhắn từ giáo viên` : undefined} />
          <CardBody className="flex flex-col gap-3">
            {nhanXet.length === 0 ? (
              <p className="text-sm text-muted">Thầy/cô chưa gửi nhận xét nào cho em.</p>
            ) : (
              <>
                {nxTrang.map((tb) => (
                  <div key={tb.id}
                    className="rounded-xl border border-gv/30 bg-gv/5 px-4 py-3">
                    <p className="text-sm text-ink whitespace-pre-wrap break-words">{tb.noi_dung}</p>
                    <div className="flex items-center flex-wrap gap-x-0.5 text-xs text-muted mt-1.5">
                      {tb.nguoi_gui_ten && <span>— {tb.nguoi_gui_ten}</span>}
                      {tb.tao_luc && <ThoiGianPhanCach iso={tb.tao_luc} />}
                    </div>
                  </div>
                ))}
                {tongTrangNx > 1 && (
                  <div className="flex items-center justify-center gap-3 pt-1">
                    <Button size="sm" variant="secondary" disabled={trangNx <= 1}
                      onClick={() => setTrangNx((t) => t - 1)}>← Trước</Button>
                    <span className="text-sm text-muted">{trangNx}/{tongTrangNx}</span>
                    <Button size="sm" variant="secondary" disabled={trangNx >= tongTrangNx}
                      onClick={() => setTrangNx((t) => t + 1)}>Sau →</Button>
                  </div>
                )}
              </>
            )}
          </CardBody>
        </Card>

        {/* Cột phải: Trả lời */}
        <Card className="h-full">
          <CardHeader title="👩‍🏫 Thầy/cô đã trả lời"
            subtitle={traLoi.length > 0 ? `${traLoi.length} câu trả lời` : undefined} />
          <CardBody className="flex flex-col gap-3">
            {traLoi.length === 0 ? (
              <p className="text-sm text-muted">Thầy/cô chưa trả lời các yêu cầu của em.</p>
            ) : (
              <>
                {tlTrang.map((tb) => (
                  <div key={tb.id}
                    className="rounded-xl border border-gv/30 bg-gv/5 px-4 py-3 flex flex-col gap-2">
                    <div className="text-sm text-ink leading-relaxed">
                      <span className="font-medium">Trả lời: </span>
                      {renderNoiDung(tb.noi_dung)}
                    </div>
                    <div className="flex items-center justify-between gap-2 flex-wrap">
                      <div className="flex items-center flex-wrap gap-x-0.5 text-xs text-muted">
                        {tb.nguoi_gui_ten && <span>— {tb.nguoi_gui_ten}</span>}
                        {tb.tao_luc && <ThoiGianPhanCach iso={tb.tao_luc} />}
                      </div>
                      {tb.lien_ket_id && onLamTiep && (
                        <Button size="sm" variant="secondary"
                          onClick={() => onLamTiep(tb.lien_ket_id)}>
                          Tiếp tục bài
                        </Button>
                      )}
                    </div>
                  </div>
                ))}
                {tongTrangTl > 1 && (
                  <div className="flex items-center justify-center gap-3 pt-1">
                    <Button size="sm" variant="secondary" disabled={trangTl <= 1}
                      onClick={() => setTrangTl((t) => t - 1)}>← Trước</Button>
                    <span className="text-sm text-muted">{trangTl}/{tongTrangTl}</span>
                    <Button size="sm" variant="secondary" disabled={trangTl >= tongTrangTl}
                      onClick={() => setTrangTl((t) => t + 1)}>Sau →</Button>
                  </div>
                )}
              </>
            )}
          </CardBody>
        </Card>
      </div>

    </div>
  )
}
