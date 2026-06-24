import { useEffect, useState } from 'react'
import { api } from '../../api'
import { Badge, Button, Card, CardBody, CardHeader, Input, Select, Table } from '../../components/ui'

const FORM_RONG = { ho_ten: '', dang_nhap: '', mat_khau: '', vai_tro: 'hs', lop_id: '' }

export default function QuanLyTaiKhoan() {
  const [rows, setRows] = useState([])
  const [form, setForm] = useState(FORM_RONG)
  const [error, setError] = useState('')
  const [ok, setOk] = useState('')

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
        lop_id: form.lop_id ? Number(form.lop_id) : null,
      })
      setOk(`Đã tạo tài khoản ${form.dang_nhap}`)
      setForm(FORM_RONG)
      tai()
    } catch (e2) {
      setError(e2.message)
    }
  }

  async function doiTrangThai(u) {
    const moi = u.trang_thai === 'hoat_dong' ? 'khoa' : 'hoat_dong'
    await api.adminSetUserStatus(u.id, moi)
    tai()
  }

  return (
    <div className="flex flex-col gap-5">
      <Card>
        <CardHeader title="Tạo tài khoản" subtitle="Giáo viên hoặc học sinh" />
        <CardBody>
          <form onSubmit={tao} className="grid sm:grid-cols-5 gap-3 items-end">
            <Input label="Họ tên" value={form.ho_ten}
              onChange={(e) => setForm((f) => ({ ...f, ho_ten: e.target.value }))} required />
            <Input label="Đăng nhập" value={form.dang_nhap}
              onChange={(e) => setForm((f) => ({ ...f, dang_nhap: e.target.value }))} required />
            <Input label="Mật khẩu" type="password" value={form.mat_khau}
              onChange={(e) => setForm((f) => ({ ...f, mat_khau: e.target.value }))} required />
            <Select label="Vai trò" value={form.vai_tro}
              onChange={(e) => setForm((f) => ({ ...f, vai_tro: e.target.value }))}
              options={[{ value: 'hs', label: 'Học sinh' }, { value: 'gv', label: 'Giáo viên' }]} />
            <Input label="Lớp (id)" value={form.lop_id}
              onChange={(e) => setForm((f) => ({ ...f, lop_id: e.target.value }))} placeholder="tùy chọn" />
            <div className="sm:col-span-5 flex items-center gap-3">
              <Button type="submit">Tạo tài khoản</Button>
              {ok && <span className="text-sm text-success">{ok}</span>}
              {error && <span className="text-sm text-danger">{error}</span>}
            </div>
          </form>
        </CardBody>
      </Card>

      <Card>
        <CardHeader title="Danh sách tài khoản" subtitle={`${rows.length} tài khoản`} />
        <CardBody className="pt-0">
          <Table
            columns={[
              { key: 'id', header: '#', className: 'w-12' },
              { key: 'ho_ten', header: 'Họ tên' },
              { key: 'dang_nhap', header: 'Đăng nhập' },
              { key: 'vai_tro', header: 'Vai trò', render: (r) => r.vai_tro.toUpperCase() },
              {
                key: 'trang_thai',
                header: 'Trạng thái',
                render: (r) => (
                  <Badge tone={r.trang_thai === 'hoat_dong' ? 'success' : 'neutral'}>
                    {r.trang_thai === 'hoat_dong' ? 'Hoạt động' : 'Khóa'}
                  </Badge>
                ),
              },
              {
                key: 'hanh_dong',
                header: '',
                render: (r) =>
                  r.vai_tro !== 'admin' ? (
                    <Button size="sm" variant="secondary" onClick={() => doiTrangThai(r)}>
                      {r.trang_thai === 'hoat_dong' ? 'Khóa' : 'Mở khóa'}
                    </Button>
                  ) : null,
              },
            ]}
            rows={rows}
            rowKey={(r) => r.id}
          />
        </CardBody>
      </Card>
    </div>
  )
}
