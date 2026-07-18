import { useEffect, useMemo, useState } from 'react'
import { api } from '../../api'
import { Badge, Button, Card, CardBody, CardHeader, Input, Select, Table, useConfirm } from '../../components/ui'
import SuaTaiKhoanModal from '../../components/admin/SuaTaiKhoanModal'

const MOI_TRANG_HS = 10

function PhanTrangHS({ trang, tongTrang, total, onChange }) {
  if (tongTrang <= 1) return null
  return (
    <div className="flex items-center justify-between gap-2 pt-3 border-t border-border mt-1">
      <span className="text-xs text-muted">{total} học sinh · Trang {trang}/{tongTrang}</span>
      <div className="flex items-center gap-1">
        <Button size="sm" variant="secondary" disabled={trang === 1} onClick={() => onChange(1)}>«</Button>
        <Button size="sm" variant="secondary" disabled={trang === 1} onClick={() => onChange(trang - 1)}>‹</Button>
        <Button size="sm" variant="secondary" disabled={trang === tongTrang} onClick={() => onChange(trang + 1)}>›</Button>
        <Button size="sm" variant="secondary" disabled={trang === tongTrang} onClick={() => onChange(tongTrang)}>»</Button>
      </div>
    </div>
  )
}

export default function QuanLyHocSinh() {
  const confirm = useConfirm()
  const [rows, setRows] = useState([])
  const [allLop, setAllLop] = useState([])
  const [error, setError] = useState('')
  const [q, setQ] = useState('')
  const [fLop, setFLop] = useState('')
  const [fTrangThai, setFTrangThai] = useState('')
  const [sua, setSua] = useState(null)
  const [trang, setTrang] = useState(1)

  function tai() {
    api.adminHocSinh().then(setRows).catch((e) => setError(e.message))
    api.adminLop().then(setAllLop).catch(() => {})
  }
  useEffect(tai, [])

  const lopOptions = [
    { value: '', label: '— Không gán lớp —' },
    ...allLop.map((l) => ({ value: String(l.id), label: l.ten })),
  ]

  async function ganLop(h, lopId) {
    try { await api.adminSetUserLop(h.id, lopId ? Number(lopId) : null); tai() }
    catch (e) { setError(e.message) }
  }
  async function doiTrangThai(h) {
    await api.adminSetUserStatus(h.id, h.trang_thai === 'hoat_dong' ? 'khoa' : 'hoat_dong')
    tai()
  }
  async function xoa(h) {
    if (!await confirm(`Xóa học sinh "${h.ho_ten}"?`)) return
    try { await api.adminDeleteUser(h.id); tai() }
    catch (e) { setError(e.message) }
  }

  const loc = useMemo(() => {
    const kw = q.trim().toLowerCase()
    return rows.filter((r) => {
      if (fLop && String(r.lop_id || '') !== fLop) return false
      if (fTrangThai && r.trang_thai !== fTrangThai) return false
      if (kw && !(`${r.ho_ten} ${r.dang_nhap}`.toLowerCase().includes(kw))) return false
      return true
    })
  }, [rows, q, fLop, fTrangThai])
  const tongTrangHS = Math.max(1, Math.ceil(loc.length / MOI_TRANG_HS))
  const locTrang = loc.slice((trang - 1) * MOI_TRANG_HS, trang * MOI_TRANG_HS)

  return (
    <div className="flex flex-col gap-5">
      {error && (
        <p className="text-danger text-sm bg-danger-soft rounded-md px-3 py-2">
          {error} <button onClick={() => setError('')} className="ml-2 font-bold">✕</button>
        </p>
      )}

      <Card>
        <CardHeader title="Học sinh" subtitle={`${loc.length}/${rows.length} học sinh`} />
        <CardBody className="flex flex-col gap-3">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <Input label="Tìm kiếm" placeholder="Tên hoặc đăng nhập..."
              value={q} onChange={(e) => { setQ(e.target.value); setTrang(1) }} />
            <Select label="Lớp" value={fLop} onChange={(e) => { setFLop(e.target.value); setTrang(1) }}
              options={[{ value: '', label: 'Tất cả lớp' },
                ...allLop.map((l) => ({ value: String(l.id), label: l.ten }))]} />
            <Select label="Trạng thái" value={fTrangThai} onChange={(e) => { setFTrangThai(e.target.value); setTrang(1) }}
              options={[{ value: '', label: 'Tất cả' }, { value: 'hoat_dong', label: 'Hoạt động' },
                { value: 'khoa', label: 'Đã khóa' }]} />
          </div>
          <Table
            columns={[
              { key: 'ho_ten', header: 'Họ tên' },
              { key: 'dang_nhap', header: 'Đăng nhập' },
              {
                key: 'lop', header: 'Lớp',
                render: (r) => (
                  <Select className="w-32" value={r.lop_id ? String(r.lop_id) : ''}
                    onChange={(e) => ganLop(r, e.target.value)} options={lopOptions} />
                ),
              },
              { key: 'gv_ten', header: 'GV phụ trách', render: (r) => r.gv_ten || '—' },
              {
                key: 'trang_thai', header: 'Trạng thái',
                render: (r) => (
                  <Badge tone={r.trang_thai === 'hoat_dong' ? 'success' : 'danger'}>
                    {r.trang_thai === 'hoat_dong' ? 'Hoạt động' : 'Đã khóa'}
                  </Badge>
                ),
              },
              {
                key: 'act', header: '',
                render: (r) => (
                  <div className="flex justify-end gap-1">
                    <Button size="sm" variant="secondary" onClick={() => setSua(r)}>Sửa</Button>
                    <Button size="sm" variant={r.trang_thai === 'hoat_dong' ? 'warning' : 'success'} onClick={() => doiTrangThai(r)}>
                      {r.trang_thai === 'hoat_dong' ? 'Khóa' : 'Mở khóa'}
                    </Button>
                    <Button size="sm" variant="danger" onClick={() => xoa(r)}>Xóa</Button>
                  </div>
                ),
              },
            ]}
            rows={locTrang}
            rowKey={(r) => r.id}
            empty="Không có học sinh phù hợp."
          />
          <PhanTrangHS trang={trang} tongTrang={tongTrangHS} total={loc.length} onChange={setTrang} />
        </CardBody>
      </Card>

      {sua && (
        <SuaTaiKhoanModal
          user={sua}
          showLop
          lopOptions={lopOptions}
          onClose={() => setSua(null)}
          onSaved={() => { setSua(null); tai() }}
        />
      )}
    </div>
  )
}
