/*
 * ThiThu — chế độ đề ôn thi THPT cho HS (C1):
 * danh sách đề → làm bài có đồng hồ (autosave, lưới câu) → nộp → kết quả từng câu
 * + nút "Luyện lại với gia sư" cho câu sai (tạo phiên Socratic bài đó).
 *
 * Trong lúc thi KHÔNG có gợi ý/gia sư — đúng tinh thần phòng thi; đồng hồ do server
 * quyết định (client chỉ hiển thị), hết giờ server tự chốt bài.
 */

import { useEffect, useRef, useState } from 'react'
import { api } from '../../api'
import { Badge, Button, Card, CardBody, CardHeader } from '../../components/ui'
import Formula from '../../components/Formula'
import { dinhDangThoiGian } from '../../utils/format'

const TEN_PHAN = { I: 'Phần I — Trắc nghiệm ABCD', II: 'Phần II — Đúng/Sai 4 ý', III: 'Phần III — Trả lời ngắn' }

function renderVanBan(text) {
  return String(text ?? '')
    .split(/(\$[^$]+\$)/g)
    .map((p, i) =>
      p.startsWith('$') ? <Formula key={i} latex={p.slice(1, -1)} /> : <span key={i}>{p}</span>
    )
}

function daTraLoi(gia_tri) {
  if (gia_tri == null || gia_tri === '') return false
  if (typeof gia_tri === 'object') return Object.keys(gia_tri).length > 0
  return true
}

/* ───────────────────────── Danh sách đề ───────────────────────── */

