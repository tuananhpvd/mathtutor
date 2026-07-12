import { useEffect, useState } from 'react'
import { api } from '../../api'
import { Badge, Button, Card, CardBody, Select, Table, useConfirm } from '../../components/ui'
import ImportCauHoiDialog from '../../components/gv/ImportCauHoiDialog'
import { CotThoiGian } from '../../components/ThoiGianPhanCach'
import { NHAN_KHO, NHAN_LOAI, NHAN_NGUON } from './quanLyCauHoi/constants'
import { ThongKeChuyenDe } from './quanLyCauHoi/ThongKeChuyenDe'
import { SuaCauHoi, TaoCauHoi } from './quanLyCauHoi/SuaTaoCauHoi'

const MOI_TRANG_CH = 20

export default function QuanLyCauHoi({ gvId = null, toanQuyen = false }) {
  const confirm = useConfirm()
  const [rows, setRows] = useState([])
  const [danhMuc, setDanhMuc] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [fTrangThai, setFTrangThai] = useState('')
  const [trangCH, setTrangCH] = useState(1)
  const [sua, setSua] = useState(null)
  const [taoMoi, setTaoMoi] = useState(false)
  const [importMo, setImportMo] = useState(false)
  const [importOk, setImportOk] = useState('')
  const [modalXoaVV, setModalXoaVV] = useState(null)   // { r, anhHuong }
  const [dangTaiAH, setDangTaiAH] = useState(false)
  const [dangXoaVV, setDangXoaVV] = useState(false)
  const [daXacNhan, setDaXacNhan] = useState(false)

  async function tai() {
    const [rs, dm] = await Promise.allSettled([api.listProblems(gvId), api.getDanhMuc(gvId)])
    if (rs.status === 'fulfilled') setRows(rs.value)
    if (dm.status === 'fulfilled') setDanhMuc(dm.value)
  }

  useEffect(() => {
    setTimeout(() => {
      setLoading(true)
      tai().catch(() => {}).finally(() => setLoading(false))
    }, 0)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [gvId])

  const loc = rows.filter((r) => {
    if (fTrangThai && r.trang_thai_duyet !== fTrangThai) return false
    return true
  })
  const tongTrangCH = Math.max(1, Math.ceil(loc.length / MOI_TRANG_CH))
  const locTrang = loc.slice((trangCH - 1) * MOI_TRANG_CH, trangCH * MOI_TRANG_CH)

  async function duyet(r) {
    try { await api.duyetCau(r.id, 'duyet'); await tai() }
    catch (e) { setError(e.message) }
  }
  async function xoa(r) {
    const msg = r.bi_an
      ? `Câu hỏi #${r.id} đang bị ẩn. Xóa vĩnh viễn?`
      : `Xóa câu hỏi #${r.id}?\n\nNếu đã có dữ liệu học sinh, câu hỏi sẽ được ẩn (không xóa vĩnh viễn, HS không thấy nữa).`
    if (!await confirm(msg)) return
    try {
      const res = await api.deleteProblem(r.id)
      if (res?.an) setError('Câu hỏi đã có phiên học của HS — đã ẩn khỏi danh sách HS (dữ liệu được giữ lại).')
      await tai()
    } catch (e) { setError(e.message) }
  }
  async function khoiPhuc(r) {
    if (!await confirm(`Khôi phục câu hỏi #${r.id}? Câu hỏi sẽ hiển thị lại cho HS.`)) return
    try { await api.khoiPhucProblem(r.id); await tai() }
    catch (e) { setError(e.message) }
  }
  async function huyDuyet(r) {
    if (!await confirm(`Hủy duyệt câu hỏi #${r.id}?\nCâu hỏi sẽ trở về trạng thái "Chờ duyệt".`)) return
    try { await api.updateProblem(r.id, { trang_thai_duyet: 'cho_duyet' }); await tai() }
    catch (e) { setError(e.message) }
  }

  async function moModalXoaVV(r) {
    setDangTaiAH(true)
    setDaXacNhan(false)
    try {
      const ah = await api.anhHuongProblem(r.id)
      setModalXoaVV({ r, anhHuong: ah })
    } catch (e) { setError(e.message) }
    finally { setDangTaiAH(false) }
  }
  async function thucHienXoaVV() {
    if (!modalXoaVV) return
    setDangXoaVV(true)
    try {
      await api.xoaVinhVienProblem(modalXoaVV.r.id)
      setModalXoaVV(null)
      await tai()
    } catch (e) { setError(e.message) }
    finally { setDangXoaVV(false) }
  }

  return (
    <div className="flex flex-col gap-4">
      {importOk && (
        <p className="text-success text-sm bg-success-soft rounded-md px-3 py-2">
          ✓ {importOk}
          <button onClick={() => setImportOk('')} className="ml-2 font-bold">✕</button>
        </p>
      )}
      {error && (
        <p className="text-danger text-sm bg-danger-soft rounded-md px-3 py-2">
          {error}
          <button onClick={() => setError('')} className="ml-2 font-bold">✕</button>
        </p>
      )}
      {!loading && <ThongKeChuyenDe danhMuc={danhMuc} rows={rows} />}
      <div className="flex items-end justify-between gap-3 flex-wrap">
        <div className="flex flex-wrap items-end gap-3">
          <Select
            label="Lọc trạng thái duyệt"
            className="w-48"
            value={fTrangThai}
            onChange={(e) => { setFTrangThai(e.target.value); setTrangCH(1) }}
            options={[
              { value: '', label: 'Tất cả' },
              { value: 'da_duyet', label: 'Đã duyệt' },
              { value: 'cho_duyet', label: 'Chờ duyệt' },
              { value: 'loai', label: 'Đã loại' },
            ]}
          />
        </div>
        {!toanQuyen && (
          <div className="flex gap-2">
            <Button variant="secondary" onClick={() => setImportMo(true)}>Import từ Excel</Button>
            <Button onClick={() => setTaoMoi(true)}>+ Tạo câu hỏi mới</Button>
          </div>
        )}
      </div>

      <Card>
        <CardBody className="pt-5">
          {loading ? (
            <p className="text-muted text-sm">Đang tải...</p>
          ) : (
            <Table
              columns={[
                { key: 'id', header: '#', className: 'w-12' },
                {
                  key: 'chuyen_de',
                  header: 'Chuyên đề / Dạng',
                  render: (r) => (
                    <span>
                      {r.chuyen_de}
                      {r.dang_ten && <span className="text-muted"> › {r.dang_ten}</span>}
                      {r.hinh_anh && <span title="Có hình minh họa" className="ml-1">🖼️</span>}
                    </span>
                  ),
                },
                { key: 'loai_cau', header: 'Loại', render: (r) => NHAN_LOAI[r.loai_cau] || r.loai_cau },
                { key: 'do_kho', header: 'Mức độ', render: (r) => NHAN_KHO[r.do_kho] || r.do_kho },
                {
                  key: 'nguon',
                  header: 'Nguồn',
                  render: (r) => (
                    <Badge tone={r.nguon === 'ai_sinh' ? 'warning' : 'primary'}>
                      {NHAN_NGUON[r.nguon] || 'GV'}
                    </Badge>
                  ),
                },
                {
                  key: 'tao_luc',
                  header: 'Ngày giờ tạo',
                  render: (r) => <CotThoiGian iso={r.tao_luc} />,
                },
                {
                  key: 'trang_thai_duyet',
                  header: 'Trạng thái',
                  render: (r) => (
                    <div className="flex flex-wrap gap-1">
                      <Badge trang_thai={r.trang_thai_duyet} />
                      {r.bi_an && <Badge tone="neutral">Đã ẩn</Badge>}
                    </div>
                  ),
                },
                {
                  key: 'actions',
                  header: '',
                  render: (r) => {
                    const coQuyen = r.la_cua_toi || toanQuyen
                    return (
                    <div className="flex justify-end gap-1 flex-wrap">
                      <Button size="sm" variant="secondary" onClick={() => setSua(r.id)}>
                        {coQuyen ? 'Xem / Sửa' : 'Xem'}
                      </Button>
                      {coQuyen && !r.bi_an && r.trang_thai_duyet !== 'da_duyet' && (
                        <Button size="sm" variant="success" onClick={() => duyet(r)}>Duyệt</Button>
                      )}
                      {coQuyen && !r.bi_an && r.trang_thai_duyet === 'da_duyet' && (
                        <Button size="sm" variant="warning" onClick={() => huyDuyet(r)}>Hủy duyệt</Button>
                      )}
                      {coQuyen && (
                        r.bi_an ? (
                          <>
                            <Button size="sm" variant="primary" onClick={() => khoiPhuc(r)}>Khôi phục</Button>
                            <Button size="sm" variant="danger" onClick={() => moModalXoaVV(r)} disabled={dangTaiAH}>Xóa vĩnh viễn</Button>
                          </>
                        ) : (
                          <Button size="sm" variant="danger" onClick={() => xoa(r)}>Xóa</Button>
                        )
                      )}
                    </div>
                    )
                  },
                },
              ]}
              rows={locTrang}
              rowKey={(r) => r.id}
              empty="Chưa có câu hỏi nào."
            />
          )}
          {!loading && tongTrangCH > 1 && (
            <div className="flex items-center justify-between gap-2 pt-3 border-t border-border mt-2">
              <span className="text-xs text-muted">
                {loc.length} câu hỏi · Trang {trangCH}/{tongTrangCH}
              </span>
              <div className="flex items-center gap-1">
                <Button size="sm" variant="secondary" disabled={trangCH === 1}
                  onClick={() => setTrangCH(1)}>«</Button>
                <Button size="sm" variant="secondary" disabled={trangCH === 1}
                  onClick={() => setTrangCH(t => t - 1)}>‹</Button>
                <Button size="sm" variant="secondary" disabled={trangCH === tongTrangCH}
                  onClick={() => setTrangCH(t => t + 1)}>›</Button>
                <Button size="sm" variant="secondary" disabled={trangCH === tongTrangCH}
                  onClick={() => setTrangCH(tongTrangCH)}>»</Button>
              </div>
            </div>
          )}
        </CardBody>
      </Card>

      {sua && (
        <SuaCauHoi
          id={sua}
          danhMuc={danhMuc}
          onDong={() => setSua(null)}
          onLuuXong={() => { setSua(null); tai() }}
        />
      )}

      {taoMoi && (
        <TaoCauHoi
          danhMuc={danhMuc}
          onDong={() => setTaoMoi(false)}
          onLuuXong={() => { setTaoMoi(false); tai() }}
        />
      )}

      {importMo && (
        <ImportCauHoiDialog
          onClose={() => setImportMo(false)}
          onSaved={(msg) => { setImportMo(false); setImportOk(msg); tai() }}
        />
      )}

      {modalXoaVV && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-surface rounded-xl shadow-xl w-full max-w-md max-h-[88vh]
            overflow-y-auto p-6 flex flex-col gap-4">
            <h2 className="text-lg font-bold text-danger">⚠️ Xóa vĩnh viễn câu hỏi #{modalXoaVV.r.id}</h2>
            <p className="text-sm text-muted">
              Hành động này <strong>không thể hoàn tác</strong>. Toàn bộ dữ liệu liên quan sẽ bị xóa:
            </p>
            <div className="bg-danger-soft rounded-lg px-4 py-3 text-sm flex flex-col gap-1">
              <span>🗂 <strong>{modalXoaVV.anhHuong.so_phien}</strong> phiên học</span>
              <span>👤 <strong>{modalXoaVV.anhHuong.so_hoc_sinh}</strong> học sinh bị ảnh hưởng</span>
              <span>💬 <strong>{modalXoaVV.anhHuong.so_luot}</strong> lượt hội thoại</span>
              <span>🚩 <strong>{modalXoaVV.anhHuong.so_co}</strong> cờ theo dõi</span>
            </div>
            <label className="flex items-start gap-2 text-sm cursor-pointer">
              <input
                type="checkbox"
                className="mt-0.5"
                checked={daXacNhan}
                onChange={(e) => setDaXacNhan(e.target.checked)}
              />
              <span>Tôi hiểu rằng dữ liệu sẽ bị xóa vĩnh viễn và không thể khôi phục</span>
            </label>
            <div className="flex justify-end gap-2">
              <Button variant="secondary" onClick={() => { setModalXoaVV(null); setDaXacNhan(false) }}>
                Hủy
              </Button>
              <Button
                variant="danger"
                onClick={thucHienXoaVV}
                disabled={!daXacNhan || dangXoaVV}
              >
                {dangXoaVV ? 'Đang xóa...' : 'Xóa vĩnh viễn'}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
