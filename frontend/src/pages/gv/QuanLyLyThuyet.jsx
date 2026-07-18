import { useEffect, useMemo, useState } from 'react'
import { api } from '../../api'
import { Badge, Button, Card, CardBody, CardHeader, Input, Select, useConfirm } from '../../components/ui'
import NoiDungLyThuyet from '../../components/NoiDungLyThuyet'
import SoanRichText from '../../components/gv/SoanRichText'

const MOI_TRANG = 10

/* ─────────────── Form tạo/sửa 1 tóm tắt — 2 cột: nhập (trái) / xem trước (phải) ─────────────── */
function FormTomTat({ danhMuc, dangSua, onDong, onXong }) {
  const confirm = useConfirm()

  const cdOptions = useMemo(
    () => danhMuc.map((cd) => ({ value: String(cd.id), label: cd.ten })),
    [danhMuc]
  )
  const [chuyenDeId, setChuyenDeId] = useState(
    dangSua ? String(dangSua.chuyen_de_id) : (cdOptions[0]?.value || '')
  )
  const dangOptions = useMemo(() => {
    const cd = danhMuc.find((c) => String(c.id) === chuyenDeId)
    return [
      { value: '', label: '— Cấp chuyên đề (không chọn dạng) —' },
      ...(cd?.dang_list || []).map((d) => ({ value: String(d.id), label: d.ten })),
    ]
  }, [danhMuc, chuyenDeId])
  const [dangId, setDangId] = useState(dangSua?.dang_id ? String(dangSua.dang_id) : '')
  const [tieuDe, setTieuDe] = useState(dangSua?.tieu_de || '')
  const [tuKhoa, setTuKhoa] = useState((dangSua?.tu_khoa || []).join(', '))
  const [hien, setHien] = useState(dangSua?.hien ?? false)
  const [noiDung, setNoiDung] = useState(dangSua?.noi_dung || '')
  const [dangLuu, setDangLuu] = useState(false)
  const [error, setError] = useState('')

  // Trạng thái ban đầu — so sánh để biết có thay đổi chưa lưu hay không khi bấm Hủy/Đóng.
  const [banDau] = useState(() => JSON.stringify({ chuyenDeId, dangId, tieuDe, tuKhoa, hien, noiDung }))
  function coThayDoi() {
    return JSON.stringify({ chuyenDeId, dangId, tieuDe, tuKhoa, hien, noiDung }) !== banDau
  }
  async function dongNeuXacNhan() {
    if (coThayDoi() && !await confirm(
      'Bạn có thay đổi chưa lưu. Đóng lại sẽ mất các thay đổi này — vẫn đóng chứ?',
      { title: 'Có thay đổi chưa lưu', labelYes: 'Đóng, bỏ thay đổi', labelNo: 'Ở lại' }
    )) return
    onDong()
  }

  function doiChuyenDe(v) {
    setChuyenDeId(v)
    setDangId('') // đổi chuyên đề → dạng cũ (nếu có) không còn thuộc chuyên đề mới
  }

  async function luu() {
    setError('')
    if (!chuyenDeId) { setError('Chọn chuyên đề trước.'); return }
    if (!tieuDe.trim()) { setError('Nhập tiêu đề tóm tắt.'); return }
    if (!noiDung.trim() || noiDung === '<p></p>') { setError('Chưa soạn nội dung tóm tắt.'); return }
    setDangLuu(true)
    try {
      const body = {
        chuyen_de_id: Number(chuyenDeId),
        dang_id: dangId ? Number(dangId) : null,
        tieu_de: tieuDe.trim(),
        noi_dung: noiDung,
        tu_khoa: tuKhoa.split(',').map((s) => s.trim()).filter(Boolean),
        hien,
      }
      if (dangSua) await api.capNhatLyThuyet(dangSua.id, body)
      else await api.taoLyThuyet(body)
      onXong()
    } catch (e) { setError(e.message) }
    finally { setDangLuu(false) }
  }

  const tenChuyenDe = danhMuc.find((c) => String(c.id) === chuyenDeId)?.ten
  const tenDang = danhMuc.find((c) => String(c.id) === chuyenDeId)
    ?.dang_list?.find((d) => String(d.id) === dangId)?.ten

  return (
    <Card>
      <CardHeader title={dangSua ? 'Sửa tóm tắt lý thuyết' : 'Tạo tóm tắt lý thuyết mới'}
        action={<Button variant="secondary" size="sm" onClick={dongNeuXacNhan}>✕ Đóng</Button>} />
      <CardBody>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          {/* Cột trái — nhập liệu */}
          <div className="flex flex-col gap-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Select label="Chuyên đề" value={chuyenDeId} onChange={(e) => doiChuyenDe(e.target.value)}
                options={cdOptions.length ? cdOptions : [{ value: '', label: 'Chưa có chuyên đề nào' }]} />
              <Select label="Dạng (tùy chọn)" value={dangId} onChange={(e) => setDangId(e.target.value)}
                options={dangOptions} />
            </div>
            <Input label="Tiêu đề" value={tieuDe} onChange={(e) => setTieuDe(e.target.value)}
              placeholder="VD: Quy tắc tìm cực trị hàm số" />
            <Input label="Từ khóa liên quan (cách nhau bằng dấu phẩy, tùy chọn)"
              value={tuKhoa} onChange={(e) => setTuKhoa(e.target.value)}
              placeholder="VD: cực trị, đạo hàm, dấu hiệu" />

            <div>
              <p className="text-sm font-medium text-ink mb-1">Nội dung tóm tắt</p>
              <SoanRichText value={noiDung} onChange={setNoiDung} />
            </div>

            <label className="flex items-center gap-2 cursor-pointer w-fit">
              <input type="checkbox" className="h-4 w-4 accent-primary"
                checked={hien} onChange={(e) => setHien(e.target.checked)} />
              <span className="text-sm text-ink">Hiện cho học sinh xem ngay</span>
            </label>

            {error && <p className="text-sm text-danger bg-danger-soft rounded-md px-3 py-2">{error}</p>}
            <div className="flex items-center gap-2">
              <Button onClick={luu} disabled={dangLuu}>
                {dangLuu ? 'Đang lưu...' : 'Lưu tóm tắt'}
              </Button>
              <Button variant="secondary" onClick={dongNeuXacNhan} disabled={dangLuu}>
                Hủy
              </Button>
            </div>
          </div>

          {/* Cột phải — xem trước, cập nhật ngay theo nội dung đang soạn */}
          <div className="lg:sticky lg:top-4 lg:self-start">
            <p className="text-sm font-medium text-ink mb-1">Xem trước</p>
            <div className="rounded-lg border border-border bg-surface-2/40 p-4 flex flex-col gap-3
              max-h-[80vh] overflow-y-auto">
              <div>
                <p className="font-bold text-ink text-lg">{tieuDe || '(Chưa có tiêu đề)'}</p>
                <p className="text-xs text-muted">
                  {tenChuyenDe || '(Chưa chọn chuyên đề)'}{tenDang && <> › {tenDang}</>}
                </p>
              </div>
              {tuKhoa.trim() && (
                <div className="flex flex-wrap gap-1">
                  {tuKhoa.split(',').map((s) => s.trim()).filter(Boolean).map((k) => (
                    <Badge key={k} tone="primary">{k}</Badge>
                  ))}
                </div>
              )}
              <div className="pt-2 border-t border-border">
                {noiDung.trim() && noiDung !== '<p></p>'
                  ? <NoiDungLyThuyet noiDung={noiDung} />
                  : <p className="text-sm text-muted">Nội dung sẽ hiện ở đây khi bạn soạn ở cột bên trái.</p>}
              </div>
            </div>
          </div>
        </div>
      </CardBody>
    </Card>
  )
}

