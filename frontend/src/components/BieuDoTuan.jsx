import { Card, CardBody, CardHeader } from './ui'

/* Diễn biến tuần học — combo chart (cột + đường) trong CÙNG một vùng vẽ, CHUNG một trục
   tung. Hai chuỗi cùng đơn vị "bài" nên 1 trục là đủ (không dual-axis): cột = số bài hoàn
   thành; đường = trong đó số bài TỰ LÀM không cần gợi ý (luôn ≤ cột) — đường bám sát cột
   dần nghĩa là học sinh đang tự lập hơn.
   Tuần là tuần HỌC tương đối của riêng HS (tuan_so: Tuần 1 = 7 ngày đầu kể từ phiên luyện
   tập đầu tiên của em đó), không phải tuần lịch của năm.
   data = payload /progress/me/hieu-qua hoặc /progress/students/{id}/hieu-qua. */

// Kích thước hệ toạ độ SVG (viewBox — hiển thị co giãn theo bề rộng card, chữ không méo
// vì giữ nguyên tỉ lệ khung, không dùng preserveAspectRatio="none").
const W = 600
const H = 230
const LE = 34   // lề trái (nhãn trục tung)
const DUOI = 26 // lề dưới (nhãn tuần)
const TREN = 12

// Bước trục tung "đẹp": bước nhỏ nhất sao cho ≤ 5 khoảng phủ hết giá trị lớn nhất;
// trần = bội số nhỏ nhất của bước ≥ max THỰC TẾ (không đệm cố định 4 khoảng).
const BUOC_DEP = [1, 2, 5, 10, 20, 50, 100, 200, 500]

export default function BieuDoTuan({ data, tieu_de = 'Diễn biến các tuần học gần nhất' }) {
  const tuan = data?.theo_tuan
  if (!data) return null
  const coBai = tuan?.some((t) => t.so_bai > 0)

  const maxBai = Math.max(...(tuan || []).map((t) => t.so_bai), 1)
  const buocTruc = BUOC_DEP.find((b) => Math.ceil(maxBai / b) <= 5) ?? Math.ceil(maxBai / 5)
  const soKhoang = Math.ceil(maxBai / buocTruc)
  const yMax = buocTruc * soKhoang
  const cao = H - TREN - DUOI
  const rong = W - LE - 6
  const oTuan = tuan?.length ? rong / tuan.length : rong
  const beCot = Math.min(oTuan * 0.55, 44)
  const yCua = (v) => TREN + (1 - v / yMax) * cao
  const xGiua = (i) => LE + oTuan * i + oTuan / 2

  const diemDuong = (tuan || []).map((t, i) => ({
    x: xGiua(i), y: yCua(t.so_tu_lam ?? 0), v: t.so_tu_lam ?? 0,
  }))

  return (
    <Card>
      <CardHeader title={tieu_de}
        subtitle="Tuần 1 = tuần bắt đầu luyện tập · Cột: bài hoàn thành mỗi tuần · Đường: trong đó tự làm không cần gợi ý — đường càng bám sát cột càng tự lập" />
      <CardBody>
        {!coBai ? (
          <p className="text-sm text-muted">Chưa có bài hoàn thành nào trong các tuần gần đây.</p>
        ) : (
          <div className="flex flex-col gap-2">
            {/* Chú giải (2 chuỗi → luôn có) */}
            <div className="flex gap-x-4 gap-y-1 flex-wrap text-xs text-ink">
              <span className="inline-flex items-center gap-1.5">
                <span className="h-3 w-3 rounded-sm inline-block bg-primary" />
                Bài hoàn thành
              </span>
              <span className="inline-flex items-center gap-1.5">
                <span className="inline-flex items-center">
                  <span className="h-0.5 w-2.5 inline-block bg-success" />
                  <span className="h-2 w-2 rounded-full inline-block bg-success -mx-0.5" />
                  <span className="h-0.5 w-2.5 inline-block bg-success" />
                </span>
                Tự làm không cần gợi ý
              </span>
            </div>

            <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-auto" role="img"
              aria-label="Biểu đồ số bài hoàn thành và số bài tự làm không cần gợi ý theo tuần học">
              {/* Lưới ngang + nhãn trục tung (nét mảnh, lùi về sau) */}
              {Array.from({ length: soKhoang + 1 }, (_, k) => k * buocTruc).map((v) => (
                <g key={v}>
                  <line x1={LE} y1={yCua(v)} x2={W - 6} y2={yCua(v)}
                    stroke="var(--color-border)" strokeWidth="1" />
                  <text x={LE - 6} y={yCua(v) + 3.5} textAnchor="end" fontSize="10"
                    fill="var(--color-muted)">{v}</text>
                </g>
              ))}

              {/* Cột: số bài hoàn thành */}
              {tuan.map((t, i) => t.so_bai > 0 && (
                <g key={t.tuan_so}>
                  <rect x={xGiua(i) - beCot / 2} y={yCua(t.so_bai)} width={beCot}
                    height={cao + TREN - yCua(t.so_bai)} rx="4" fill="var(--color-primary)"
                    opacity="0.85">
                    <title>{`Tuần ${t.tuan_so}: ${t.so_bai} bài hoàn thành, ${t.so_tu_lam ?? 0} bài tự làm`}</title>
                  </rect>
                  <text x={xGiua(i)} y={yCua(t.so_bai) - 4} textAnchor="middle" fontSize="10"
                    fontWeight="600" fill="var(--color-ink)">{t.so_bai}</text>
                </g>
              ))}

              {/* Đường + chấm: số bài tự làm không cần gợi ý (cùng trục "bài") */}
              <polyline fill="none" stroke="var(--color-success)" strokeWidth="2"
                strokeLinecap="round" strokeLinejoin="round"
                points={diemDuong.map((d) => `${d.x},${d.y}`).join(' ')} />
              {diemDuong.map((d, i) => (
                <circle key={i} cx={d.x} cy={d.y} r="3.5" fill="var(--color-success)"
                  stroke="var(--color-surface)" strokeWidth="1.5">
                  <title>{`Tuần ${tuan[i].tuan_so}: ${d.v} bài tự làm không cần gợi ý`}</title>
                </circle>
              ))}

              {/* Nhãn tuần học (tương đối theo mốc của HS) */}
              {tuan.map((t, i) => (
                <text key={t.tuan_so} x={xGiua(i)} y={H - 8} textAnchor="middle" fontSize="10"
                  fill="var(--color-muted)">{`Tuần ${t.tuan_so}`}</text>
              ))}
            </svg>
          </div>
        )}
      </CardBody>
    </Card>
  )
}
