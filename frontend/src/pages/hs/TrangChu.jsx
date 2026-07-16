import { useEffect, useState } from 'react'
import { api } from '../../api'
import { getSession } from '../../auth'
import { Badge, Button, Card, CardBody, CardHeader } from '../../components/ui'
import Formula from '../../components/Formula'
import ThoiGianPhanCach from '../../components/ThoiGianPhanCach'
import TongQuanTienDo from '../../components/TongQuanTienDo'
import The7NgayQua from '../../components/The7NgayQua'
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

// Lời chào theo số ngày đã học (X) + số ngày liên tiếp (Y) — khích lệ, không tiêu cực.
function LoiChao({ so_ngay, chuoi }) {
  if (so_ngay <= 0) {
    return <>Cùng bắt đầu bài học đầu tiên nào — gia sư sẽ dẫn dắt em từng bước để tự tìm ra lời giải.</>
  }
  if (chuoi >= 1) {
    return (
      <>
        Em đã học được <b className="text-primary">{so_ngay} ngày</b>, trong đó có{' '}
        <b className="text-primary">{chuoi} ngày liên tiếp</b>. Hãy giữ nhịp nhé!
      </>
    )
  }
  return (
    <>
      Em đã học được <b className="text-primary">{so_ngay} ngày</b>. Quay lại luyện tiếp hôm nay
      để nối lại chuỗi nhé!
    </>
  )
}

// 2 card trong hero (không tiêu đề): số lớn + chú thích ngắn + CTA.
function MiniHero({ big, cap, nhan, tone, onClick }) {
  const txt = tone === 'doing' ? 'text-warning-ink' : 'text-primary'
  return (
    <div className="bg-surface border border-border rounded-card shadow-[var(--shadow-card)]
      p-4 flex flex-col gap-2.5">
      <div>
        <p className={`text-4xl font-semibold leading-none tabular-nums ${txt}`}>{big}</p>
        <p className="text-xs text-muted mt-1">{cap}</p>
      </div>
      <Button variant="primary" size="sm" className="w-full" onClick={onClick}>{nhan}</Button>
    </div>
  )
}

// 3 card dưới hero: Nhiệm vụ / Mục tiêu / Luyện đề — phân số + thanh tiến độ + CTA "Bắt đầu".
function CardChiSo({ icon, iconBg, title, val, tong, donViXong, barColor, onClick }) {
  const w = pct(val, tong)
  return (
    <Card className="p-[18px] flex flex-col gap-3">
      <div className="flex items-center gap-2.5">
        <div className={`h-10 w-10 rounded-[10px] grid place-items-center text-xl shrink-0 ${iconBg}`}>
          {icon}
        </div>
        <h3 className="text-base font-semibold text-ink">{title}</h3>
      </div>
      <p className="text-[30px] font-semibold leading-none tabular-nums text-ink">
        {val}<span className="text-base font-medium text-muted"> / {tong} {donViXong}</span>
      </p>
      <div className="h-[7px] rounded-full bg-surface-2 overflow-hidden">
        <div className={`h-full rounded-full ${barColor}`} style={{ width: `${w}%` }} />
      </div>
      {/* Phương án A: nút "Bắt đầu" của 3 card này là LỐI TẮT điều hướng → dùng secondary
          (viền) để nhường sự nổi bật cam cho 2 CTA cốt lõi ở hero, tránh "bức tường cam". */}
      <Button variant="secondary" size="sm" className="w-full mt-0.5" onClick={onClick}>Bắt đầu</Button>
    </Card>
  )
}

