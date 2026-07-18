import { Badge, Button, Card, CardBody, CardHeader } from './ui'

const TONE_NHAN = {
  manh: 'success', kha: 'warning', can_cai_thien: 'danger', chua_du_lieu: 'neutral',
}
const NHAN_TEXT = {
  manh: 'Mạnh', kha: 'Khá', can_cai_thien: 'Cần cải thiện', chua_du_lieu: 'Chưa đủ dữ liệu',
}
const BAR = {
  manh: 'bg-success', kha: 'bg-warning', can_cai_thien: 'bg-danger', chua_du_lieu: 'bg-surface-2',
}
const TIN_CAY = { cao: 'Độ tin cậy cao', trung_binh: 'Độ tin cậy trung bình', thap: 'Độ tin cậy thấp' }

// Xu hướng (đo bằng điểm quá trình: ít sai/ít cần gợi ý hơn = tiến bộ).
const XU_HUONG_CFG = {
  tien_bo: { text: '↗ Đang tiến bộ', cls: 'text-success bg-success-soft' },
  on_dinh: { text: '→ Ổn định', cls: 'text-muted bg-surface-2' },
  giam: { text: '↘ Cần quan tâm', cls: 'text-warning bg-warning-soft' },
}

// Badge xu hướng tổng (đặt ở header card phân tích) — 'chua_du' thì không chiếm chỗ.
function XuHuongBadge({ xh }) {
  const cfg = XU_HUONG_CFG[xh]
  if (!cfg) return null
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-bold ${cfg.cls}`}
      title="So nửa số bài gần đây với nửa trước đó, theo điểm quá trình (số lần sai + lượt cần gợi ý)">
      {cfg.text}
    </span>
  )
}

// Mũi tên xu hướng nhỏ theo từng dạng (chỉ hiện khi dạng đó đủ ≥4 bài hoàn thành).
function MuiTenXuHuong({ xh }) {
  const cfg = XU_HUONG_CFG[xh]
  if (!cfg) return null
  return (
    <span className={`text-xs font-bold shrink-0 ${cfg.cls.split(' ')[0]}`}
      title={`Xu hướng riêng của dạng này: ${cfg.text.slice(2)}`}>
      {cfg.text.split(' ')[0]}
    </span>
  )
}

function HangNhom({ r }) {
  const pct = r.diem_thanh_thao ?? 0
  return (
    <div className="py-2 border-b border-border last:border-0">
      <div className="flex items-center justify-between gap-2 mb-1">
        <span className="text-sm text-ink inline-flex items-center gap-1.5 min-w-0">
          <span className="truncate">{r.ten}</span>
          <MuiTenXuHuong xh={r.xu_huong} />
        </span>
        <span className="flex items-center gap-2 shrink-0">
          <Badge tone={TONE_NHAN[r.nhan]}>{NHAN_TEXT[r.nhan]}</Badge>
          <b className="text-sm text-ink w-10 text-right">
            {r.diem_thanh_thao == null ? '—' : `${pct}%`}
          </b>
        </span>
      </div>
      <div className="h-2 w-full rounded-full bg-surface-2 overflow-hidden">
        <div className={`h-full ${BAR[r.nhan]}`} style={{ width: `${pct}%` }} />
      </div>
      <p className="text-[11px] text-muted mt-1">
        Hoàn thành {r.so_hoan_thanh}/{r.so_phien} · {r.ty_le_hoan_thanh}%
        {r.goi_y_tb >= 1 ? ` · dùng gợi ý TB ${r.goi_y_tb}` : ''}
      </p>
      <ChanDoanVatLon r={r} />
    </div>
  )
}

// Cột chẩn đoán "vật lộn" — chỉ hiện các dấu hiệu > 0 (không có thì không chiếm chỗ). KHÔNG
// nằm trong điểm thành thạo, chỉ là bức tranh hành trình để GV/HS thấy chỗ cần quan tâm.
function ChanDoanVatLon({ r }) {
  const dau = [
    r.so_lan_het_goi_y > 0 && { icon: '🚧', text: `cạn gợi ý ${r.so_lan_het_goi_y} lần` },
    r.so_lan_xem_ly_thuyet > 0 && { icon: '📖', text: `xem lại lý thuyết ${r.so_lan_xem_ly_thuyet} lần` },
    r.so_lan_nho_thay_co > 0 && { icon: '🙋', text: `nhờ thầy/cô ${r.so_lan_nho_thay_co} lần` },
  ].filter(Boolean)
  if (dau.length === 0) return null
  return (
    <div className="mt-1 flex flex-wrap gap-1.5">
      {dau.map((d, i) => (
        <span key={i} className="inline-flex items-center gap-1 rounded bg-warning-soft
          text-warning text-[11px] font-medium px-1.5 py-0.5">
          {d.icon} {d.text}
        </span>
      ))}
    </div>
  )
}

function dinhDangNgay(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  return isNaN(d) ? '' : d.toLocaleString('vi-VN', {
    day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit',
  })
}

// pt: payload từ /phan-tich. vaiTro: 'hs' | 'gv'.
// onCapNhat?: gọi API sinh phân tích; dangCapNhat: cờ đang chạy.
// sauNhanXet?: nội dung chèn ngay sau card "Nhận xét & gợi ý cho em"/"Phân tích năng lực"
// (trước khối "Theo dạng bài"/"Theo loại câu hỏi") — dùng ở trang Tiến độ HS để đặt card
// "Nhận xét của thầy/cô" đúng vị trí, không đổi gì khác của component dùng chung này.
export default function PhanTichNangLuc({ pt, vaiTro = 'hs', onCapNhat, dangCapNhat, onLuyen, sauNhanXet }) {
  if (!pt) return null
  const deXuat = vaiTro === 'gv' ? pt.de_xuat_gv : pt.de_xuat_hs
  const aiText = pt.ai ? (vaiTro === 'gv' ? pt.ai.cho_giao_vien : pt.ai.cho_hoc_sinh) : ''
  const coData = pt.tong_hoan_thanh > 0
  const tuDong = pt.tu_dong_phan_tich
  const theoLuat = pt.ai?.nguon === 'luat'
  // Đã mới khi: tự động bật + đã có bản phân tích AI + không đến hạn.
  const daMoiNhat = tuDong && pt.ai && !theoLuat && !pt.nen_cap_nhat
  const nhanNut = dangCapNhat
    ? 'Đang phân tích...'
    : daMoiNhat ? 'Cập nhật lại ngay' : (pt.ai ? 'Cập nhật' : 'Tạo phân tích')

  return (
    <div className="flex flex-col gap-4">
      {/* Nhận định (nếu có) + nút cập nhật thông minh theo trạng thái */}
      <Card>
        <CardHeader
          title="Đánh giá tổng quan"
          subtitle={pt.ai?.tao_luc
            ? `Cập nhật ${dinhDangNgay(pt.ai.tao_luc)} · dựa trên ${pt.ai.so_bai_luc_tao} bài`
            : 'Diễn giải hồ sơ năng lực thành nhận xét & định hướng'}
          action={onCapNhat && coData ? (
            <Button size="sm" variant={daMoiNhat || pt.ai ? 'ghost' : 'primary'}
              onClick={onCapNhat} disabled={dangCapNhat}>
              {nhanNut}
            </Button>
          ) : null}
        />
        <CardBody>
          {aiText ? (
            <>
              <p className="text-sm text-ink whitespace-pre-line leading-relaxed">{aiText}</p>
              {theoLuat ? (
                <p className="text-[11px] text-warning mt-2">
                  Nhận định tạm theo quy tắc — chưa gọi được AI (có thể đã hết lượt trong ngày).
                  Hệ thống sẽ tự nâng cấp khi AI sẵn sàng.
                </p>
              ) : pt.nen_cap_nhat ? (
                <p className="text-[11px] text-warning mt-2">
                  Có dữ liệu mới — nên bấm "Cập nhật" để phân tích lại.
                </p>
              ) : daMoiNhat ? (
                <p className="text-[11px] text-muted mt-2">
                  🤖 Đã tự động phân tích - đây đã là phân tích mới nhất.
                </p>
              ) : null}
            </>
          ) : (
            <p className="text-sm text-muted">
              {coData
                ? (tuDong
                    ? 'Hệ thống sẽ tự động phân tích — hoặc bấm "Tạo phân tích" để xem ngay.'
                    : 'Chưa có bản phân tích. Bấm "Tạo phân tích" để hệ thống diễn giải hồ sơ bên dưới.')
                : 'Cần hoàn thành ít nhất một bài để có phân tích.'}
              {' '}Phần số liệu & đề xuất bên dưới luôn sẵn có.
            </p>
          )}
        </CardBody>
      </Card>

      <Card>
        <CardHeader
          title={vaiTro === 'gv' ? 'Phân tích năng lực (đề xuất cho GV)' : 'Nhận xét & gợi ý cho em'}
          subtitle={`Dựa trên ${pt.tong_hoan_thanh} bài đã hoàn thành · ${TIN_CAY[pt.do_tin_cay] || ''}`}
          action={<XuHuongBadge xh={pt.xu_huong} />}
        />
        <CardBody className="flex flex-col gap-4">
          {!pt.du_lieu_du && (
            <p className="text-sm text-warning bg-warning-soft rounded-md px-3 py-2">
              Số liệu còn ít — nhận định mang tính tham khảo, sẽ chính xác hơn khi luyện thêm.
            </p>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <p className="text-sm font-semibold text-success mb-1">✅ Điểm mạnh</p>
              {pt.diem_manh.length === 0 ? (
                <p className="text-sm text-muted">Chưa xác định rõ.</p>
              ) : (
                <ul className="text-sm text-ink list-disc pl-5 flex flex-col gap-0.5">
                  {pt.diem_manh.map((r, i) => (
                    <li key={i}>{r.ten} <b className="text-success">{r.diem_thanh_thao}%</b></li>
                  ))}
                </ul>
              )}
            </div>
            <div>
              <p className="text-sm font-semibold text-danger mb-1">🎯 Cần cải thiện</p>
              {pt.diem_yeu.length === 0 ? (
                <p className="text-sm text-muted">Không có dạng nào đáng lo. 👍</p>
              ) : (
                <ul className="text-sm text-ink flex flex-col gap-1.5">
                  {pt.diem_yeu.map((r, i) => (
                    <li key={i} className="flex items-center justify-between gap-2">
                      <span>• {r.ten} <b className="text-danger">{r.diem_thanh_thao}%</b></span>
                      {onLuyen && r.dang_id && (
                        <Button size="sm" onClick={() => onLuyen(r)}>Luyện ngay</Button>
                      )}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>

          {deXuat?.length > 0 && (
            <div className="rounded-lg bg-primary-soft/60 px-4 py-3">
              <p className="text-sm font-semibold text-primary mb-1">💡 Đề xuất</p>
              <ul className="text-sm text-ink list-disc pl-5 flex flex-col gap-1">
                {deXuat.map((t, i) => <li key={i}>{t}</li>)}
              </ul>
            </div>
          )}
        </CardBody>
      </Card>

      {sauNhanXet}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card>
          <CardHeader title="Theo dạng bài" subtitle="Mức thành thạo từng dạng (yếu → mạnh)" />
          <CardBody>
            {pt.theo_dang.length === 0
              ? <p className="text-sm text-muted">Chưa có dữ liệu.</p>
              : pt.theo_dang.map((r, i) => <HangNhom key={i} r={r} />)}
          </CardBody>
        </Card>
        <Card>
          <CardHeader title="Theo loại câu hỏi" subtitle="Mức thành thạo từng loại" />
          <CardBody>
            {pt.theo_loai_cau.length === 0
              ? <p className="text-sm text-muted">Chưa có dữ liệu.</p>
              : pt.theo_loai_cau.map((r, i) => <HangNhom key={i} r={r} />)}
          </CardBody>
        </Card>
      </div>
    </div>
  )
}
