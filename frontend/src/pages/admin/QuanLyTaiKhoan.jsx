import { useEffect, useMemo, useState } from 'react'
import { api } from '../../api'
import { Badge, Button, Card, CardBody, CardHeader, Input, Select, Table, useConfirm } from '../../components/ui'
import ImportTaiKhoanDialog from '../../components/admin/ImportTaiKhoanDialog'
import SuaTaiKhoanModal from '../../components/admin/SuaTaiKhoanModal'

const FORM_RONG = { ho_ten: '', dang_nhap: '', mat_khau: '', vai_tro: 'hs' }
const NHAN_VAI = { admin: 'Quản trị', gv: 'Giáo viên', hs: 'Học sinh' }
const MOI_TRANG_TK = 10

function PhanTrangTK({ trang, tongTrang, total, onChange }) {
  if (tongTrang <= 1) return null
  return (
    <div className="flex items-center justify-between gap-2 pt-3 border-t border-border mt-1">
      <span className="text-xs text-muted">{total} tài khoản · Trang {trang}/{tongTrang}</span>
      <div className="flex items-center gap-1">
        <Button size="sm" variant="secondary" disabled={trang === 1} onClick={() => onChange(1)}>«</Button>
        <Button size="sm" variant="secondary" disabled={trang === 1} onClick={() => onChange(trang - 1)}>‹</Button>
        <Button size="sm" variant="secondary" disabled={trang === tongTrang} onClick={() => onChange(trang + 1)}>›</Button>
        <Button size="sm" variant="secondary" disabled={trang === tongTrang} onClick={() => onChange(tongTrang)}>»</Button>
      </div>
    </div>
  )
}

export default function QuanLyTaiKhoan() {
  const confirm = useConfirm()
  const [rows, setRows] = useState([])
  const [form, setForm] = useState(FORM_RONG)
  const [error, setError] = useState('')
  const [ok, setOk] = useState('')
  const [sua, setSua] = useState(null)
  const [showImport, setShowImport] = useState(false)
  // lọc
  const [q, setQ] = useState('')
  const [fVai, setFVai] = useState('')
  const [fTrangThai, setFTrangThai] = useState('')
  const [trang, setTrang] = useState(1)

  function tai() {
    api.adminUsers().then(setRows).catch(() => {})
  }
  useEffect(tai, [])

  async function tao(e) {
    e.preventDefault()
    setError('')
    setOk('')
    try {
      await api.adminCreateUser({
        ho_ten: form.ho_ten,
        dang_nhap: form.dang_nhap,
        mat_khau: form.mat_khau,
        vai_tro: form.vai_tro,
      })
      setOk(`Đã tạo tài khoản ${form.dang_nhap}`)
      setForm(FORM_RONG)
      tai()
    } catch (e2) {
      setError(e2.message)
    }
  }

  async function doiTrangThai(u) {
    await api.adminSetUserStatus(u.id, u.trang_thai === 'hoat_dong' ? 'khoa' : 'hoat_dong')
    tai()
  }
  async function xoa(u) {
    if (!await confirm(`Xóa tài khoản "${u.ho_ten}"? Không hoàn tác.`)) return
    try { await api.adminDeleteUser(u.id); tai() }
    catch (e) { setError(e.message) }
  }

  const loc = useMemo(() => {
    const kw = q.trim().toLowerCase()
    return rows.filter((r) => {
      if (fVai && r.vai_tro !== fVai) return false
      if (fTrangThai && r.trang_thai !== fTrangThai) return false
      if (kw && !(`${r.ho_ten} ${r.dang_nhap}`.toLowerCase().includes(kw))) return false
      return true
    })
  }, [rows, q, fVai, fTrangThai])
  const tongTrangTK = Math.max(1, Math.ceil(loc.length / MOI_TRANG_TK))
  const locTrang = loc.slice((trang - 1) * MOI_TRANG_TK, trang * MOI_TRANG_TK)

  return (
    <div className="flex flex-col gap-5">
      <Card>
        <CardHeader
          title="Tạo tài khoản"
          subtitle="Giáo viên hoặc học sinh"
          action={
            <Button variant="secondary" size="sm" onClick={() => setShowImport(true)}>
              Import từ Excel
            </Button>
          }
        />
        <CardBody>
          <form onSubmit={tao} className="grid sm:grid-cols-5 gap-3 items-end">
            <Input label="Họ tên" value={form.ho_ten}
              onChange={(e) => setForm((f) => ({ ...f, ho_ten: e.target.value }))} required />
            <Input label="Tên đăng nhập" value={form.dang_nhap}
              onChange={(e) => setForm((f) => ({ ...f, dang_nhap: e.target.value }))} required />
            <Input label="Mật khẩu" type="password" value={form.mat_khau}
              onChange={(e) => setForm((f) => ({ ...f, mat_khau: e.target.value }))} required />
            <Select label="Vai trò" value={form.vai_tro}
              onChange={(e) => setForm((f) => ({ ...f, vai_tro: e.target.value }))}
              options={[{ value: 'hs', label: 'Học sinh' }, { value: 'gv', label: 'Giáo viên' }]} />
            <div className="flex flex-col">
              <Button type="submit">Tạo tài khoản</Button>
            </div>
            {(ok || error) && (
              <div className="sm:col-span-5">
                {ok && <span className="text-sm text-success">{ok}</span>}
                {error && <span className="text-sm text-danger">{error}</span>}
              </div>
            )}
          </form>
        </CardBody>
      </Card>

      <Card>
        <CardHeader title="Danh sách tài khoản" subtitle={`${loc.length}/${rows.length} tài khoản`} />
        <CardBody className="flex flex-col gap-3">
          <div className="grid sm:grid-cols-3 gap-3">
            <Input label="Tìm kiếm" placeholder="Tên hoặc đăng nhập..."
              value={q} onChange={(e) => { setQ(e.target.value); setTrang(1) }} />
            <Select label="Vai trò" value={fVai} onChange={(e) => { setFVai(e.target.value); setTrang(1) }}
              options={[{ value: '', label: 'Tất cả' }, { value: 'gv', label: 'Giáo viên' },
                { value: 'hs', label: 'Học sinh' }, { value: 'admin', label: 'Quản trị' }]} />
            <Select label="Trạng thái" value={fTrangThai} onChange={(e) => { setFTrangThai(e.target.value); setTrang(1) }}
              options={[{ value: '', label: 'Tất cả' }, { value: 'hoat_dong', label: 'Hoạt động' },
                { value: 'khoa', label: 'Đã khóa' }]} />
          </div>
          <Table
            columns={[
              { key: 'id', header: '#', className: 'w-12' },
              { key: 'ho_ten', header: 'Họ tên' },
              { key: 'dang_nhap', header: 'Đăng nhập' },
              { key: 'vai_tro', header: 'Vai trò', render: (r) => NHAN_VAI[r.vai_tro] || r.vai_tro },
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
                render: (r) =>
                  r.vai_tro === 'admin' ? <span className="text-muted">—</span> : (
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
            empty="Không có tài khoản phù hợp."
          />
          <PhanTrangTK trang={trang} tongTrang={tongTrangTK} total={loc.length} onChange={setTrang} />
        </CardBody>
      </Card>

      {sua && (
        <SuaTaiKhoanModal
          user={sua}
          showRole
          onClose={() => setSua(null)}
          onSaved={() => { setSua(null); tai() }}
        />
      )}

      {showImport && (
        <ImportTaiKhoanDialog
          onClose={() => setShowImport(false)}
          onSaved={(msg) => { setShowImport(false); setOk(msg); tai() }}
        />
      )}
    </div>
  )
}
