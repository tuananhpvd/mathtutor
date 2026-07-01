import { useEffect, useMemo, useState } from 'react'
import { api } from '../../api'
import { Badge, Button, Card, CardBody, CardHeader, Input, Select } from '../../components/ui'

const NHAN_LOAI = { TN4PA: 'Trắc nghiệm', TNDS: 'Đúng/Sai', TLN: 'Trả lời ngắn' }

export default function GiaoNhiemVu() {
  const [bais, setBais] = useState([])
  const [hocSinhs, setHocSinhs] = useState([])
  const [lops, setLops] = useState([])
  const [nhiemVus, setNhiemVus] = useState([])

  const [tieuDe, setTieuDe] = useState('')
  const [moTa, setMoTa] = useState('')
  const [hanChot, setHanChot] = useState('')
  const [chonBai, setChonBai] = useState(() => new Set())
  const [chonHs, setChonHs] = useState(() => new Set())
  const [qBai, setQBai] = useState('')
  const [fLop, setFLop] = useState('')

  const [hsDeXuat, setHsDeXuat] = useState('')
  const [deXuat, setDeXuat] = useState(null)
  const [dangDeXuat, setDangDeXuat] = useState(false)

  const [dangGui, setDangGui] = useState(false)
  const [ok, setOk] = useState('')
  const [loi, setLoi] = useState('')

  function taiNhiemVu() {
    api.gvNhiemVu().then(setNhiemVus).catch(() => {})
  }
  useEffect(() => {
    api.listProblems()
      .then((ps) => setBais((ps || []).filter((p) => p.trang_thai_duyet === 'da_duyet' && !p.bi_an)))
      .catch(() => {})
    api.gvHocSinh().then(setHocSinhs).catch(() => {})
    api.gvLop().then(setLops).catch(() => {})
    taiNhiemVu()
  }, [])

  const lopOptions = useMemo(
    () => [{ value: '', label: 'Tất cả lớp' },
      ...lops.map((l) => ({ value: String(l.id), label: l.ten }))],
    [lops]
  )
  const hsLoc = useMemo(
    () => (fLop ? hocSinhs.filter((h) => String(h.lop_id) === fLop) : hocSinhs),
    [hocSinhs, fLop]
  )
  const baiLoc = useMemo(() => {
    const kw = qBai.trim().toLowerCase()
    return bais.filter((b) =>
      !kw || `${b.chuyen_de} ${b.dang_ten || ''}`.toLowerCase().includes(kw))
  }, [bais, qBai])

  function toggle(set, setter, id) {
    const next = new Set(set)
    next.has(id) ? next.delete(id) : next.add(id)
    setter(next)
  }
  function chonCaLop() {
    const next = new Set(chonHs)
    hsLoc.forEach((h) => next.add(h.id))
    setChonHs(next)
  }

  async function layDeXuat() {
    if (!hsDeXuat) return
    setDangDeXuat(true)
    setDeXuat(null)
    try {
      setDeXuat(await api.gvDeXuatNhiemVu(Number(hsDeXuat)))
    } catch (e) {
      setLoi(e.message)
    } finally {
      setDangDeXuat(false)
    }
  }
  function themBaiDeXuat() {
    if (!deXuat) return
    const next = new Set(chonBai)
    deXuat.bai.forEach((b) => next.add(b.problem_id))
    setChonBai(next)
  }

  async function gui() {
    setLoi('')
    if (!tieuDe.trim()) { setLoi('Cần nhập tiêu đề'); return }
    if (chonBai.size === 0) { setLoi('Cần chọn ít nhất 1 bài'); return }
    if (chonHs.size === 0) { setLoi('Cần chọn ít nhất 1 học sinh'); return }
    setDangGui(true)
    try {
      const r = await api.gvTaoNhiemVu({
        tieu_de: tieuDe.trim(),
        mo_ta: moTa.trim() || null,
        han_chot: hanChot || null,
        problem_ids: [...chonBai],
        hoc_sinh_ids: [...chonHs],
      })
      setOk(`Đã giao nhiệm vụ cho ${r.so_hs} học sinh (${r.so_bai} bài).`)
      setTimeout(() => setOk(''), 4000)
      setTieuDe(''); setMoTa(''); setHanChot('')
      setChonBai(new Set()); setChonHs(new Set()); setDeXuat(null)
      taiNhiemVu()
    } catch (e) {
      setLoi(e.message)
    } finally {
      setDangGui(false)
    }
  }

  async function xoa(nv) {
    if (!window.confirm(`Xóa nhiệm vụ "${nv.tieu_de}"?`)) return
    try { await api.gvXoaNhiemVu(nv.id); taiNhiemVu() } catch (e) { setLoi(e.message) }
  }

  return (
    <div className="flex flex-col gap-4">
      <Card>
        <CardHeader title="Tạo nhiệm vụ" subtitle="Giao bài cho học sinh / cả lớp, có hạn nộp" />
        <CardBody className="flex flex-col gap-4">
          <div className="grid sm:grid-cols-3 gap-3">
            <Input label="Tiêu đề" value={tieuDe} onChange={(e) => setTieuDe(e.target.value)}
              placeholder="VD: Luyện cực trị cuối tuần" />
            <Input label="Hạn nộp (tùy chọn)" type="date" value={hanChot}
              onChange={(e) => setHanChot(e.target.value)} />
            <Input label="Mô tả (tùy chọn)" value={moTa} onChange={(e) => setMoTa(e.target.value)}
              placeholder="Ghi chú cho học sinh" />
          </div>

          {/* Đề xuất theo điểm yếu */}
          <div className="rounded-xl border border-border bg-surface-2/40 p-3 flex flex-col gap-2">
            <p className="text-sm font-semibold text-ink">💡 Gợi ý bài theo điểm yếu</p>
            <div className="flex flex-wrap items-end gap-2">
              <div className="min-w-[200px]">
                <Select label="Chọn học sinh để gợi ý" value={hsDeXuat}
                  onChange={(e) => setHsDeXuat(e.target.value)}
                  options={[{ value: '', label: '— Chọn học sinh —' },
                    ...hocSinhs.map((h) => ({ value: String(h.id), label: h.ho_ten }))]} />
              </div>
              <Button size="sm" variant="secondary" onClick={layDeXuat}
                disabled={!hsDeXuat || dangDeXuat}>
                {dangDeXuat ? 'Đang lấy...' : 'Lấy gợi ý'}
              </Button>
              {deXuat && deXuat.bai.length > 0 && (
                <Button size="sm" onClick={themBaiDeXuat}>
                  + Thêm {deXuat.bai.length} bài gợi ý vào danh sách
                </Button>
              )}
            </div>
            {deXuat && (
              deXuat.bai.length === 0 ? (
                <p className="text-xs text-muted">
                  Chưa có bài gợi ý phù hợp (HS chưa đủ dữ liệu điểm yếu, hoặc đã làm hết bài cùng dạng).
                </p>
              ) : (
                <p className="text-xs text-muted">
                  Dạng yếu: {deXuat.dang_yeu.join(', ') || '—'} · {deXuat.bai.length} bài đề xuất.
                </p>
              )
            )}
          </div>

          <div className="grid lg:grid-cols-2 gap-4">
            {/* Chọn bài */}
            <div className="flex flex-col gap-2">
              <div className="flex items-center justify-between">
                <p className="text-sm font-semibold text-ink">Chọn bài ({chonBai.size})</p>
                <input
                  value={qBai} onChange={(e) => setQBai(e.target.value)}
                  placeholder="Tìm bài..."
                  className="rounded-md border border-border px-2 py-1 text-xs w-36" />
              </div>
              <div className="max-h-72 overflow-y-auto rounded-lg border border-border divide-y divide-border">
                {baiLoc.length === 0 ? (
                  <p className="text-sm text-muted px-3 py-4">Không có bài.</p>
                ) : baiLoc.map((b) => (
                  <label key={b.id}
                    className="flex items-center gap-2 px-3 py-2 hover:bg-surface-2 cursor-pointer">
                    <input type="checkbox" checked={chonBai.has(b.id)}
                      onChange={() => toggle(chonBai, setChonBai, b.id)} />
                    <span className="text-sm text-ink flex-1 min-w-0 truncate">
                      {b.chuyen_de}{b.dang_ten ? ` › ${b.dang_ten}` : ''}
                    </span>
                    <Badge tone="primary">{NHAN_LOAI[b.loai_cau] || b.loai_cau}</Badge>
                  </label>
                ))}
              </div>
            </div>

            {/* Chọn học sinh */}
            <div className="flex flex-col gap-2">
              <div className="flex items-center justify-between gap-2">
                <p className="text-sm font-semibold text-ink">Chọn học sinh ({chonHs.size})</p>
                <div className="flex items-center gap-2">
                  <select value={fLop} onChange={(e) => setFLop(e.target.value)}
                    className="rounded-md border border-border px-2 py-1 text-xs">
                    {lopOptions.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
                  </select>
                  <Button size="sm" variant="secondary" onClick={chonCaLop}>Chọn cả lớp</Button>
                </div>
              </div>
              <div className="max-h-72 overflow-y-auto rounded-lg border border-border divide-y divide-border">
                {hsLoc.length === 0 ? (
                  <p className="text-sm text-muted px-3 py-4">Không có học sinh.</p>
                ) : hsLoc.map((h) => (
                  <label key={h.id}
                    className="flex items-center gap-2 px-3 py-2 hover:bg-surface-2 cursor-pointer">
                    <input type="checkbox" checked={chonHs.has(h.id)}
                      onChange={() => toggle(chonHs, setChonHs, h.id)} />
                    <span className="text-sm text-ink flex-1">{h.ho_ten}</span>
                    {h.trang_thai === 'khoa' && <Badge tone="danger">Khóa</Badge>}
                  </label>
                ))}
              </div>
            </div>
          </div>

          {loi && <p className="text-sm text-danger">{loi}</p>}
          {ok && <p className="text-sm text-success">✓ {ok}</p>}
          <div>
            <Button onClick={gui} disabled={dangGui}>
              {dangGui ? 'Đang giao...' : 'Giao nhiệm vụ'}
            </Button>
          </div>
        </CardBody>
      </Card>

      <Card>
        <CardHeader title="Nhiệm vụ đã giao" subtitle={`${nhiemVus.length} nhiệm vụ`} />
        <CardBody className="flex flex-col gap-3">
          {nhiemVus.length === 0 ? (
            <p className="text-sm text-muted">Chưa giao nhiệm vụ nào.</p>
          ) : nhiemVus.map((nv) => (
            <div key={nv.id} className="rounded-xl border border-border px-4 py-3">
              <div className="flex items-center justify-between gap-2">
                <span className="font-semibold text-ink">{nv.tieu_de}</span>
                <Button size="sm" variant="ghost" onClick={() => xoa(nv)}>
                  <span className="text-danger">Xóa</span>
                </Button>
              </div>
              <p className="text-xs text-muted mt-0.5">
                {nv.so_bai} bài · {nv.so_hs} học sinh · {nv.so_hs_hoan_thanh}/{nv.so_hs} hoàn thành
                {nv.han_chot ? ` · hạn ${new Date(nv.han_chot).toLocaleDateString('vi-VN')}` : ''}
              </p>
              {nv.hoc_sinh.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {nv.hoc_sinh.map((h, i) => {
                    const xong = h.tong_bai > 0 && h.so_hoan_thanh >= h.tong_bai
                    return (
                      <Badge key={i} tone={xong ? 'success' : 'warning'}>
                        {h.ho_ten}: {h.so_hoan_thanh}/{h.tong_bai}
                      </Badge>
                    )
                  })}
                </div>
              )}
            </div>
          ))}
        </CardBody>
      </Card>
    </div>
  )
}
