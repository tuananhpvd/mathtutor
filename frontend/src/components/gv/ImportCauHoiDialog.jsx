import { useRef, useState } from 'react'
import * as XLSX from 'xlsx'
import { api } from '../../api'
import { Button } from '../ui'
import { kiemTraDapAnTLN } from '../../utils/cauHoi'

const TABS = [
  { key: 'TN4PA', label: 'Trắc nghiệm ABCD' },
  { key: 'TNDS', label: 'Đúng/Sai 4 ý' },
  { key: 'TLN', label: 'Trả lời ngắn' },
]

const DO_KHO_MAP = {
  'dễ': 'de', 'de': 'de', 'dê': 'de',
  'trung bình': 'tb', 'tb': 'tb', 'trung binh': 'tb',
  'khó': 'kho', 'kho': 'kho',
}

function chuanHoaDoKho(v) {
  return DO_KHO_MAP[(v || 'tb').toString().trim().toLowerCase()] || 'tb'
}

function findCol(header, ...keywords) {
  return header.findIndex((h) =>
    keywords.some((k) => String(h).trim().toLowerCase().includes(k.toLowerCase()))
  )
}

function s(val) { return String(val ?? '').trim() }

// Trạng thái khớp ảnh cho 1 dòng: '' → không có; có trong map → khớp; còn lại → chưa upload.
function trangThaiHinh(ten, anhMap) {
  if (!ten) return { text: '—', cls: 'text-muted' }
  if (anhMap[ten]) return { text: `✓ ${ten}`, cls: 'text-green-600' }
  return { text: `⚠ ${ten}`, cls: 'text-amber-600' }
}

// -------- Template generators --------

function xuatMauTN4PA() {
  const wb = XLSX.utils.book_new()
  const ws = XLSX.utils.aoa_to_sheet([
    ['Chuyên đề', 'Dạng (tùy chọn)', 'Độ khó', 'Đề bài',
      'Phương án A', 'Phương án B', 'Phương án C', 'Phương án D',
      'Đáp án đúng (A/B/C/D)', 'Bắt buộc suy luận (Có/Không)', 'Hình (tên file, tùy chọn)'],
    ['Khảo sát hàm số', 'Tính đơn điệu', 'tb',
      'Hàm số $y=x^3-3x$ đồng biến trên khoảng nào?',
      '$(1;+\\infty)$', '$(-1;1)$', '$(-\\infty;-1)$', '$(-1;+\\infty)$',
      'A', 'Không', ''],
    ['Tích phân', '', 'de',
      'Tính $\\int_0^1 x\\,dx$.',
      '$\\dfrac{1}{2}$', '$1$', '$2$', '$\\dfrac{1}{4}$',
      'A', 'Không', ''],
  ])
  ws['!cols'] = [
    { wch: 22 }, { wch: 18 }, { wch: 10 }, { wch: 36 },
    { wch: 18 }, { wch: 18 }, { wch: 18 }, { wch: 18 },
    { wch: 20 }, { wch: 24 },
  ]
  XLSX.utils.book_append_sheet(wb, ws, 'TN4PA')
  XLSX.writeFile(wb, 'mau_import_TN4PA.xlsx')
}

function xuatMauTNDS() {
  const wb = XLSX.utils.book_new()
  const ws = XLSX.utils.aoa_to_sheet([
    ['Chuyên đề', 'Dạng (tùy chọn)', 'Độ khó', 'Đề bài',
      'Nội dung ý a', 'Đáp án ý a (Đ/S)',
      'Nội dung ý b', 'Đáp án ý b (Đ/S)',
      'Nội dung ý c', 'Đáp án ý c (Đ/S)',
      'Nội dung ý d', 'Đáp án ý d (Đ/S)', 'Hình (tên file, tùy chọn)'],
    ['Khảo sát hàm số', 'Cực trị', 'kho',
      'Cho hàm số $y=x^3-3x+2$. Xét tính đúng sai của các mệnh đề sau:',
      'Hàm số có cực đại tại $x=-1$', 'Đ',
      'Giá trị cực đại bằng $4$', 'Đ',
      'Hàm số có cực tiểu tại $x=1$', 'Đ',
      'Giá trị cực tiểu bằng $2$', 'S', ''],
  ])
  ws['!cols'] = [
    { wch: 22 }, { wch: 18 }, { wch: 10 }, { wch: 36 },
    { wch: 28 }, { wch: 16 }, { wch: 28 }, { wch: 16 },
    { wch: 28 }, { wch: 16 }, { wch: 28 }, { wch: 16 },
  ]
  XLSX.utils.book_append_sheet(wb, ws, 'TNDS')
  XLSX.writeFile(wb, 'mau_import_TNDS.xlsx')
}

