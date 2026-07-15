import { Card, CardBody, CardHeader } from './ui'
import BangXepHangThoiGian from './BangXepHangThoiGian'
import { NHAN_LOAI_MAT_THOI_GIAN, dinhDangThoiGian } from '../utils/format'

const pct = (n, t) => (t > 0 ? Math.round((n / t) * 100) : 0)

// Vòng tròn tiến độ tổng (SVG).
function VongTienDo({ percent, size = 132, stroke = 13 }) {
  const r = (size - stroke) / 2
  const c = 2 * Math.PI * r
  const off = c * (1 - percent / 100)
  return (
    <div className="relative shrink-0 w-full mx-auto" style={{ maxWidth: size }}>
      <svg viewBox={`0 0 ${size} ${size}`} className="w-full h-auto -rotate-90">
        <circle cx={size / 2} cy={size / 2} r={r} fill="none"
          stroke="var(--color-surface-2)" strokeWidth={stroke} />
        <circle cx={size / 2} cy={size / 2} r={r} fill="none"
          stroke="var(--color-success)" strokeWidth={stroke} strokeLinecap="round"
          strokeDasharray={c} strokeDashoffset={off}
          style={{ transition: 'stroke-dashoffset .6s ease' }} />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-3xl font-bold text-ink">{percent}%</span>
        <span className="text-xs text-muted">hoàn thành</span>
      </div>
    </div>
  )
}

// Thanh tiến độ phân đoạn: hoàn thành (xanh) · đang dở (vàng) · chưa làm (xám, không đỏ).
function ThanhPhanDoan({ ht, dl, cl, tong }) {
  const w = (n) => (tong > 0 ? `${(n / tong) * 100}%` : '0%')
  return (
    <div className="flex h-2.5 w-full overflow-hidden rounded-full bg-surface-2">
      <div className="bg-success h-full" style={{ width: w(ht), transition: 'width .5s ease' }} />
      <div className="bg-warning h-full" style={{ width: w(dl), transition: 'width .5s ease' }} />
      <div className="bg-idle h-full" style={{ width: w(cl), transition: 'width .5s ease' }} />
    </div>
  )
}

function Cham({ color, children }) {
  return (
    <span className="inline-flex items-center gap-1 text-xs text-muted">
      <span className={`h-2 w-2 rounded-full ${color}`} />
      {children}
    </span>
  )
}

function HangTienDo({ ten, r }) {
  return (
    <div className="py-3 border-b border-border last:border-0">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-semibold text-ink">{ten}</span>
        <span className="text-xs text-muted">
          <b className="text-success text-sm">{r.hoan_thanh}</b>/{r.tong} bài ({pct(r.hoan_thanh, r.tong)}%)
        </span>
      </div>
      <ThanhPhanDoan ht={r.hoan_thanh} dl={r.dang_lam} cl={r.chua_lam} tong={r.tong} />
      <div className="flex flex-wrap gap-x-4 gap-y-1 mt-2">
        <Cham color="bg-success">Hoàn thành {r.hoan_thanh} ({pct(r.hoan_thanh, r.tong)}%)</Cham>
        <Cham color="bg-warning">Đang dở {r.dang_lam} ({pct(r.dang_lam, r.tong)}%)</Cham>
        <Cham color="bg-idle">Chưa làm {r.chua_lam} ({pct(r.chua_lam, r.tong)}%)</Cham>
      </div>
    </div>
  )
}

const MUC_CFG = {
  de:  { ten: 'Dễ',         bg: 'bg-success-soft', ring: 'var(--color-success)', txt: 'text-success' },
  tb:  { ten: 'Trung bình', bg: 'bg-warning-soft', ring: 'var(--color-warning)', txt: 'text-warning' },
  kho: { ten: 'Khó',        bg: 'bg-danger-soft',  ring: 'var(--color-danger)',  txt: 'text-danger'  },
}