function DanhSachDe({ onVaoThi, onXemKetQua, focusId, onFocusDone }) {
  const [ds, setDs] = useState(null)
  const [error, setError] = useState('')
  const [noiBatId, setNoiBatId] = useState(null)

  useEffect(() => {
    api.deThiDs().then(setDs).catch((e) => setError(e.message))
  }, [])

  // focusId: { id, ts } | null — HS bấm thông báo "Đề thi mới" ở chuông, nhảy tới + làm nổi
  // bật tạm thời đúng đề đó trong danh sách.
  useEffect(() => {
    if (!focusId || !ds) return
    let cuonTimeout, tatNoiBat
    const batDau = setTimeout(() => {
      if (!ds.some((de) => de.id === focusId.id)) { onFocusDone?.(); return }
      setNoiBatId(focusId.id)
      cuonTimeout = setTimeout(() => {
        document.getElementById(`de-thi-${focusId.id}`)
          ?.scrollIntoView({ behavior: 'smooth', block: 'center' })
      }, 150)
      tatNoiBat = setTimeout(() => setNoiBatId(null), 3000)
      onFocusDone?.()
    }, 0)
    return () => {
      clearTimeout(batDau)
      clearTimeout(cuonTimeout)
      clearTimeout(tatNoiBat)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [focusId, ds])

  if (error) return <p className="text-sm text-danger">{error}</p>
  if (!ds) return <p className="text-sm text-muted">Đang tải danh sách đề...</p>
  if (ds.length === 0) {
    return (
      <Card>
        <CardBody className="py-10 text-center text-muted">
          Thầy/cô chưa phát hành đề thi thử nào.
        </CardBody>
      </Card>
    )
  }
  return (
    <div className="grid md:grid-cols-2 gap-3">
      {ds.map((de) => {
        const bai = de.bai_gan_nhat
        return (
          <Card key={de.id} id={`de-thi-${de.id}`}
            className={noiBatId === de.id ? 'ring-2 ring-primary transition-shadow' : ''}>
            <CardBody className="pt-4 flex flex-col gap-2">
              <p className="font-bold text-ink">{de.ten}</p>
              <div className="flex gap-2 flex-wrap items-center text-sm text-muted">
                <Badge tone="neutral">{de.thoi_gian_phut} phút</Badge>
              </div>
              {bai?.trang_thai === 'da_nop' && (
                <p className="text-sm text-ink">
                  Lần gần nhất: <b className="text-primary">{bai.diem}/{bai.diem_toi_da} điểm</b>
                  {bai.lam_trong_giay != null && (
                    <> · Làm trong <b>{dinhDangThoiGian(bai.lam_trong_giay)}</b></>
                  )}
                  {bai.nop_luc && (
                    <> · Ngày <b>{new Date(bai.nop_luc).toLocaleDateString('vi-VN')}</b></>
                  )}
                </p>
              )}
              <div className="flex gap-2 mt-1">
                {bai?.trang_thai === 'dang_thi' ? (
                  <Button className="flex-1" variant="warning" onClick={() => onVaoThi(de.id)}>
                    Làm tiếp (đang thi dở)
                  </Button>
                ) : (
                  <Button className="flex-1" onClick={() => onVaoThi(de.id)}>
                    {bai ? 'Thi lại' : 'Vào thi'}
                  </Button>
                )}
                {bai?.trang_thai === 'da_nop' && (
                  <Button className="flex-1" variant="secondary"
                    onClick={() => onXemKetQua(bai.bai_thi_id)}>
                    Xem kết quả
                  </Button>
                )}
              </div>
            </CardBody>
          </Card>
        )
      })}
    </div>
  )
}

/* ───────────────────────── Màn làm bài ───────────────────────── */

function ManLamBai({ bai, onNopXong }) {
  const [cauIdx, setCauIdx] = useState(0)
  const [baiLam, setBaiLam] = useState(bai.bai_lam || {})
  const [conLai, setConLai] = useState(bai.con_lai_giay)
  const [dangNop, setDangNop] = useState(false)
  const [error, setError] = useState('')
  const baiLamRef = useRef(baiLam)
  baiLamRef.current = baiLam
  const daNopRef = useRef(false)

  // Đồng hồ đếm ngược cục bộ; về 0 → tự nộp (server vẫn là trọng tài cuối).
  useEffect(() => {
    const t = setInterval(() => setConLai((s) => s - 1), 1000)
    return () => clearInterval(t)
  }, [])
  useEffect(() => {
    if (conLai <= 0 && !daNopRef.current) nop()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [conLai])

  // Autosave mỗi 20 giây
  useEffect(() => {
    const t = setInterval(() => {
      if (!daNopRef.current) api.deThiLuu(bai.bai_thi_id, baiLamRef.current).catch(() => {})
    }, 20000)
    return () => clearInterval(t)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  function datDapAn(cauId, gia_tri) {
    setBaiLam((bl) => {
      const moi = { ...bl, [String(cauId)]: gia_tri }
      // lưu ngay khi đổi đáp án (không đợi chu kỳ 20s)
      api.deThiLuu(bai.bai_thi_id, moi).catch(() => {})
      return moi
    })
  }

  async function nop() {
    if (daNopRef.current) return
    daNopRef.current = true
    setDangNop(true)
    try {
      const kq = await api.deThiNop(bai.bai_thi_id, baiLamRef.current)
      onNopXong(kq)
    } catch (e) {
      daNopRef.current = false
      setError(e.message)
    } finally {
      setDangNop(false)
    }
  }

  const cau = bai.cau_list[cauIdx]
  const gia_tri = baiLam[String(cau.de_thi_cau_id)]
  const soDaLam = bai.cau_list.filter((c) => daTraLoi(baiLam[String(c.de_thi_cau_id)])).length
  const gapGio = conLai <= 300

  return (
    <div className="flex flex-col gap-4">
      {/* Thanh trên: tên đề + đồng hồ + nộp */}
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <h2 className="text-lg font-bold text-ink">{bai.ten_de}</h2>
        <div className="flex items-center gap-3">
          <span className={`font-mono text-lg font-bold px-3 py-1 rounded-md ${
            gapGio ? 'bg-danger-soft text-danger' : 'bg-surface-2 text-ink'}`}>
            ⏱ {dinhDangThoiGian(Math.max(0, conLai))}
          </span>
          <Button variant="danger" onClick={nop} disabled={dangNop}>
            {dangNop ? 'Đang nộp...' : 'Nộp bài'}
          </Button>
        </div>
      </div>
      {error && <p className="text-sm text-danger bg-danger-soft rounded-md px-3 py-2">{error}</p>}

      <div className="grid lg:grid-cols-4 gap-4">
        {/* Lưới câu */}
        <Card className="lg:col-span-1 self-start">
          <CardHeader title={`Đã làm ${soDaLam}/${bai.cau_list.length}`} />
          <CardBody className="grid grid-cols-5 lg:grid-cols-4 gap-1.5">
            {bai.cau_list.map((c, i) => {
              const lam = daTraLoi(baiLam[String(c.de_thi_cau_id)])
              return (
                <button key={c.de_thi_cau_id} onClick={() => setCauIdx(i)}
                  className={`h-8 rounded text-xs font-semibold border transition-colors ${
                    i === cauIdx
                      ? 'border-primary bg-primary text-white'
                      : lam
                        ? 'border-success bg-success-soft text-success'
                        : 'border-border bg-surface text-muted'
                  }`}>
                  {c.thu_tu}
                </button>
              )
            })}
          </CardBody>
        </Card>

        {/* Câu hiện tại */}
        <Card className="lg:col-span-3">
          <CardHeader title={`Câu ${cau.thu_tu}`} subtitle={TEN_PHAN[cau.phan]} />
          <CardBody className="flex flex-col gap-4">
            <div className="text-sm text-ink leading-relaxed">
              {renderVanBan(cau.problem.de_bai)}
            </div>
            {cau.problem.hinh_anh && (
              <img src={cau.problem.hinh_anh} alt="Hình minh họa"
                className="max-w-full sm:max-w-md rounded-md border border-border" />
            )}

            {cau.phan === 'I' && (
              <div className="flex flex-col gap-2">
                {Object.entries(cau.problem.meta?.phuong_an || {}).map(([k, v]) => (
                  <button key={k} onClick={() => datDapAn(cau.de_thi_cau_id, k)}
                    className={`text-left rounded-md border px-3 py-2 text-sm transition-colors ${
                      gia_tri === k
                        ? 'border-primary bg-primary-soft text-ink font-medium'
                        : 'border-border hover:bg-surface-2 text-ink'
                    }`}>
                    <span className="font-semibold text-primary">{k}.</span> {renderVanBan(v)}
                  </button>
                ))}
              </div>
            )}

            {cau.phan === 'II' && (
              <div className="flex flex-col gap-2">
                {(cau.problem.meta?.y || []).map((item) => {
                  const chon = (gia_tri || {})[item.ky_hieu]
                  return (
                    <div key={item.ky_hieu}
                      className="flex items-center justify-between gap-3 rounded-md border border-border px-3 py-2">
                      <div className="text-sm text-ink">
                        <span className="font-semibold text-primary">{item.ky_hieu})</span>{' '}
                        {renderVanBan(item.noi_dung_y)}
                      </div>
                      <div className="flex gap-1 shrink-0">
                        {['Dung', 'Sai'].map((da) => (
                          <button key={da}
                            onClick={() => datDapAn(cau.de_thi_cau_id,
                              { ...(gia_tri || {}), [item.ky_hieu]: da })}
                            className={`px-3 py-1 rounded text-sm font-semibold border ${
                              chon === da
                                ? da === 'Dung'
                                  ? 'bg-success text-white border-success'
                                  : 'bg-danger text-white border-danger'
                                : 'border-border text-muted hover:bg-surface-2'
                            }`}>
                            {da === 'Dung' ? 'Đ' : 'S'}
                          </button>
                        ))}
                      </div>
                    </div>
                  )
                })}
              </div>
            )}

            {cau.phan === 'III' && (
              <input
                type="text"
                value={gia_tri || ''}
                onChange={(e) => datDapAn(cau.de_thi_cau_id, e.target.value)}
                placeholder="Nhập đáp án (số)..."
                className="rounded-md border border-border px-3 py-2 text-sm max-w-xs
                  focus:outline-none focus:ring-2 focus:ring-primary/40"
              />
            )}

            <div className="flex justify-between">
              <Button variant="secondary" disabled={cauIdx === 0}
                onClick={() => setCauIdx((i) => i - 1)}>← Câu trước</Button>
              <Button variant="secondary" disabled={cauIdx === bai.cau_list.length - 1}
                onClick={() => setCauIdx((i) => i + 1)}>Câu sau →</Button>
            </div>
          </CardBody>
        </Card>
      </div>
    </div>
  )
}

/* ───────────────────────── Màn kết quả ───────────────────────── */

function ManKetQua({ kq, onQuayLai, onLuyenBai }) {
  const theoPhan = { I: [], II: [], III: [] }
  kq.cau_list.forEach((c) => theoPhan[c.phan]?.push(c))
  const diemPhan = (ds) => ds.reduce((s, c) => s + (c.diem || 0), 0).toFixed(2)

  function textDapAnDung(c) {
    const da = c.dap_an_dung || {}
    if (c.phan === 'I') return da.dap_an_dung
    if (c.phan === 'III') return da.dap_an_cuoi
    return Object.entries(da.dap_an_y || {})
      .map(([k, v]) => `${k}) ${v === 'Dung' ? 'Đ' : 'S'}`).join('  ')
  }
  function textDapAnNhap(c) {
    if (c.dap_an_nhap == null || c.dap_an_nhap === '') return '(bỏ trống)'
    if (typeof c.dap_an_nhap === 'object') {
      return Object.entries(c.dap_an_nhap)
        .map(([k, v]) => `${k}) ${v === 'Dung' ? 'Đ' : 'S'}`).join('  ') || '(bỏ trống)'
    }
    return String(c.dap_an_nhap)
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <h2 className="text-lg font-bold text-ink">Kết quả: {kq.ten_de}</h2>
        <Button variant="secondary" onClick={onQuayLai}>← Danh sách đề</Button>
      </div>

      <Card>
        <CardBody className="py-5 flex items-center gap-6 flex-wrap">
          <p className="text-4xl font-bold text-primary">
            {kq.diem}<span className="text-xl text-muted">/{kq.diem_toi_da}</span>
          </p>
          <div className="flex gap-2 flex-wrap">
            {Object.entries(theoPhan).map(([phan, ds]) =>
              ds.length > 0 && (
                <Badge key={phan} tone="neutral">
                  Phần {phan}: {diemPhan(ds)}đ ({ds.filter((c) => c.dung).length}/{ds.length} đúng)
                </Badge>
              )
            )}
          </div>
        </CardBody>
      </Card>

      <div className="flex flex-col gap-2">
        {kq.cau_list.map((c) => (
          <Card key={c.de_thi_cau_id}>
            <CardBody className="pt-4 flex flex-col gap-2">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="font-semibold text-ink">Câu {c.thu_tu}</span>
                <Badge tone="neutral">Phần {c.phan}</Badge>
                {c.dung
                  ? <Badge tone="success">✓ Đúng · +{c.diem}đ</Badge>
                  : <Badge tone="danger">{c.da_tra_loi ? `✗ Sai · ${c.diem > 0 ? `+${c.diem}đ` : '0đ'}` : 'Bỏ trống · 0đ'}</Badge>}
              </div>
              <div className="text-sm text-ink">{renderVanBan(c.problem.de_bai)}</div>
              {c.problem.hinh_anh && (
                <img src={c.problem.hinh_anh} alt="Hình minh họa"
                  className="max-w-full sm:max-w-md rounded-md border border-border" />
              )}
              {c.phan === 'I' && c.problem.meta?.phuong_an && (
                <div className="flex flex-col gap-1">
                  {Object.entries(c.problem.meta.phuong_an).map(([k, v]) => (
                    <span key={k} className="text-sm text-ink">
                      <span className="font-semibold text-primary">{k}.</span> {renderVanBan(v)}
                    </span>
                  ))}
                </div>
              )}
              {c.phan === 'II' && c.problem.meta?.y && (
                <div className="flex flex-col gap-1">
                  {c.problem.meta.y.map((item) => (
                    <span key={item.ky_hieu} className="text-sm text-ink">
                      <span className="font-semibold text-primary">{item.ky_hieu})</span>{' '}
                      {renderVanBan(item.noi_dung_y)}
                    </span>
                  ))}
                </div>
              )}
              <div className="text-sm flex flex-col sm:flex-row gap-x-6 gap-y-1">
                <span className="text-muted">Em trả lời: <b className="text-ink">{textDapAnNhap(c)}</b></span>
                <span className="text-muted">Đáp án đúng: <b className="text-success">{textDapAnDung(c)}</b></span>
              </div>
              {!c.dung && (
                <div>
                  <Button size="sm" variant="ghost" onClick={() => onLuyenBai(c.problem.id)}>
                    🎓 Luyện lại câu này với gia sư
                  </Button>
                </div>
              )}
            </CardBody>
          </Card>
        ))}
      </div>
    </div>
  )
}

/* ───────────────────────── Trang chính ───────────────────────── */

export default function ThiThu({ onLuyenBai, focusId, onFocusDone }) {
  const [man, setMan] = useState({ ten: 'ds' }) // ds | thi | ket_qua
  const [error, setError] = useState('')

  async function vaoThi(deId) {
    setError('')
    try {
      const bai = await api.deThiBatDau(deId)
      if (bai.trang_thai === 'da_nop') setMan({ ten: 'ket_qua', kq: bai })
      else setMan({ ten: 'thi', bai })
    } catch (e) { setError(e.message) }
  }

  async function xemKetQua(baiId) {
    setError('')
    try {
      const kq = await api.deThiXemBai(baiId)
      if (kq.trang_thai === 'da_nop') setMan({ ten: 'ket_qua', kq })
      else setMan({ ten: 'thi', bai: kq })
    } catch (e) { setError(e.message) }
  }

  return (
    <div className="flex flex-col gap-4">
      {man.ten === 'ds' && (
        <>
          <h2 className="text-2xl font-bold text-black">Thi thử</h2>
          {error && <p className="text-sm text-danger bg-danger-soft rounded-md px-3 py-2">{error}</p>}
          <DanhSachDe onVaoThi={vaoThi} onXemKetQua={xemKetQua}
            focusId={focusId} onFocusDone={onFocusDone} />
        </>
      )}
      {man.ten === 'thi' && (
        <ManLamBai bai={man.bai} onNopXong={(kq) => setMan({ ten: 'ket_qua', kq })} />
      )}
      {man.ten === 'ket_qua' && (
        <ManKetQua kq={man.kq} onQuayLai={() => setMan({ ten: 'ds' })} onLuyenBai={onLuyenBai} />
      )}
    </div>
  )
}