function xuatMauTLN() {
  const wb = XLSX.utils.book_new()
  const ws = XLSX.utils.aoa_to_sheet([
    ['Chuyên đề', 'Dạng (tùy chọn)', 'Độ khó', 'Đề bài', 'Đáp án cuối', 'Hình (tên file, tùy chọn)'],
    ['Tích phân', 'Tính tích phân', 'tb',
      'Tính $\\int_0^2 (x^2+1)\\,dx$. Kết quả là $m$. Tìm $m$.',
      '14/3', ''],
    ['Khảo sát hàm số', '', 'de',
      'Hàm số $y=x^2-2x+3$ đạt giá trị nhỏ nhất bằng bao nhiêu?',
      '2', ''],
  ])
  ws['!cols'] = [
    { wch: 22 }, { wch: 18 }, { wch: 10 }, { wch: 40 }, { wch: 16 },
  ]
  XLSX.utils.book_append_sheet(wb, ws, 'TLN')
  XLSX.writeFile(wb, 'mau_import_TLN.xlsx')
}

// -------- Parsers --------

function parseTN4PA(data) {
  const header = (data[0] || [])
  const iCD = findCol(header, 'chuyên đề', 'chuyen de')
  const iDang = findCol(header, 'dạng', 'dang')
  const iKho = findCol(header, 'độ khó', 'do kho')
  const iDe = findCol(header, 'đề bài', 'de bai')
  const iA = findCol(header, 'phương án a', 'phuong an a')
  const iB = findCol(header, 'phương án b', 'phuong an b')
  const iC = findCol(header, 'phương án c', 'phuong an c')
  const iD = findCol(header, 'phương án d', 'phuong an d')
  const iDA = findCol(header, 'đáp án đúng', 'dap an dung')
  const iBBSL = findCol(header, 'bắt buộc', 'bat buoc')
  const iHinh = findCol(header, 'hình', 'hinh')

  if ([iCD, iDe, iA, iB, iC, iD, iDA].some((i) => i === -1))
    throw new Error('Thiếu cột bắt buộc. Hãy dùng file mẫu TN4PA.')

  return data.slice(1).map((r, idx) => {
    const chuyen_de = s(r[iCD])
    const de_bai = s(r[iDe])
    const pA = s(r[iA]); const pB = s(r[iB])
    const pC = s(r[iC]); const pD = s(r[iD])
    const da = s(r[iDA]).toUpperCase()
    const bbsl = s(r[iBBSL]).toLowerCase()

    const ly_do = !chuyen_de ? 'Thiếu chuyên đề'
      : !de_bai ? 'Thiếu đề bài'
      : !pA || !pB || !pC || !pD ? 'Thiếu phương án'
      : !['A', 'B', 'C', 'D'].includes(da) ? 'Đáp án đúng phải là A/B/C/D'
      : null

    return {
      dong: idx + 2,
      loai_cau: 'TN4PA',
      chuyen_de,
      dang_ten: iDang !== -1 ? s(r[iDang]) : '',
      do_kho: chuanHoaDoKho(iKho !== -1 ? r[iKho] : 'tb'),
      de_bai,
      hinh_ten: iHinh !== -1 ? s(r[iHinh]) : '',
      meta: {
        phuong_an: { A: pA, B: pB, C: pC, D: pD },
        dap_an_dung: da,
        bat_buoc_suy_luan: ['có', 'co', 'true', '1', 'yes'].includes(bbsl),
      },
      ly_do,
    }
  }).filter((r) => r.chuyen_de || r.de_bai)
}