// size = kích thước Ý ĐỊNH (px) dùng để tính bán kính/tỉ lệ nét vẽ — kích thước HIỂN THỊ
// thật sự co giãn theo bề rộng cột cha (viewBox + CSS thay vì width/height cố định), nên
// không bao giờ ép tràn ra ngoài khi cột bị hẹp lại (điện thoại, chia nhiều cột).
function BieuDoPie({ r, size = 110, stroke = 13 }) {
  const radius = (size - stroke) / 2
  const circ = 2 * Math.PI * radius
  const parts = [
    { n: r.hoan_thanh, color: 'var(--color-success)' },
    { n: r.dang_lam,   color: 'var(--color-warning)' },
    { n: r.chua_lam,   color: 'var(--color-idle)'  },
  ]
  let cum = 0
  const segs = parts.map(({ n, color }) => {
    const len = r.tong > 0 ? (n / r.tong) * circ : 0
    const seg = { len, offset: cum, color }
    cum += len
    return seg
  })
  const htPct = pct(r.hoan_thanh, r.tong)
  return (
    <div className="relative shrink-0 w-full mx-auto" style={{ maxWidth: size }}>
      <svg viewBox={`0 0 ${size} ${size}`} className="w-full h-auto -rotate-90">
        <circle cx={size / 2} cy={size / 2} r={radius} fill="none"
          stroke="var(--color-surface-2)" strokeWidth={stroke} />
        {segs.map((s, i) => s.len > 0.1 && (
          <circle key={i} cx={size / 2} cy={size / 2} r={radius} fill="none"
            stroke={s.color} strokeWidth={stroke}
            strokeDasharray={`${s.len} ${circ - s.len}`}
            strokeDashoffset={-s.offset}
            style={{ transition: 'stroke-dashoffset .6s ease' }} />
        ))}
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center leading-none gap-0.5">
        <span className="text-[22px] font-extrabold text-ink">{htPct}%</span>
        <span className="text-[9px] text-muted">hoàn thành</span>
      </div>
    </div>
  )
}

function TheMucDo({ r, size }) {
  const cfg = MUC_CFG[r.do_kho] || { ten: r.ten, bg: 'bg-surface-2', ring: 'var(--color-primary)', txt: 'text-primary' }
  return (
    <div className={`rounded-2xl ${cfg.bg} px-3 py-4 flex flex-col items-center gap-3`}>
      <p className={`text-xs font-bold uppercase tracking-widest ${cfg.txt}`}>{cfg.ten}</p>
      <BieuDoPie r={r} size={size} />
      <div className="w-full flex flex-col gap-1">
        <div className="flex items-center justify-between text-[11px]">
          <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-success inline-block" />Hoàn thành</span>
          <b className="text-ink">{r.hoan_thanh}</b>
        </div>
        <div className="flex items-center justify-between text-[11px]">
          <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-warning inline-block" />Đang dở</span>
          <b className="text-ink">{r.dang_lam}</b>
        </div>
        <div className="flex items-center justify-between text-[11px]">
          <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-idle inline-block" />Chưa làm</span>
          <b className="text-ink">{r.chua_lam}</b>
        </div>
        <p className="text-center text-[10px] text-muted mt-0.5">Tổng {r.tong} bài</p>
      </div>
    </div>
  )
}

function TheSo({ icon, label, value, tone = 'primary' }) {
  const toneCls = {
    primary: 'text-primary bg-primary-soft',
    success: 'text-success bg-success-soft',
    warning: 'text-warning bg-warning-soft',
    danger: 'text-danger bg-danger-soft',
  }[tone]
  return (
    <Card className="px-4 py-4 flex items-center gap-3">
      <div className={`h-11 w-11 rounded-lg grid place-items-center text-xl ${toneCls}`}>{icon}</div>
      <div className="min-w-0">
        <p className="text-xs text-muted">{label}</p>
        <p className="text-xl font-bold text-ink truncate">{value}</p>
      </div>
    </Card>
  )
}

