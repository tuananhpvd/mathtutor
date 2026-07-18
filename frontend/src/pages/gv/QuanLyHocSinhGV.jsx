import { useEffect, useMemo, useState } from 'react'
import { api } from '../../api'
import { Badge, Button, Card, CardBody, CardHeader, Input, Select, Table, useConfirm } from '../../components/ui'
import SuaHocSinhModal from '../../components/gv/SuaHocSinhModal'

const FORM_RONG = { ho_ten: '', dang_nhap: '', mat_khau: '', lop_id: '' }

export default function QuanLyHocSinhGV() {
  const confirm = useConfirm()
  const [rows, setRows] = useState([])
  const [lops, setLops] = useState([])
  const [form, setForm] = useState(FORM_RONG)
  const [error, setError] = useState('')
  const [ok, setOk] = useState('')
  const [sua, setSua] = useState(null)
  const [q, setQ] = useState('')
  const [fLop, setFLop] = useState('')
  const [fTrangThai, setFTrangThai] = useState('')
  const [modalDatLai, setModalDatLai] = useState(null)  // HS đang chọn đặt lại
  const [dangDatLai, setDangDatLai] = useState(false)

  function tai() {
    api.gvHocSinh().then(setRows).catch((e) => setError(e.message))
    api.gvLop().then(setLops).catch(() => {})
  }
  useEffect(tai, [])

  const lopOptions = lops.map((l) => ({ value: String(l.id), label: l.ten }))

  async function tao(e) {
    e.preventDefault()
    setError(''); setOk('')
    try {
      await api.gvTaoHocSinh({
        ho_ten: form.ho_ten, dang_nhap: form.dang_nhap,
        mat_khau: form.mat_khau, lop_id: Number(form.lop_id),
      })
      setOk(`Đã tạo học sinh ${form.dang_nhap}`)
      setForm(FORM_RONG)
      tai()
    } catch (e2) { setError(e2.message) }
  }
  async function ganLop(h, lopId) {
    if (!lopId) return
    try { await api.gvGanLopHocSinh(h.id, Number(lopId)); tai() } catch (e) { setError(e.message) }
  }
  async function doiTrangThai(h) {
    await api.gvDoiTrangThaiHocSinh(h.id, h.trang_thai === 'hoat_dong' ? 'khoa' : 'hoat_dong')
    tai()
  }
  async function xoa(h) {
    if (!await confirm(`Xóa học sinh "${h.ho_ten}"?`)) return
    try { await api.gvXoaHocSinh(h.id); tai() } catch (e) { setError(e.message) }
  }
  async function datLai() {
    if (!modalDatLai) return
    setDangDatLai(true)
    try {
      await api.gvDatLaiTienDo(modalDatLai.id)
      setModalDatLai(null)
      tai()
    } catch (e) { setError(e.message) }
    finally { setDangDatLai(false) }
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

  return (
    <div className="flex flex-col gap-5">
      {error && (
        <p className="text-danger text-sm bg-danger-soft rounded-md px-3 py-2">
          {error} <button onClick={() => setError('')} className="ml-2 font-bold">✕</button>
        </p>
      )}

      <Card>
        <CardHeader title="Thêm học sinh" subtitle="Tạo tài khoản học sinh vào lớp bạn phụ trách" />
        <CardBody>
          {lops.length === 0 ? (
            <p className="text-sm text-muted">Bạn chưa có lớp nào. Hãy tạo lớp ở mục "Quản lý lớp" trước.</p>
          ) : (
            <form onSubmit={tao} className="grid sm:grid-cols-5 gap-3 items-end">
              <Input label="Họ tên" value={form.ho_ten}
                onChange={(e) => setForm((f) => ({ ...f, ho_ten: e.target.value }))} required />
              <Input label="Tên đăng nhập" value={form.dang_nhap}
                onChange={(e) => setForm((f) => ({ ...f, dang_nhap: e.target.value }))} required />
              <Input label="Mật khẩu" type="password" value={form.mat_khau}
                onChange={(e) => setForm((f) => ({ ...f, mat_khau: e.target.value }))} required minLength={6} />
              <Select label="Lớp" value={form.lop_id}
                onChange={(e) => setForm((f) => ({ ...f, lop_id: e.target.value }))}
                options={[{ value: '', label: '— chọn lớp —' }, ...lopOptions]} required />
              <Button type="submit" disabled={!form.lop_id}>Tạo học sinh</Button>
              {ok && (
                <div className="sm:col-span-5">
                  <span className="text-sm text-success">{ok}</span>
                </div>
              )}
            </form>
          )}
        </CardBody>
      </Card>

      <Card>
        <CardHeader title="Học sinh của tôi" subtitle={`${loc.length}/${rows.length} học sinh`} />
        <CardBody className="flex flex-col gap-3">
          <div className="grid sm:grid-cols-3 gap-3">
            <Input label="Tìm kiếm" placeholder="Tên hoặc đăng nhập..."
              value={q} onChange={(e) => setQ(e.target.value)} />
            <Select label="Lớp" value={fLop} onChange={(e) => setFLop(e.target.value)}
              options={[{ value: '', label: 'Tất cả lớp' }, ...lopOptions]} />
            <Select label="Trạng thái" value={fTrangThai} onChange={(e) => setFTrangThai(e.target.value)}
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
                    onChange={(e) => ganLop(r, e.target.value)}
                    options={[{ value: '', label: '— chọn —' }, ...lopOptions]} />
                ),
              },
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
                  <div className="flex justify-end gap-1 flex-wrap">
                    <Button size="sm" variant="secondary" onClick={() => setSua(r)}>Sửa</Button>
                    <Button size="sm" variant={r.trang_thai === 'hoat_dong' ? 'warning' : 'success'} onClick={() => doiTrangThai(r)}>
                      {r.trang_thai === 'hoat_dong' ? 'Khóa' : 'Mở khóa'}
                    </Button>
                    <Button size="sm" variant="warning" onClick={() => setModalDatLai(r)}>Đặt lại tiến độ</Button>
                    <Button size="sm" variant="danger" onClick={() => xoa(r)}>Xóa</Button>
                  </div>
                ),
              },
            ]}
            rows={loc}
            rowKey={(r) => r.id}
            empty="Không có học sinh phù hợp."
          />
        </CardBody>
      </Card>

      {sua && (
        <SuaHocSinhModal hs={sua} showLop lopOptions={lopOptions}
          onClose={() => setSua(null)} onSaved={() => { setSua(null); tai() }} />
      )}

      {modalDatLai && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-surface rounded-xl shadow-xl w-full max-w-md max-h-[88vh]
            overflow-y-auto p-6 flex flex-col gap-4">
            <h2 className="text-lg font-bold text-warning">⚠️ Đặt lại tiến độ: {modalDatLai.ho_ten}</h2>
            <p className="text-sm text-muted">
              Sau khi xác nhận, các thông tin sau sẽ bị ẩn đi và <strong>không thể hoàn tác</strong>:
            </p>
            <ul className="text-sm bg-warning-soft rounded-lg px-4 py-3 flex flex-col gap-1 list-disc list-inside text-warning">
              <li>Toàn bộ phiên học và lịch sử hội thoại</li>
              <li>Điểm số và tiến độ theo chuyên đề</li>
              <li>Phân tích năng lực đã lưu</li>
            </ul>
            <p className="text-sm text-muted">Cờ theo dõi hành vi vẫn được giữ lại.</p>
            <div className="flex justify-end gap-2">
              <Button variant="secondary" onClick={() => setModalDatLai(null)}>Hủy</Button>
              <Button
                variant="warning"
                onClick={datLai}
                disabled={dangDatLai}
              >
                {dangDatLai ? 'Đang đặt lại...' : 'Xác nhận đặt lại'}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