function parseTNDS(data) {
  const header = (data[0] || [])
  const iCD = findCol(header, 'chuyên đề', 'chuyen de')
  const iDang = findCol(header, 'dạng', 'dang')
  const iKho = findCol(header, 'độ khó', 'do kho')
  const iDe = findCol(header, 'đề bài', 'de bai')
  const iNa = findCol(header, 'nội dung ý a', 'noi dung y a', 'ý a', 'y a')
  const iDa = findCol(header, 'đáp án ý a', 'dap an y a')
  const iNb = findCol(header, 'nội dung ý b', 'noi dung y b', 'ý b', 'y b')
  const iDb = findCol(header, 'đáp án ý b', 'dap an y b')
  const iNc = findCol(header, 'nội dung ý c', 'noi dung y c', 'ý c', 'y c')
  const iDc = findCol(header, 'đáp án ý c', 'dap an y c')
  const iNd = findCol(header, 'nội dung ý d', 'noi dung y d', 'ý d', 'y d')
  const iDd = findCol(header, 'đáp án ý d', 'dap an y d')
  const iHinh = findCol(header, 'hình', 'hinh')

  if ([iCD, iDe, iNa, iDa, iNb, iDb, iNc, iDc, iNd, iDd].some((i) => i === -1))
    throw new Error('Thiếu cột bắt buộc. Hãy dùng file mẫu TNDS.')

  const chuanDA = (v) => {
    const t = s(v).toLowerCase()
    if (['đ', 'd', 'đúng', 'dung', 'true', '1'].includes(t)) return 'Dung'
    if (['s', 'sai', 'false', '0'].includes(t)) return 'Sai'
    return null
  }

  return data.slice(1).map((r, idx) => {
    const chuyen_de = s(r[iCD])
    const de_bai = s(r[iDe])
    const dAs = [
      chuanDA(r[iDa]), chuanDA(r[iDb]), chuanDA(r[iDc]), chuanDA(r[iDd])
    ]

    const ly_do = !chuyen_de ? 'Thiếu chuyên đề'
      : !de_bai ? 'Thiếu đề bài'
      : !s(r[iNa]) || !s(r[iNb]) || !s(r[iNc]) || !s(r[iNd]) ? 'Thiếu nội dung ý'
      : dAs.some((d) => d === null) ? 'Đáp án ý phải là Đ hoặc S'
      : null

    return {
      dong: idx + 2,
      loai_cau: 'TNDS',
      chuyen_de,
      dang_ten: iDang !== -1 ? s(r[iDang]) : '',
      do_kho: chuanHoaDoKho(iKho !== -1 ? r[iKho] : 'tb'),
      de_bai,
      hinh_ten: iHinh !== -1 ? s(r[iHinh]) : '',
      meta: {
        y: [
          { ky_hieu: 'a', noi_dung_y: s(r[iNa]), dap_an: dAs[0] ?? 'Dung' },
          { ky_hieu: 'b', noi_dung_y: s(r[iNb]), dap_an: dAs[1] ?? 'Dung' },
          { ky_hieu: 'c', noi_dung_y: s(r[iNc]), dap_an: dAs[2] ?? 'Dung' },
          { ky_hieu: 'd', noi_dung_y: s(r[iNd]), dap_an: dAs[3] ?? 'Dung' },
        ],
      },
      ly_do,
    }
  }).filter((r) => r.chuyen_de || r.de_bai)
}

function parseTLN(data) {
  const header = (data[0] || [])
  const iCD = findCol(header, 'chuyên đề', 'chuyen de')
  const iDang = findCol(header, 'dạng', 'dang')
  const iKho = findCol(header, 'độ khó', 'do kho')
  const iDe = findCol(header, 'đề bài', 'de bai')
  const iDA = findCol(header, 'đáp án cuối', 'dap an cuoi', 'đáp án', 'dap an')
  const iHinh = findCol(header, 'hình', 'hinh')

  if ([iCD, iDe, iDA].some((i) => i === -1))
    throw new Error('Thiếu cột bắt buộc. Hãy dùng file mẫu TLN.')

  return data.slice(1).map((r, idx) => {
    const chuyen_de = s(r[iCD])
    const de_bai = s(r[iDe])
    const dap_an_cuoi = s(r[iDA])

    const ly_do = !chuyen_de ? 'Thiếu chuyên đề'
      : !de_bai ? 'Thiếu đề bài'
      : kiemTraDapAnTLN(dap_an_cuoi)

    return {
      dong: idx + 2,
      loai_cau: 'TLN',
      chuyen_de,
      dang_ten: iDang !== -1 ? s(r[iDang]) : '',
      do_kho: chuanHoaDoKho(iKho !== -1 ? r[iKho] : 'tb'),
      de_bai,
      hinh_ten: iHinh !== -1 ? s(r[iHinh]) : '',
      meta: { dap_an_cuoi },
      ly_do,
    }
  }).filter((r) => r.chuyen_de || r.de_bai)
}

const PARSERS = { TN4PA: parseTN4PA, TNDS: parseTNDS, TLN: parseTLN }
const XUAT_MAU = { TN4PA: xuatMauTN4PA, TNDS: xuatMauTNDS, TLN: xuatMauTLN }

// -------- Preview columns --------

