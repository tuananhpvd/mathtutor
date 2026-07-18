import { useEffect, useMemo, useState } from 'react'
import { api } from '../../api'
import { Badge, Button, Card, CardBody, CardHeader, Select } from '../../components/ui'
import NoiDungLyThuyet from '../../components/NoiDungLyThuyet'

const MOI_TRANG = 10

export default function LyThuyet() {
  const [danhMuc, setDanhMuc] = useState([])
  const [ds, setDs] = useState(null)
  const [error, setError] = useState('')
  const [fChuyenDe, setFChuyenDe] = useState('')
  const [fDang, setFDang] = useState('')
  const [trang, setTrang] = useState(1)
  const [moRong, setMoRong] = useState(() => new Set())

  useEffect(() => {
    api.getDanhMuc().then(setDanhMuc).catch(() => {})
  }, [])

  useEffect(() => {
    let con = true
    setTimeout(() => {
      if (!con) return
      setError('')
      api.hsLyThuyetDs(fChuyenDe || undefined, fDang || undefined)
        .then((d) => con && setDs(d))
        .catch((e) => con && setError(e.message))
    }, 0)
    return () => { con = false }
  }, [fChuyenDe, fDang])

  const cdOptions = useMemo(
    () => [{ value: '', label: 'Tất cả chuyên đề' }, ...danhMuc.map((cd) => ({ value: String(cd.id), label: cd.ten }))],
    [danhMuc]
  )
  const dangOptions = useMemo(() => {
    if (!fChuyenDe) return [{ value: '', label: 'Tất cả dạng' }]
    const cd = danhMuc.find((c) => String(c.id) === fChuyenDe)
    return [
      { value: '', label: 'Tất cả dạng' },
      ...(cd?.dang_list || []).map((d) => ({ value: String(d.id), label: d.ten })),
    ]
  }, [danhMuc, fChuyenDe])

  function doiChuyenDe(v) {
    setFChuyenDe(v)
    setFDang('')
    setTrang(1)
  }

  function toggleMoRong(id) {
    setMoRong((s) => {
      const next = new Set(s)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
  }

  const tongTrang = ds ? Math.max(1, Math.ceil(ds.length / MOI_TRANG)) : 1
  const trangHienTai = Math.min(trang, tongTrang)
  const dsTrang = ds ? ds.slice((trangHienTai - 1) * MOI_TRANG, trangHienTai * MOI_TRANG) : []

  return (
    <div className="flex flex-col gap-4">
      <Card>
        <CardHeader title="Tóm tắt lý thuyết"
          subtitle="Xem lại lý thuyết thầy/cô đã tổng hợp theo từng chuyên đề, dạng bài." />
        <CardBody className="flex flex-col gap-3">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-xl">
            <Select label="Chuyên đề" value={fChuyenDe} onChange={(e) => doiChuyenDe(e.target.value)}
              options={cdOptions} />
            <Select label="Dạng" value={fDang}
              onChange={(e) => { setFDang(e.target.value); setTrang(1) }}
              options={dangOptions} />
          </div>

          {error && <p className="text-sm text-danger bg-danger-soft rounded-md px-3 py-2">{error}</p>}
          {!ds && !error && <p className="text-sm text-muted">Đang tải...</p>}
          {ds && ds.length === 0 && (
            <p className="text-sm text-muted text-center py-6">
              Chưa có tóm tắt lý thuyết nào phù hợp.
            </p>
          )}
        </CardBody>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {dsTrang.map((tt) => {
          const dangXem = moRong.has(tt.id)
          return (
            <Card key={tt.id}>
              <CardBody className="pt-4 flex flex-col gap-2">
                <div className="flex items-center justify-between gap-2 flex-wrap">
                  <div>
                    <p className="font-bold text-ink">{tt.tieu_de}</p>
                    <p className="text-xs text-muted">
                      {tt.chuyen_de_ten}{tt.dang_ten && <> › {tt.dang_ten}</>}
                    </p>
                  </div>
                  <Button size="sm" variant="secondary" onClick={() => toggleMoRong(tt.id)}>
                    {dangXem ? 'Thu gọn' : 'Xem nội dung'}
                  </Button>
                </div>
                {tt.tu_khoa?.length > 0 && (
                  <div className="flex flex-wrap gap-1">
                    {tt.tu_khoa.map((k) => <Badge key={k} tone="primary">{k}</Badge>)}
                  </div>
                )}
                {dangXem && (
                  <div className="mt-2 pt-3 border-t border-border">
                    <NoiDungLyThuyet noiDung={tt.noi_dung} />
                  </div>
                )}
              </CardBody>
            </Card>
          )
        })}
      </div>

      {ds && ds.length > 0 && tongTrang > 1 && (
        <div className="flex items-center justify-center gap-2">
          <Button size="sm" variant="secondary" disabled={trangHienTai <= 1}
            onClick={() => setTrang((t) => t - 1)}>‹ Trước</Button>
          <span className="text-sm text-muted">Trang {trangHienTai}/{tongTrang}</span>
          <Button size="sm" variant="secondary" disabled={trangHienTai >= tongTrang}
            onClick={() => setTrang((t) => t + 1)}>Sau ›</Button>
        </div>
      )}
    </div>
  )
}