/* ─────────────── Trang chính ─────────────── */
export default function QuanLyLyThuyet() {
  const [danhMuc, setDanhMuc] = useState([])
  const [ds, setDs] = useState(null)
  const [formMo, setFormMo] = useState(false)
  const [dangSua, setDangSua] = useState(null)
  const [error, setError] = useState('')
  const [thongBao, setThongBao] = useState('')
  const [trang, setTrang] = useState(1)
  const [moRong, setMoRong] = useState(() => new Set())

  function toggleMoRong(id) {
    setMoRong((s) => {
      const next = new Set(s)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
  }

  function tai() {
    Promise.all([api.getDanhMuc(), api.gvLyThuyetDs()])
      .then(([dm, list]) => { setDanhMuc(dm); setDs(list) })
      .catch((e) => setError(e.message))
  }
  useEffect(tai, [])

  async function xoa(tt) {
    if (!window.confirm(`Xóa tóm tắt "${tt.tieu_de}"?`)) return
    setError('')
    try {
      await api.xoaLyThuyet(tt.id)
      setThongBao('Đã xóa tóm tắt.')
      setTimeout(() => setThongBao(''), 3000)
      tai()
    } catch (e) { setError(e.message) }
  }

  async function toggleHien(tt) {
    setError('')
    try {
      await api.capNhatLyThuyet(tt.id, { hien: !tt.hien })
      tai()
    } catch (e) { setError(e.message) }
  }

  const tongTrang = ds ? Math.max(1, Math.ceil(ds.length / MOI_TRANG)) : 1
  const trangHienTai = Math.min(trang, tongTrang)
  const dsTrang = ds ? ds.slice((trangHienTai - 1) * MOI_TRANG, trangHienTai * MOI_TRANG) : []

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <h2 className="text-2xl font-bold text-black">Tóm tắt lý thuyết</h2>
        {!formMo && (
          <Button onClick={() => { setDangSua(null); setFormMo(true) }}>
            + Tạo tóm tắt mới
          </Button>
        )}
      </div>

      {error && <p className="text-sm text-danger bg-danger-soft rounded-md px-3 py-2">{error}</p>}
      {thongBao && <p className="text-sm text-success bg-success-soft rounded-md px-3 py-2">✓ {thongBao}</p>}

      {formMo && (
        <FormTomTat
          danhMuc={danhMuc}
          dangSua={dangSua}
          onDong={() => setFormMo(false)}
          onXong={() => {
            setFormMo(false)
            setThongBao(dangSua ? 'Đã cập nhật tóm tắt.' : 'Đã tạo tóm tắt mới.')
            setTimeout(() => setThongBao(''), 3000)
            tai()
          }}
        />
      )}

      {!ds && <p className="text-sm text-muted">Đang tải...</p>}
      {ds && ds.length === 0 && !formMo && (
        <Card>
          <CardBody className="py-10 text-center text-muted">
            Chưa có tóm tắt lý thuyết nào — bấm "Tạo tóm tắt mới" để soạn bản đầu tiên.
          </CardBody>
        </Card>
      )}
      {ds && ds.length > 0 && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {dsTrang.map((tt) => {
              const dangXem = moRong.has(tt.id)
              return (
                <Card key={tt.id}>
                  <CardBody className="pt-4 flex flex-col gap-2">
                    <div className="flex items-center gap-2 flex-wrap">
                      <p className="font-bold text-ink flex-1">{tt.tieu_de}</p>
                      {tt.hien
                        ? <Badge tone="success">Đang hiện</Badge>
                        : <Badge tone="neutral">Đang ẩn</Badge>}
                    </div>
                    <p className="text-xs text-muted">
                      {tt.chuyen_de_ten}{tt.dang_ten && <> › {tt.dang_ten}</>}
                    </p>
                    {tt.tu_khoa?.length > 0 && (
                      <div className="flex flex-wrap gap-1">
                        {tt.tu_khoa.map((k) => <Badge key={k} tone="primary">{k}</Badge>)}
                      </div>
                    )}
                    <div>
                      <Button size="sm" variant="secondary" onClick={() => toggleMoRong(tt.id)}>
                        {dangXem ? 'Thu gọn' : 'Xem nội dung'}
                      </Button>
                    </div>
                    {dangXem && (
                      <div className="pt-2 border-t border-border">
                        <NoiDungLyThuyet noiDung={tt.noi_dung} />
                      </div>
                    )}
                    <div className="flex gap-2 mt-1 flex-wrap">
                      <Button size="sm" variant="secondary"
                        onClick={() => { setDangSua(tt); setFormMo(true) }}>
                        Sửa
                      </Button>
                      <Button size="sm" variant={tt.hien ? 'warning' : 'success'} onClick={() => toggleHien(tt)}>
                        {tt.hien ? 'Ẩn đi' : 'Hiện cho HS'}
                      </Button>
                      <Button size="sm" variant="danger" onClick={() => xoa(tt)}>Xóa</Button>
                    </div>
                  </CardBody>
                </Card>
              )
            })}
          </div>
          {tongTrang > 1 && (
            <div className="flex items-center justify-center gap-2">
              <Button size="sm" variant="secondary" disabled={trangHienTai <= 1}
                onClick={() => setTrang((t) => t - 1)}>‹ Trước</Button>
              <span className="text-sm text-muted">Trang {trangHienTai}/{tongTrang}</span>
              <Button size="sm" variant="secondary" disabled={trangHienTai >= tongTrang}
                onClick={() => setTrang((t) => t + 1)}>Sau ›</Button>
            </div>
          )}
        </>
      )}
    </div>
  )
}