function PreviewTN4PA({ rows, anhMap }) {
  return (
    <table className="w-full text-xs">
      <thead>
        <tr className="bg-surface border-b border-border">
          {['Dòng', 'Chuyên đề', 'Đề bài', 'Đáp án', 'Khó', 'Hình', 'Trạng thái'].map((h) => (
            <th key={h} className="text-left px-2 py-1.5 font-medium text-muted whitespace-nowrap">{h}</th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((r) => (
          <tr key={r.dong} className={`border-t border-border ${r.ly_do ? 'bg-red-50' : ''}`}>
            <td className="px-2 py-1.5 text-muted">{r.dong}</td>
            <td className={`px-2 py-1.5 ${r.ly_do ? 'text-red-700' : 'text-ink'}`}>{r.chuyen_de || '—'}</td>
            <td className={`px-2 py-1.5 max-w-[200px] truncate ${r.ly_do ? 'text-red-700' : 'text-ink'}`}>{r.de_bai || '—'}</td>
            <td className="px-2 py-1.5 text-ink">{r.meta?.dap_an_dung || '—'}</td>
            <td className="px-2 py-1.5 text-ink">{r.do_kho}</td>
            <td className={`px-2 py-1.5 whitespace-nowrap ${trangThaiHinh(r.hinh_ten, anhMap).cls}`}>
              {trangThaiHinh(r.hinh_ten, anhMap).text}
            </td>
            <td className="px-2 py-1.5">
              {r.ly_do
                ? <span className="text-red-600">{r.ly_do}</span>
                : <span className="text-green-600">✓ Hợp lệ</span>}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}

function PreviewTNDS({ rows, anhMap }) {
  return (
    <table className="w-full text-xs">
      <thead>
        <tr className="bg-surface border-b border-border">
          {['Dòng', 'Chuyên đề', 'Đề bài', 'Ý a', 'Ý b', 'Ý c', 'Ý d', 'Khó', 'Hình', 'Trạng thái'].map((h) => (
            <th key={h} className="text-left px-2 py-1.5 font-medium text-muted whitespace-nowrap">{h}</th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((r) => {
          const y = r.meta?.y || []
          return (
            <tr key={r.dong} className={`border-t border-border ${r.ly_do ? 'bg-red-50' : ''}`}>
              <td className="px-2 py-1.5 text-muted">{r.dong}</td>
              <td className={`px-2 py-1.5 ${r.ly_do ? 'text-red-700' : 'text-ink'}`}>{r.chuyen_de || '—'}</td>
              <td className={`px-2 py-1.5 max-w-[140px] truncate ${r.ly_do ? 'text-red-700' : 'text-ink'}`}>{r.de_bai || '—'}</td>
              {['a','b','c','d'].map((k, i) => (
                <td key={k} className="px-2 py-1.5 text-ink whitespace-nowrap">
                  {y[i] ? (y[i].dap_an === 'Dung' ? '✓' : '✗') : '—'}
                </td>
              ))}
              <td className="px-2 py-1.5 text-ink">{r.do_kho}</td>
              <td className={`px-2 py-1.5 whitespace-nowrap ${trangThaiHinh(r.hinh_ten, anhMap).cls}`}>
                {trangThaiHinh(r.hinh_ten, anhMap).text}
              </td>
              <td className="px-2 py-1.5">
                {r.ly_do
                  ? <span className="text-red-600">{r.ly_do}</span>
                  : <span className="text-green-600">✓ Hợp lệ</span>}
              </td>
            </tr>
          )
        })}
      </tbody>
    </table>
  )
}

function PreviewTLN({ rows, anhMap }) {
  return (
    <table className="w-full text-xs">
      <thead>
        <tr className="bg-surface border-b border-border">
          {['Dòng', 'Chuyên đề', 'Đề bài', 'Đáp án cuối', 'Khó', 'Hình', 'Trạng thái'].map((h) => (
            <th key={h} className="text-left px-2 py-1.5 font-medium text-muted whitespace-nowrap">{h}</th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((r) => (
          <tr key={r.dong} className={`border-t border-border ${r.ly_do ? 'bg-red-50' : ''}`}>
            <td className="px-2 py-1.5 text-muted">{r.dong}</td>
            <td className={`px-2 py-1.5 ${r.ly_do ? 'text-red-700' : 'text-ink'}`}>{r.chuyen_de || '—'}</td>
            <td className={`px-2 py-1.5 max-w-[200px] truncate ${r.ly_do ? 'text-red-700' : 'text-ink'}`}>{r.de_bai || '—'}</td>
            <td className="px-2 py-1.5 text-ink font-mono">{r.meta?.dap_an_cuoi || '—'}</td>
            <td className="px-2 py-1.5 text-ink">{r.do_kho}</td>
            <td className={`px-2 py-1.5 whitespace-nowrap ${trangThaiHinh(r.hinh_ten, anhMap).cls}`}>
              {trangThaiHinh(r.hinh_ten, anhMap).text}
            </td>
            <td className="px-2 py-1.5">
              {r.ly_do
                ? <span className="text-red-600">{r.ly_do}</span>
                : <span className="text-green-600">✓ Hợp lệ</span>}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}

const PREVIEW = { TN4PA: PreviewTN4PA, TNDS: PreviewTNDS, TLN: PreviewTLN }

// -------- Main dialog --------

export default function ImportCauHoiDialog({ onClose, onSaved }) {
  const [tab, setTab] = useState('TN4PA')
  const [rows, setRows] = useState(null)
  const [dangXuLy, setDangXuLy] = useState(false)
  const [loi, setLoi] = useState('')
  const [anhMap, setAnhMap] = useState({})   // tên file gốc -> URL đã upload
  const [dangUpAnh, setDangUpAnh] = useState(false)
  const fileRef = useRef(null)
  const anhRef = useRef(null)

  async function onChonAnh(e) {
    const files = [...(e.target.files || [])]
    e.target.value = ''
    if (!files.length) return
    setDangUpAnh(true)
    setLoi('')
    const ketQua = {}
    for (const f of files) {
      try {
        const { url } = await api.uploadHinh(f)
        ketQua[f.name] = url
      } catch (err) {
        setLoi(`Ảnh "${f.name}": ${err.message}`)
      }
    }
    setAnhMap((m) => ({ ...m, ...ketQua }))
    setDangUpAnh(false)
  }

  function doiTab(key) {
    setTab(key)
    setRows(null)
    setLoi('')
    if (fileRef.current) fileRef.current.value = ''
  }

  async function onChonFile(e) {
    const file = e.target.files?.[0]
    if (!file) return
    setLoi('')
    setDangXuLy(true)
    try {
      const buf = await file.arrayBuffer()
      const wb = XLSX.read(buf, { type: 'array' })
      const ws = wb.Sheets[wb.SheetNames[0]]
      const data = XLSX.utils.sheet_to_json(ws, { header: 1, defval: '' })
      const parsed = PARSERS[tab](data)
      if (parsed.length === 0) throw new Error('File không có dữ liệu hợp lệ.')
      setRows(parsed)
    } catch (err) {
      setLoi(err.message)
      setRows(null)
    } finally {
      setDangXuLy(false)
      e.target.value = ''
    }
  }

  async function xacNhan() {
    if (!rows) return
    const valid = rows
      .filter((r) => !r.ly_do)
      // eslint-disable-next-line no-unused-vars -- loại "dong"/"ly_do" khỏi payload gửi API
      .map(({ dong, ly_do, hinh_ten, ...rest }) => ({
        ...rest,
        hinh_anh: hinh_ten ? (anhMap[hinh_ten] || null) : null,
      }))
    if (valid.length === 0) return
    setDangXuLy(true)
    setLoi('')
    try {
      const res = await api.importCauHoiBatch(valid)
      onSaved(`Đã import ${res.da_tao} câu hỏi (trạng thái: chờ duyệt).${res.loi?.length ? ` ${res.loi.length} dòng lỗi bị bỏ qua.` : ''}`)
    } catch (err) {
      setLoi(err.message)
      setDangXuLy(false)
    }
  }

  const soLoi = rows ? rows.filter((r) => r.ly_do).length : 0
  const soHopLe = rows ? rows.filter((r) => !r.ly_do).length : 0
  const PreviewComp = PREVIEW[tab]

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-4xl flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="px-5 pt-5 pb-3 border-b border-border flex-shrink-0">
          <h2 className="font-bold text-lg text-ink">Import câu hỏi từ Excel</h2>
          <p className="text-xs text-muted mt-0.5">
            Câu hỏi import sẽ có trạng thái <strong>Chờ duyệt + Riêng tư</strong> — duyệt xong mới hiện với HS.
          </p>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 px-5 pt-3 flex-shrink-0">
          {TABS.map((t) => (
            <button
              key={t.key}
              onClick={() => doiTab(t.key)}
              className={`px-4 py-1.5 rounded-full text-sm font-semibold border transition-colors ${
                tab === t.key
                  ? 'bg-primary text-white border-primary'
                  : 'bg-surface text-ink border-border hover:border-primary'
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>

        {/* Body */}
        <div className="overflow-y-auto flex-1 px-5 py-4 flex flex-col gap-4">
          {/* Controls */}
          <div className="flex items-center gap-3 flex-wrap">
            <Button variant="secondary" onClick={XUAT_MAU[tab]}>
              Tải file mẫu {tab} (.xlsx)
            </Button>
            <Button
              variant="secondary"
              onClick={() => fileRef.current?.click()}
              disabled={dangXuLy}
            >
              {dangXuLy ? 'Đang xử lý...' : 'Chọn file Excel để import'}
            </Button>
            <input
              ref={fileRef}
              type="file"
              accept=".xlsx,.xls"
              className="hidden"
              onChange={onChonFile}
            />
          </div>

          {/* Hướng dẫn theo tab */}
          <div className="text-xs text-muted leading-relaxed">
            {tab === 'TN4PA' && (
              <>Cột bắt buộc: <strong>Chuyên đề, Đề bài, Phương án A/B/C/D, Đáp án đúng</strong> (A/B/C/D).
              Cột tùy chọn: Dạng, Độ khó (dễ/tb/khó), Bắt buộc suy luận (Có/Không).</>
            )}
            {tab === 'TNDS' && (
              <>Cột bắt buộc: <strong>Chuyên đề, Đề bài, Nội dung ý a/b/c/d, Đáp án ý a/b/c/d</strong> (Đ hoặc S).
              Cột tùy chọn: Dạng, Độ khó.</>
            )}
            {tab === 'TLN' && (
              <>Cột bắt buộc: <strong>Chuyên đề, Đề bài, Đáp án cuối</strong>.
              Cột tùy chọn: Dạng, Độ khó.</>
            )}
            <div className="mt-1">
              Cột <strong>Hình</strong> (tùy chọn): ghi <b>tên file</b> ảnh (đã upload bên dưới) để gắn ảnh minh họa cho câu.
            </div>
          </div>

          {/* Upload ảnh minh họa (tùy chọn) — khớp cột "Hình" theo tên file */}
          <div className="rounded-lg border border-border bg-surface-2 px-3 py-2.5 flex flex-col gap-2">
            <div className="flex items-center gap-3 flex-wrap">
              <Button variant="secondary" onClick={() => anhRef.current?.click()} disabled={dangUpAnh}>
                {dangUpAnh ? 'Đang tải ảnh...' : 'Upload ảnh minh họa (chọn nhiều)'}
              </Button>
              <input
                ref={anhRef}
                type="file"
                accept="image/png,image/jpeg,image/webp"
                multiple
                className="hidden"
                onChange={onChonAnh}
              />
              <span className="text-xs text-muted">
                Upload trước, rồi ghi tên file vào cột "Hình" trong Excel. PNG/JPG/WebP ≤ 3MB.
              </span>
            </div>
            {Object.keys(anhMap).length > 0 && (
              <div className="flex flex-wrap gap-1.5">
                {Object.keys(anhMap).map((ten) => (
                  <span key={ten} className="text-[11px] bg-green-50 text-green-700 rounded px-1.5 py-0.5">
                    ✓ {ten}
                  </span>
                ))}
              </div>
            )}
          </div>

          {loi && (
            <p className="text-sm text-danger bg-danger-soft rounded-md px-3 py-2">{loi}</p>
          )}

          {/* Preview */}
          {rows && (
            <div className="flex flex-col gap-2">
              <p className="text-sm text-muted">
                {rows.length} dòng ·{' '}
                <span className="text-green-600 font-medium">{soHopLe} hợp lệ</span>
                {soLoi > 0 && (
                  <>{' '}· <span className="text-danger font-medium">{soLoi} lỗi (bỏ qua)</span></>
                )}
              </p>
              <div className="rounded-lg border border-border overflow-x-auto">
                <PreviewComp rows={rows} anhMap={anhMap} />
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-5 py-4 border-t border-border flex-shrink-0 flex gap-2 justify-end">
          <Button variant="secondary" onClick={onClose} disabled={dangXuLy}>Hủy bỏ</Button>
          {rows && soHopLe > 0 && (
            <Button onClick={xacNhan} disabled={dangXuLy}>
              {dangXuLy ? 'Đang import...' : `Xác nhận import ${soHopLe} câu hỏi`}
            </Button>
          )}
        </div>
      </div>
    </div>
  )
}