// Thống kê tiến độ dùng chung (trang HS + GV xem từng học sinh).
export default function ThongKeTienDo({ tk }) {
  if (!tk) return <p className="text-sm text-danger">Không tải được thống kê.</p>

  const tq = tk.tong_quan
  const tg = tk.thoi_gian
  const MUC = [['de', 'Dễ'], ['tb', 'Trung bình'], ['kho', 'Khó']]

  return (
    <div className="flex flex-col gap-6">
      {/* 1) TỔNG QUAN — hero */}
      <Card className="overflow-hidden">
        <div className="border-l-4 border-primary">
          <CardBody className="pt-5 flex flex-col sm:flex-row items-center gap-6">
            <VongTienDo percent={pct(tq.hoan_thanh, tq.tong)} />
            <div className="flex-1 w-full grid grid-cols-2 gap-3">
              <div className="rounded-lg bg-surface-2 px-4 py-3">
                <p className="text-xs text-muted">Tổng số bài</p>
                <p className="text-2xl font-bold text-ink">{tq.tong}</p>
              </div>
              <div className="rounded-lg bg-success-soft px-4 py-3">
                <p className="text-xs text-success">Đã hoàn thành</p>
                <p className="text-2xl font-bold text-success">
                  {tq.hoan_thanh} <span className="text-base font-semibold">({pct(tq.hoan_thanh, tq.tong)}%)</span>
                </p>
              </div>
              <div className="rounded-lg bg-warning-soft px-4 py-3">
                <p className="text-xs text-warning">Đang làm dở</p>
                <p className="text-2xl font-bold text-warning">
                  {tq.dang_lam} <span className="text-base font-semibold">({pct(tq.dang_lam, tq.tong)}%)</span>
                </p>
              </div>
              <div className="rounded-lg bg-idle-soft px-4 py-3">
                <p className="text-xs text-idle">Chưa làm</p>
                <p className="text-2xl font-bold text-idle">
                  {tq.chua_lam} <span className="text-base font-semibold">({pct(tq.chua_lam, tq.tong)}%)</span>
                </p>
              </div>
            </div>
          </CardBody>
        </div>
      </Card>

      {/* 2) THEO THỜI GIAN (trái) + THEO MỨC ĐỘ (phải) — 2 cột cao bằng nhau */}
      <div className="grid lg:grid-cols-2 gap-6 items-stretch">
        <Card className="h-full flex flex-col">
          <CardHeader title="Theo thời gian" subtitle="Thời gian hoàn thành bài theo mức độ" />
          <CardBody className="flex flex-col gap-3 flex-1">
            <TheSo icon="⏱️" label="Tổng thời gian làm bài"
              value={dinhDangThoiGian(tg.tong_thoi_gian_giay)} tone="primary" />
            <div className="flex flex-col gap-2">
              {MUC.map(([k, ten]) => (
                <div key={k} className="rounded-lg border border-border px-3 py-2.5">
                  <p className="text-sm font-semibold text-ink mb-1">{ten}</p>
                  <div className="flex items-center justify-between text-sm">
                    <span className="inline-flex items-center gap-1 text-success">⚡ Nhanh nhất</span>
                    <b>{tg.nhanh_nhat[k] != null ? dinhDangThoiGian(tg.nhanh_nhat[k]) : '—'}</b>
                  </div>
                  <div className="flex items-center justify-between text-sm mt-0.5">
                    <span className="inline-flex items-center gap-1 text-muted">🐢 Chậm nhất</span>
                    <b>{tg.cham_nhat[k] != null ? dinhDangThoiGian(tg.cham_nhat[k]) : '—'}</b>
                  </div>
                </div>
              ))}
            </div>
          </CardBody>
        </Card>

        <Card className="h-full flex flex-col">
          <CardHeader title="Theo mức độ" subtitle="Tỉ lệ hoàn thành từng mức" />
          <CardBody className="flex-1 flex items-center py-6">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 w-full">
              {tk.theo_do_kho.map((r) => (
                <TheMucDo key={r.do_kho} r={r} size={128} />
              ))}
            </div>
          </CardBody>
        </Card>
      </div>

      {/* 3) THEO DẠNG BÀI — 2 cột chuyên đề */}
      <Card>
        <CardHeader title="Theo dạng bài" subtitle="Tiến độ từng dạng trong mỗi chuyên đề" />
        <CardBody>
          {tk.theo_dang.length === 0 && <p className="text-sm text-muted">Chưa có bài nào.</p>}
          <div className="grid lg:grid-cols-2 gap-4 items-start">
            {tk.theo_dang.map((cd) => (
              <div key={cd.chuyen_de} className="rounded-lg border border-border overflow-hidden">
                <div className="bg-primary-soft px-4 py-2 text-primary font-bold text-sm">
                  {cd.chuyen_de}
                </div>
                <div className="px-4">
                  {cd.dang.map((r) => (
                    <HangTienDo key={r.ten} ten={r.ten} r={r} />
                  ))}
                </div>
              </div>
            ))}
          </div>
        </CardBody>
      </Card>

      {/* 4) MẤT NHIỀU THỜI GIAN — riêng của HS này (KHÔNG cộng dồn với HS khác), khác với
          card cùng tên ở trang Tổng quan (GV, cộng dồn cả lớp). */}
      {(tk.dang_mat_thoi_gian?.length > 0 || tk.loai_mat_thoi_gian?.length > 0) && (
        <div className="grid lg:grid-cols-2 gap-4 items-start">
          <BangXepHangThoiGian
            title="Dạng bài mất nhiều thời gian"
            subtitle="Tối đa 3 dạng — theo tổng thời gian hoàn thành"
            rows={tk.dang_mat_thoi_gian || []}
            nhan={(r) => r.ten}
            empty="Chưa có dữ liệu hoàn thành."
          />
          <BangXepHangThoiGian
            title="Loại câu hỏi mất nhiều thời gian"
            subtitle="Theo tổng thời gian hoàn thành"
            rows={tk.loai_mat_thoi_gian || []}
            nhan={(r) => NHAN_LOAI_MAT_THOI_GIAN[r.loai] || r.loai}
            empty="Chưa có dữ liệu hoàn thành."
          />
        </div>
      )}
    </div>
  )
}
