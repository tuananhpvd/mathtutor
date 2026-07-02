import { useEffect, useState } from 'react'
import { api } from '../../api'
import { Button, Card, CardBody, CardHeader, Input, useConfirm } from '../../components/ui'

function FormInput({ label, value, onChange, placeholder }) {
  return (
    <Input
      label={label}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
    />
  )
}

function TenChuyenDe({ cd, onSua }) {
  const [sua, setSua] = useState(false)
  const [ten, setTen] = useState(cd.ten)
  async function luu() {
    const t = ten.trim()
    if (!t || t === cd.ten) { setSua(false); return }
    await onSua(cd, t)
    setSua(false)
  }
  if (sua) {
    return (
      <div className="flex items-center gap-2">
        <input
          value={ten}
          autoFocus
          onChange={(e) => setTen(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter') luu(); if (e.key === 'Escape') setSua(false) }}
          className="font-semibold rounded border border-primary bg-surface px-2 py-0.5 focus:outline-none"
        />
        <button onClick={luu} className="text-primary text-xs hover:underline">Lưu</button>
        <button onClick={() => { setTen(cd.ten); setSua(false) }} className="text-muted text-xs hover:underline">Hủy</button>
      </div>
    )
  }
  return (
    <p className="font-semibold text-ink flex items-center gap-2">
      {cd.ten}
      <button onClick={() => setSua(true)} className="text-primary text-xs font-normal hover:underline">Sửa</button>
    </p>
  )
}

function DangRow({ dang, onXoa, onSua }) {
  const [sua, setSua] = useState(false)
  const [ten, setTen] = useState(dang.ten)
  async function luu() {
    const t = ten.trim()
    if (!t || t === dang.ten) { setSua(false); return }
    await onSua(dang, t)
    setSua(false)
  }
  return (
    <div className="flex items-center justify-between rounded-md bg-surface-2 px-3 py-1.5 text-sm gap-2">
      {sua ? (
        <input
          value={ten}
          autoFocus
          onChange={(e) => setTen(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter') luu(); if (e.key === 'Escape') setSua(false) }}
          className="flex-1 rounded border border-primary bg-surface px-2 py-0.5 focus:outline-none"
        />
      ) : (
        <span className="text-ink flex-1">{dang.ten}</span>
      )}
      <div className="flex items-center gap-3 shrink-0">
        <span className="text-xs text-muted">{dang.so_cau} câu</span>
        {sua ? (
          <>
            <button onClick={luu} className="text-primary text-xs hover:underline">Lưu</button>
            <button onClick={() => { setTen(dang.ten); setSua(false) }} className="text-muted text-xs hover:underline">Hủy</button>
          </>
        ) : (
          <>
            <button onClick={() => setSua(true)} className="text-primary text-xs hover:underline">Sửa</button>
            <button
              onClick={() => onXoa(dang)}
              className="text-danger text-xs hover:underline disabled:opacity-40"
              disabled={dang.so_cau > 0}
              title={dang.so_cau > 0 ? 'Còn câu hỏi, không thể xóa' : 'Xóa dạng'}
            >
              Xóa
            </button>
          </>
        )}
      </div>
    </div>
  )
}

export default function QuanLyDanhMuc({ gvId = null, toanQuyen = false }) {
  const confirm = useConfirm()
  const [danhMuc, setDanhMuc] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  // Form thêm chuyên đề
  const [tenCD, setTenCD] = useState('')
  const [moTaCD, setMoTaCD] = useState('')
  const [dangThemCD, setDangThemCD] = useState(false)

  // Form thêm dạng (theo chuyên đề đang mở)
  const [moCD, setMoCD] = useState(null) // id chuyên đề đang expand
  const [tenDang, setTenDang] = useState('')
  const [moTaDang, setMoTaDang] = useState('')
  const [dangThemDang, setDangThemDang] = useState(false)

  async function tai() {
    const dm = await api.getDanhMuc(gvId)
    setDanhMuc(dm)
  }

  useEffect(() => {
    setLoading(true)
    tai().catch((e) => setError(e.message)).finally(() => setLoading(false))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [gvId])

  async function themCD() {
    if (!tenCD.trim()) return
    setDangThemCD(true)
    try {
      await api.themChuyenDe({ ten: tenCD.trim(), mo_ta: moTaCD.trim() || null, thu_tu: 0 })
      setTenCD(''); setMoTaCD('')
      await tai()
    } catch (e) { setError(e.message) }
    finally { setDangThemCD(false) }
  }

  async function xoaCD(cd) {
    if (!await confirm(`Xóa chuyên đề "${cd.ten}"?`)) return
    try { await api.xoaChuyenDe(cd.id); await tai() }
    catch (e) { setError(e.message) }
  }

  async function suaCD(cd, ten) {
    try { await api.capNhatChuyenDe(cd.id, { ten }); await tai() }
    catch (e) { setError(e.message) }
  }

  async function suaDang(dang, ten) {
    try { await api.capNhatDang(dang.id, { ten }); await tai() }
    catch (e) { setError(e.message) }
  }

  async function themDang(cdId) {
    if (!tenDang.trim()) return
    setDangThemDang(true)
    try {
      await api.themDang({ chuyen_de_id: cdId, ten: tenDang.trim(), mo_ta: moTaDang.trim() || null, thu_tu: 0 })
      setTenDang(''); setMoTaDang('')
      await tai()
    } catch (e) { setError(e.message) }
    finally { setDangThemDang(false) }
  }

  async function xoaDang(dang) {
    if (!await confirm(`Xóa dạng "${dang.ten}"?`)) return
    try { await api.xoaDang(dang.id); await tai() }
    catch (e) { setError(e.message) }
  }

  if (loading) return <p className="text-muted text-sm">Đang tải...</p>

  return (
    <div className="flex flex-col gap-5">
      {error && (
        <p className="text-danger text-sm bg-danger-soft rounded-md px-3 py-2">
          {error}
          <button onClick={() => setError('')} className="ml-2 font-bold">✕</button>
        </p>
      )}

      {/* Form thêm chuyên đề — ẩn với tài khoản Quản lý (chỉ sửa/xóa của GV) */}
      {!toanQuyen && (
        <Card>
          <CardHeader title="Thêm chuyên đề mới" />
          <CardBody className="grid sm:grid-cols-3 gap-3 items-end">
            <FormInput label="Tên chuyên đề" value={tenCD} onChange={setTenCD} placeholder="VD: Hình học không gian" />
            <FormInput label="Mô tả (tùy chọn)" value={moTaCD} onChange={setMoTaCD} placeholder="" />
            <Button onClick={themCD} disabled={!tenCD.trim() || dangThemCD}>
              {dangThemCD ? 'Đang thêm...' : 'Thêm chuyên đề'}
            </Button>
          </CardBody>
        </Card>
      )}

      {/* Danh sách chuyên đề + dạng */}
      {danhMuc.length === 0 ? (
        <Card><CardBody className="py-8 text-center text-muted">Chưa có chuyên đề nào.</CardBody></Card>
      ) : (
        danhMuc.map((cd) => (
          <Card key={cd.id}>
            <CardBody className="pt-4 flex flex-col gap-3">
              {/* Header chuyên đề */}
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1">
                  <TenChuyenDe cd={cd} onSua={suaCD} />
                  {cd.mo_ta && <p className="text-xs text-muted mt-0.5">{cd.mo_ta}</p>}
                  <p className="text-xs text-muted mt-0.5">{cd.dang_list.length} dạng</p>
                </div>
                <div className="flex gap-2 shrink-0">
                  <Button size="sm" variant="secondary" onClick={() => setMoCD(moCD === cd.id ? null : cd.id)}>
                    {moCD === cd.id ? 'Thu gọn' : 'Quản lý dạng'}
                  </Button>
                  <button
                    onClick={() => xoaCD(cd)}
                    className="text-sm text-danger hover:underline disabled:opacity-40"
                    disabled={cd.dang_list.length > 0}
                    title={cd.dang_list.length > 0 ? 'Còn dạng, không thể xóa' : 'Xóa chuyên đề'}
                  >
                    Xóa
                  </button>
                </div>
              </div>

              {/* Expand: list dạng + form thêm dạng */}
              {moCD === cd.id && (
                <div className="border-t border-border pt-3 flex flex-col gap-2">
                  {cd.dang_list.length === 0 ? (
                    <p className="text-xs text-muted">Chưa có dạng nào.</p>
                  ) : (
                    cd.dang_list.map((d) => (
                      <DangRow key={d.id} dang={d} onXoa={xoaDang} onSua={suaDang} />
                    ))
                  )}
                  {/* Form thêm dạng — ẩn với tài khoản Quản lý */}
                  {!toanQuyen && (
                    <div className="grid sm:grid-cols-3 gap-2 mt-1 items-end">
                      <FormInput label="Tên dạng mới" value={tenDang} onChange={setTenDang} placeholder="VD: Xét đơn điệu" />
                      <FormInput label="Mô tả (tùy chọn)" value={moTaDang} onChange={setMoTaDang} placeholder="" />
                      <Button size="sm" onClick={() => themDang(cd.id)} disabled={!tenDang.trim() || dangThemDang}>
                        {dangThemDang ? 'Đang thêm...' : '+ Thêm dạng'}
                      </Button>
                    </div>
                  )}
                </div>
              )}
            </CardBody>
          </Card>
        ))
      )}
    </div>
  )
}
