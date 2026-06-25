import { useEffect, useMemo, useState } from 'react'
import { api } from '../../api'
import { Badge, Button, Card, CardBody, CardHeader, Input, Select } from '../../components/ui'

export default function QuanLyGiaoVien() {
  const [gvs, setGvs] = useState([])
  const [allLop, setAllLop] = useState([])
  const [error, setError] = useState('')
  const [q, setQ] = useState('')
  const [chonLop, setChonLop] = useState({}) // {gv_id: lop_id} cho dropdown phân công

  function tai() {
    api.adminGiaoVien().then(setGvs).catch((e) => setError(e.message))
    api.adminLop().then(setAllLop).catch(() => {})
  }
  useEffect(tai, [])

  async function phanCong(gvId) {
    const lopId = chonLop[gvId]
    if (!lopId) return
    try {
      await api.adminUpdateLop(Number(lopId), { gv_id: gvId })
      setChonLop((c) => ({ ...c, [gvId]: '' }))
      tai()
    } catch (e) { setError(e.message) }
  }
  async function goPhanCong(lopId) {
    try { await api.adminUpdateLop(lopId, { gv_id: null }); tai() }
    catch (e) { setError(e.message) }
  }

  const loc = useMemo(() => {
    const kw = q.trim().toLowerCase()
    return kw ? gvs.filter((g) => `${g.ho_ten} ${g.dang_nhap}`.toLowerCase().includes(kw)) : gvs
  }, [gvs, q])

  // Lớp chưa có GV (gợi ý phân công)
  const lopChuaGv = allLop.filter((l) => !l.gv_id)

  return (
    <div className="flex flex-col gap-5">
      {error && (
        <p className="text-danger text-sm bg-danger-soft rounded-md px-3 py-2">
          {error} <button onClick={() => setError('')} className="ml-2 font-bold">✕</button>
        </p>
      )}

      <Card>
        <CardHeader title="Giáo viên" subtitle={`${loc.length}/${gvs.length} giáo viên`} />
        <CardBody className="flex flex-col gap-3">
          <Input label="Tìm giáo viên" placeholder="Tên hoặc đăng nhập..."
            value={q} onChange={(e) => setQ(e.target.value)} />

          <div className="flex flex-col gap-3">
            {loc.map((g) => (
              <div key={g.id} className="rounded-lg border border-border p-3 flex flex-col gap-2">
                <div className="flex items-center justify-between flex-wrap gap-2">
                  <div>
                    <span className="font-bold text-ink">{g.ho_ten}</span>
                    <span className="text-muted text-sm"> ({g.dang_nhap})</span>
                    <Badge className="ml-2" tone={g.trang_thai === 'hoat_dong' ? 'success' : 'danger'}>
                      {g.trang_thai === 'hoat_dong' ? 'Hoạt động' : 'Đã khóa'}
                    </Badge>
                  </div>
                  <div className="flex items-end gap-2">
                    <Select className="w-40" label="Phân công lớp"
                      value={chonLop[g.id] || ''}
                      onChange={(e) => setChonLop((c) => ({ ...c, [g.id]: e.target.value }))}
                      options={[
                        { value: '', label: '— chọn lớp —' },
                        ...allLop.map((l) => ({
                          value: String(l.id),
                          label: l.gv_id && l.gv_id !== g.id ? `${l.ten} (đang: ${l.gv_ten})` : l.ten,
                        })),
                      ]} />
                    <Button size="sm" onClick={() => phanCong(g.id)}>Phân công</Button>
                  </div>
                </div>

                <div className="text-sm">
                  <span className="text-muted">Lớp phụ trách: </span>
                  {g.lops.length === 0 ? (
                    <span className="text-muted">chưa có</span>
                  ) : (
                    <span className="text-ink font-medium">{g.lops.map((l) => l.ten).join(', ')}</span>
                  )}
                </div>

                {g.lops.map((l) => (
                  <div key={l.id} className="rounded-md bg-surface-2 px-3 py-2">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-ink text-sm">{l.ten}
                        <span className="text-muted font-normal"> · {l.hoc_sinhs.length} học sinh</span>
                      </span>
                      <Button size="sm" variant="ghost" onClick={() => goPhanCong(l.id)}>
                        <span className="text-danger">Gỡ phụ trách</span>
                      </Button>
                    </div>
                    {l.hoc_sinhs.length > 0 && (
                      <p className="text-xs text-muted mt-1">
                        {l.hoc_sinhs.map((h) => h.ho_ten).join(', ')}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            ))}
            {loc.length === 0 && <p className="text-sm text-muted">Không có giáo viên phù hợp.</p>}
          </div>

          {lopChuaGv.length > 0 && (
            <p className="text-xs text-muted">
              Lớp chưa có GV phụ trách: <b>{lopChuaGv.map((l) => l.ten).join(', ')}</b>
            </p>
          )}
        </CardBody>
      </Card>
    </div>
  )
}
