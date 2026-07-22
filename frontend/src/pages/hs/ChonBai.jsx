import { useEffect, useMemo, useState } from 'react'
import { BookOpen } from 'lucide-react'
import { api } from '../../api'
import { Badge, Button, Card, CardBody, Select } from '../../components/ui'
import Formula from '../../components/Formula'
import XemLaiBai from '../../components/XemLaiBai'

const NHAN_LOAI = { TN4PA: 'Trắc nghiệm ABCD', TNDS: 'Đúng/Sai 4 ý', TLN: 'Trả lời ngắn' }
const NHAN_KHO = { de: 'Dễ', tb: 'Trung bình', kho: 'Khó' }
const TONE_KHO = { de: 'success', tb: 'warning', kho: 'danger' }
const MOI_TRANG = 20

function renderDe(text) {
  return String(text)
    .split(/(\$[^$]+\$)/g)
    .map((p, i) =>
      p.startsWith('$') ? <Formula key={i} latex={p.slice(1, -1)} /> : <span key={i}>{p}</span>
    )
}

export default function ChonBai({ onChon, onLamTiep, locBanDau }) {
  const [danhMuc, setDanhMuc] = useState([]) // [{id, ten, dang_list:[...]}]
  const [bai, setBai] = useState([])
  const [trangThaiBai, setTrangThaiBai] = useState({}) // {problem_id: {session_id, trang_thai}}
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [xemLaiSid, setXemLaiSid] = useState(null) // session_id đang mở xem lại

  // Bộ lọc
  const [fChuyenDeId, setFChuyenDeId] = useState('')
  const [fDangId, setFDangId] = useState('')
  const [fLoai, setFLoai] = useState('')
  const [fKho, setFKho] = useState('')
  const [fTrangThai, setFTrangThai] = useState('')
  const [trang, setTrang] = useState(1)

  useEffect(() => {
    async function load() {
      try {
        // Các call độc lập: lỗi phụ không chặn danh sách bài
        const [dmResult, baiResult, ttResult] = await Promise.allSettled([
          api.getDanhMuc(),
          api.listProblems(),
          api.getPhienCuaToi(),
        ])
        if (dmResult.status === 'fulfilled') setDanhMuc(dmResult.value)
        if (baiResult.status === 'fulfilled') setBai(baiResult.value)
        else setError(baiResult.reason?.message || 'Lỗi tải danh sách bài')
        if (ttResult.status === 'fulfilled') {
          const map = {}
          ttResult.value.forEach((s) => { map[s.problem_id] = s })
          setTrangThaiBai(map)
        }
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  // Áp bộ lọc ban đầu (vd từ "Luyện ngay" trang Tiến độ: chuyên đề + dạng; hoặc từ "Tiếp tục
  // làm" trang chủ: trạng thái "Đang làm dở"). trang_thai áp ngay, không đợi danh mục tải.
  useEffect(() => {
    if (!locBanDau) return
    const t = setTimeout(() => {
      if (locBanDau.trang_thai) setFTrangThai(locBanDau.trang_thai)
      if (danhMuc.length > 0) {
        const cd = danhMuc.find((c) => c.ten === locBanDau.chuyen_de)
        if (cd) setFChuyenDeId(String(cd.id))
        if (locBanDau.dang_id) setFDangId(String(locBanDau.dang_id))
      }
    }, 0)
    return () => clearTimeout(t)
  }, [danhMuc, locBanDau])

  // Dạng của chuyên đề đang chọn
  const dangList = useMemo(() => {
    if (!fChuyenDeId) return []
    const cd = danhMuc.find((c) => String(c.id) === fChuyenDeId)
    return cd ? cd.dang_list : []
  }, [danhMuc, fChuyenDeId])

  // Reset dạng khi đổi chuyên đề
  function chonChuyenDe(val) {
    setFChuyenDeId(val)
    setFDangId('')
  }

  // Tên chuyên đề đang chọn (để lọc theo tên nếu bài không có dang_id)
  const cdTen = useMemo(() => {
    if (!fChuyenDeId) return ''
    const cd = danhMuc.find((c) => String(c.id) === fChuyenDeId)
    return cd ? cd.ten : ''
  }, [danhMuc, fChuyenDeId])

  const loc = bai.filter((b) => {
    if (fChuyenDeId && b.chuyen_de !== cdTen) return false
    if (fDangId && String(b.dang_id) !== fDangId) return false
    if (fLoai && b.loai_cau !== fLoai) return false
    if (fKho && b.do_kho !== fKho) return false
    if (fTrangThai) {
      const tt = trangThaiBai[b.id]?.trang_thai
      if (fTrangThai === 'hoan_thanh' && tt !== 'hoan_thanh') return false
      if (fTrangThai === 'dang_lam' && tt !== 'dang_lam') return false
      if (fTrangThai === 'chua_lam' && (tt === 'hoan_thanh' || tt === 'dang_lam')) return false
    }
    return true
  })

  // Đổi bộ lọc → quay về trang 1, tránh kẹt ở trang rỗng.
  useEffect(() => {
    setTimeout(() => setTrang(1), 0)
  }, [fChuyenDeId, fDangId, fLoai, fKho, fTrangThai])

  const tongTrang = Math.max(1, Math.ceil(loc.length / MOI_TRANG))
  const locTrang = loc.slice((trang - 1) * MOI_TRANG, trang * MOI_TRANG)

  return (
    <div className="flex flex-col gap-5">
      <h2 className="text-xl font-semibold text-ink">Chọn bài luyện</h2>

      {/* Bộ lọc theo cây danh mục */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
        <Select
          label="Chuyên đề"
          value={fChuyenDeId}
          onChange={(e) => chonChuyenDe(e.target.value)}
          options={[
            { value: '', label: 'Tất cả chuyên đề' },
            ...danhMuc.map((c) => ({ value: String(c.id), label: c.ten })),
          ]}
        />
        <Select
          label="Dạng"
          value={fDangId}
          onChange={(e) => setFDangId(e.target.value)}
          disabled={!fChuyenDeId || dangList.length === 0}
          options={[
            { value: '', label: fChuyenDeId ? 'Tất cả dạng' : 'Chọn chuyên đề trước' },
            ...dangList.map((d) => ({ value: String(d.id), label: d.ten })),
          ]}
        />
        <Select
          label="Loại câu"
          value={fLoai}
          onChange={(e) => setFLoai(e.target.value)}
          options={[
            { value: '', label: 'Tất cả loại' },
            { value: 'TN4PA', label: NHAN_LOAI.TN4PA },
            { value: 'TNDS', label: NHAN_LOAI.TNDS },
            { value: 'TLN', label: NHAN_LOAI.TLN },
          ]}
        />
        <Select
          label="Mức độ"
          value={fKho}
          onChange={(e) => setFKho(e.target.value)}
          options={[
            { value: '', label: 'Tất cả mức' },
            { value: 'de', label: 'Dễ' },
            { value: 'tb', label: 'Trung bình' },
            { value: 'kho', label: 'Khó' },
          ]}
        />
        <Select
          label="Trạng thái"
          value={fTrangThai}
          onChange={(e) => setFTrangThai(e.target.value)}
          options={[
            { value: '', label: 'Tất cả trạng thái' },
            { value: 'hoan_thanh', label: 'Hoàn thành' },
            { value: 'dang_lam', label: 'Đang làm dở' },
            { value: 'chua_lam', label: 'Chưa làm' },
          ]}
        />
      </div>

      {loading && <p className="text-muted text-sm">Đang tải danh sách bài...</p>}
      {error && <p className="text-danger text-sm bg-danger-soft rounded-md px-3 py-2">{error}</p>}

      {!loading && loc.length === 0 && (
        <Card>
          <CardBody className="py-10 text-center text-muted">
            Chưa có bài phù hợp bộ lọc.
          </CardBody>
        </Card>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {locTrang.map((b) => {
          const tt = trangThaiBai[b.id]
          const daXong = tt?.trang_thai === 'hoan_thanh'
          const dangDo = tt?.trang_thai === 'dang_lam'
          return (
            <Card key={b.id}>
              <CardBody className="pt-4 flex flex-col gap-2">
                {/* Chuyên đề → Dạng breadcrumb */}
                <p className="text-sm sm:text-base font-bold text-primary">
                  {b.chuyen_de}{b.dang_ten ? <> › <span className="text-ink">{b.dang_ten}</span></> : null}
                </p>
                <div className="flex items-center gap-2 flex-wrap">
                  <Badge tone="primary">{NHAN_LOAI[b.loai_cau] || b.loai_cau}</Badge>
                  <Badge tone={TONE_KHO[b.do_kho] || 'neutral'}>{NHAN_KHO[b.do_kho] || b.do_kho}</Badge>
                  {daXong && <Badge trang_thai="hoan_thanh" />}
                  {dangDo && <Badge trang_thai="dang_lam" />}
                </div>
                <p className="text-sm text-ink line-clamp-3">{renderDe(b.de_bai)}</p>
                {dangDo ? (
                  <Button className="w-full mt-1" variant="warning" onClick={() => onLamTiep(tt.session_id)}>
                    Làm tiếp
                  </Button>
                ) : daXong ? (
                  <div className="flex gap-2 mt-1">
                    <Button className="flex-1" variant="primary" onClick={() => onChon(b.id)}>
                      Làm lại
                    </Button>
                    <Button className="flex-1" variant="secondary"
                      onClick={() => setXemLaiSid(tt.session_id)}>
                      <BookOpen size={15} strokeWidth={2.2} />
                      <span>Xem lại</span>
                    </Button>
                  </div>
                ) : (
                  <Button className="w-full mt-1" variant="primary" onClick={() => onChon(b.id)}>
                    Bắt đầu
                  </Button>
                )}
              </CardBody>
            </Card>
          )
        })}
      </div>

      {!loading && loc.length > 0 && tongTrang > 1 && (
        <div className="flex items-center justify-center gap-3 pt-1">
          <Button size="sm" variant="secondary" disabled={trang <= 1}
            onClick={() => setTrang((t) => t - 1)}>← Trước</Button>
          <span className="text-sm text-muted">Trang {trang}/{tongTrang}</span>
          <Button size="sm" variant="secondary" disabled={trang >= tongTrang}
            onClick={() => setTrang((t) => t + 1)}>Sau →</Button>
        </div>
      )}

      {xemLaiSid && <XemLaiBai sessionId={xemLaiSid} onDong={() => setXemLaiSid(null)} />}
    </div>
  )
}
