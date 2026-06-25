import { useEffect, useMemo, useState } from 'react'
import { api } from '../../api'
import { Badge, Button, Card, CardBody, CardHeader, Input, Select } from '../../components/ui'
import SuaTaiKhoanModal from '../../components/admin/SuaTaiKhoanModal'

export default function QuanLyLop() {
  const [lops, setLops] = useState([])
  const [gvList, setGvList] = useState([])
  const [error, setError] = useState('')
  const [newTen, setNewTen] = useState('')
  const [newGv, setNewGv] = useState('')
  const [q, setQ] = useState('')
  const [moRong, setMoRong] = useState({})
  const [suaLop, setSuaLop] = useState(null) // {id, ten, gv_id}
  const [suaHs, setSuaHs] = useState(null)

  function tai() {
    api.adminLopChiTiet().then(setLops).catch((e) => setError(e.message))
    api.adminUsers().then((us) => setGvList(us.filter((u) => u.vai_tro === 'gv'))).catch(() => {})
  }
  useEffect(tai, [])

  const gvOptions = [
    { value: '', label: '— Chưa phân công —' },
    ...gvList.map((g) => ({ value: String(g.id), label: g.ho_ten })),
  ]
  const lopOptions = [
    { value: '', label: '— Không gán lớp —' },
    ...lops.map((l) => ({ value: String(l.id), label: l.ten })),
  ]

  async function themLop() {
    if (!newTen.trim()) return
    try {
      await api.adminCreateLop({ ten: newTen.trim(), gv_id: newGv ? Number(newGv) : null })
      setNewTen(''); setNewGv(''); tai()
    } catch (e) { setError(e.message) }
  }
  async function luuSuaLop() {
    try {
      await api.adminUpdateLop(suaLop.id, {
        ten: suaLop.ten,
        gv_id: suaLop.gv_id ? Number(suaLop.gv_id) : null,
      })
      setSuaLop(null); tai()
    } catch (e) { setError(e.message) }
  }
  async function xoaLop(l) {
    if (!window.confirm(`Xóa lớp "${l.ten}"? Học sinh trong lớp sẽ bị gỡ khỏi lớp.`)) return
    try { await api.adminDeleteLop(l.id); tai() }
    catch (e) { setError(e.message) }
  }
  async function doiTrangThaiHs(h) {
    await api.adminSetUserStatus(h.id, h.trang_thai === 'hoat_dong' ? 'khoa' : 'hoat_dong')
    tai()
  }
  async function xoaHs(h) {
    if (!window.confirm(`Xóa học sinh "${h.ho_ten}"?`)) return
    try { await api.adminDeleteUser(h.id); tai() }
    catch (e) { setError(e.message) }
  }

  const loc = useMemo(() => {
    const kw = q.trim().toLowerCase()
    return kw ? lops.filter((l) => l.ten.toLowerCase().includes(kw)) : lops
  }, [lops, q])

  return (
    <div className="flex flex-col gap-5">
      {error && (
        <p className="text-danger text-sm bg-danger-soft rounded-md px-3 py-2">
          {error} <button onClick={() => setError('')} className="ml-2 font-bold">✕</button>
        </p>
      )}

      <Card>
        <CardHeader title="Thêm lớp" subtitle="Tên lớp + giáo viên phụ trách (tùy chọn)" />
        <CardBody>
          <div className="grid sm:grid-cols-3 gap-3 items-end">
            <Input label="Tên lớp" value={newTen} onChange={(e) => setNewTen(e.target.value)} placeholder="vd: 12A2" />
            <Select label="Giáo viên phụ trách" value={newGv} onChange={(e) => setNewGv(e.target.value)} options={gvOptions} />
            <Button onClick={themLop}>Thêm lớp</Button>
          </div>
        </CardBody>
      </Card>

      <Card>
        <CardHeader title="Danh sách lớp" subtitle={`${loc.length}/${lops.length} lớp`} />
        <CardBody className="flex flex-col gap-3">
          <Input label="Tìm lớp" placeholder="Tên lớp..." value={q} onChange={(e) => setQ(e.target.value)} />
          <div className="flex flex-col gap-2">
            {loc.map((l) => (
              <div key={l.id} className="rounded-lg border border-border">
                {suaLop?.id === l.id ? (
                  <div className="grid sm:grid-cols-3 gap-3 items-end p-3">
                    <Input label="Tên lớp" value={suaLop.ten}
                      onChange={(e) => setSuaLop((s) => ({ ...s, ten: e.target.value }))} />
                    <Select label="Giáo viên phụ trách" value={suaLop.gv_id ? String(suaLop.gv_id) : ''}
                      onChange={(e) => setSuaLop((s) => ({ ...s, gv_id: e.target.value }))} options={gvOptions} />
                    <div className="flex gap-2">
                      <Button onClick={luuSuaLop}>Lưu</Button>
                      <Button variant="secondary" onClick={() => setSuaLop(null)}>Hủy</Button>
                    </div>
                  </div>
                ) : (
                  <div className="flex items-center justify-between gap-2 p-3 flex-wrap">
                    <div>
                      <span className="font-bold text-ink">{l.ten}</span>
                      <span className="text-muted text-sm"> · GV: {l.gv_ten || '— chưa phân công —'} · {l.so_hoc_sinh} học sinh</span>
                    </div>
                    <div className="flex gap-1">
                      <Button size="sm" variant="ghost" onClick={() => setMoRong((m) => ({ ...m, [l.id]: !m[l.id] }))}>
                        {moRong[l.id] ? 'Ẩn học sinh' : 'Xem học sinh'}
                      </Button>
                      <Button size="sm" variant="ghost" onClick={() => setSuaLop({ id: l.id, ten: l.ten, gv_id: l.gv_id || '' })}>Sửa</Button>
                      <Button size="sm" variant="ghost" onClick={() => xoaLop(l)}><span className="text-danger">Xóa</span></Button>
                    </div>
                  </div>
                )}

                {moRong[l.id] && (
                  <div className="border-t border-border px-3 py-2 flex flex-col gap-1">
                    {l.hoc_sinhs.length === 0 && <p className="text-sm text-muted py-1">Lớp chưa có học sinh.</p>}
                    {l.hoc_sinhs.map((h) => (
                      <div key={h.id} className="flex items-center justify-between gap-2 py-1.5 border-b border-border last:border-0">
                        <div className="text-sm">
                          <span className="text-ink font-medium">{h.ho_ten}</span>
                          <span className="text-muted"> ({h.dang_nhap})</span>
                          <Badge className="ml-2" tone={h.trang_thai === 'hoat_dong' ? 'success' : 'danger'}>
                            {h.trang_thai === 'hoat_dong' ? 'Hoạt động' : 'Đã khóa'}
                          </Badge>
                        </div>
                        <div className="flex gap-1">
                          <Button size="sm" variant="ghost" onClick={() => setSuaHs(h)}>Sửa</Button>
                          <Button size="sm" variant="ghost" onClick={() => doiTrangThaiHs(h)}>
                            {h.trang_thai === 'hoat_dong' ? 'Khóa' : 'Mở khóa'}
                          </Button>
                          <Button size="sm" variant="ghost" onClick={() => xoaHs(h)}><span className="text-danger">Xóa</span></Button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
            {loc.length === 0 && <p className="text-sm text-muted">Không có lớp phù hợp.</p>}
          </div>
        </CardBody>
      </Card>

      {suaHs && (
        <SuaTaiKhoanModal
          user={suaHs}
          showLop
          lopOptions={lopOptions}
          onClose={() => setSuaHs(null)}
          onSaved={() => { setSuaHs(null); tai() }}
        />
      )}
    </div>
  )
}