// Thẻ thống kê thời gian — nổi bật, hiện đại.
function TheThoiGian({ icon, label, value, tone }) {
  const cls = {
    primary: 'from-primary/10 to-primary/5 text-primary',
    success: 'from-success/15 to-success/5 text-success',
    // "neutral" — vế "chậm nhất" của so sánh min/max: xám trung tính, KHÔNG đỏ (không phải lỗi).
    neutral: 'from-muted/10 to-muted/5 text-muted',
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

export default function TrangChu({ onChonBai, onLamTiep, onTiepTucLam, onDieuHuong }) {
  const { ho_ten } = getSession() || {}
  const [baiDo, setBaiDo] = useState([])
  const [tk, setTk] = useState(null)
  const [chuoi, setChuoi] = useState(null) // {chuoi_ngay, so_ngay_hoc, ...}
  const [deThi, setDeThi] = useState([])
  const [loading, setLoading] = useState(true)
  const [trang, setTrang] = useState(1)
  const [traLoi, setTraLoi] = useState([])
  const [trangTl, setTrangTl] = useState(1)
  const MOI_TRANG_TB = 3

  useEffect(() => {
    Promise.all([api.getDangDo(), api.getThongKeMe()])
      .then(([dd, thongKe]) => {
        setBaiDo(dd)
        setTk(thongKe || null)
      })
      .catch(() => {})
      .finally(() => setLoading(false))
    api.thongBao()
      .then((rows) => setTraLoi((rows || []).filter((t) => t.loai === 'tra_loi')))
      .catch(() => {})
    api.hsChuoiNgay().then(setChuoi).catch(() => {})
    api.deThiDs().then((d) => setDeThi(d || [])).catch(() => {})
  }, [])

  const tongTrang = Math.max(1, Math.ceil(baiDo.length / MOI_TRANG))
  const trangAnToan = Math.min(trang, tongTrang)
  const baiTrang = baiDo.slice((trangAnToan - 1) * MOI_TRANG, trangAnToan * MOI_TRANG)

  const tongTrangTl = Math.max(1, Math.ceil(traLoi.length / MOI_TRANG_TB))
  const tlTrang = traLoi.slice((trangTl - 1) * MOI_TRANG_TB, trangTl * MOI_TRANG_TB)

  const tq = tk?.tong_quan
  const tg = tk?.thoi_gian
  const nhanhNhat = tg ? minNonNull([tg.nhanh_nhat?.de, tg.nhanh_nhat?.tb, tg.nhanh_nhat?.kho]) : null
  const chamNhat = tg ? maxNonNull([tg.cham_nhat?.de, tg.cham_nhat?.tb, tg.cham_nhat?.kho]) : null
  const theoMuc = (k) => (tk?.theo_do_kho || []).find((r) => r.do_kho === k) || { hoan_thanh: 0, tong: 0 }

  const chuaLam = tq?.chua_lam ?? 0
  const soNgayHoc = chuoi?.so_ngay_hoc ?? 0
  const chuoiNgay = chuoi?.chuoi_ngay ?? 0
  // Luyện đề: suy từ danh sách đề đã phát hành — "đã làm" = có bài gần nhất đã nộp.
  const deDaLam = deThi.filter((d) => d.bai_gan_nhat?.trang_thai === 'da_nop').length
  const deTong = deThi.length

  return (
    <div className="flex flex-col gap-6">
      {/* ===== HERO: 1 vùng nổi bật duy nhất ===== */}
      <div className="rounded-card border border-border bg-gradient-to-br from-primary-soft
        to-[#f2f1fd] p-6 grid lg:grid-cols-[1.15fr_1fr] gap-5 items-center">
        <div>
          <h2 className="text-2xl font-semibold text-ink text-balance">
            Chào em{ho_ten ? `, ${ho_ten}` : ''}! 👋
          </h2>
          <p className="text-sm text-muted mt-2 max-w-[42ch] leading-relaxed">
            <LoiChao so_ngay={soNgayHoc} chuoi={chuoiNgay} />
          </p>
        </div>
        <div className="grid grid-cols-2 gap-3.5">
          <MiniHero big={baiDo.length} cap="bài đang làm dở" nhan="Tiếp tục làm"
            tone="doing" onClick={onTiepTucLam} />
          <MiniHero big={chuaLam} cap="bài chưa làm" nhan="Bắt đầu làm"
            tone="new" onClick={onChonBai} />
        </div>
      </div>

      {/* ===== 3 card: Nhiệm vụ · Mục tiêu · Luyện đề ===== */}
      <div className="grid sm:grid-cols-3 gap-4">
        <CardChiSo
          icon="📋" iconBg="bg-primary-soft" title="Nhiệm vụ"
          val={tk?.nhiem_vu?.hoan_thanh ?? 0} tong={tk?.nhiem_vu?.tong ?? 0}
          donViXong="hoàn thành" barColor="bg-primary"
          onClick={() => onDieuHuong?.('nhiem_vu')}
        />
        <CardChiSo
          icon="🎯" iconBg="bg-success-soft" title="Mục tiêu"
          val={tk?.muc_tieu?.dat ?? 0} tong={tk?.muc_tieu?.tong ?? 0}
          donViXong="đạt được" barColor="bg-success"
          onClick={() => onDieuHuong?.('muc_tieu')}
        />
        <CardChiSo
          icon="📝" iconBg="bg-accent-soft" title="Luyện đề"
          val={deDaLam} tong={deTong}
          donViXong="đã làm" barColor="bg-accent"
          onClick={() => onDieuHuong?.('thi_thu')}
        />
      </div>

      {/* ===== 2 cột: 7 ngày qua · thành tích ===== */}
      <div className="grid lg:grid-cols-2 gap-4 items-stretch">
        <The7NgayQua ss={tk?.so_sanh_7_ngay} title="7 ngày qua" className="h-full" />

        {/* Cột phải: thành tích (thời gian + số bài theo mức độ) */}
        <Card className="h-full flex flex-col">
          <CardHeader title="Thành tích của em" subtitle="Thời gian làm bài & số bài theo mức độ" />
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
                      value={dinhDangThoiGian(chamNhat)} tone="neutral" />
                  </div>
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
                          <p className="text-2xl font-bold text-ink mt-1 tabular-nums">{r.hoan_thanh}</p>
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

      {/* ===== Tổng quan tiến độ ===== */}
      <Card>
        <CardHeader title="Tiến độ của em" subtitle="Tổng quan tình hình luyện tập" />
        <CardBody>
          {loading || !tq ? (
            <p className="text-sm text-muted">Đang tải...</p>
          ) : (
            <TongQuanTienDo tq={tq} />
          )}
        </CardBody>
      </Card>

      {/* ===== Bài đang làm dở + Trả lời ===== */}
      <div className="grid lg:grid-cols-2 gap-4 items-stretch">
        {/* Cột trái: Bài đang làm dở */}
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
