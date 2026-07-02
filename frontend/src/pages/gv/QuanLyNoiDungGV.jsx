import { useEffect, useState } from 'react'
import { api } from '../../api'
import { Card, CardBody, CardHeader, Select } from '../../components/ui'
import QuanLyDanhMuc from './QuanLyDanhMuc'
import QuanLyCauHoi from './QuanLyCauHoi'

const TABS = [
  { key: 'danh_muc', label: 'Danh mục chuyên đề / dạng' },
  { key: 'cau_hoi', label: 'Câu hỏi' },
]

export default function QuanLyNoiDungGV() {
  const [gvs, setGvs] = useState([])
  const [gvId, setGvId] = useState('')
  const [tab, setTab] = useState('danh_muc')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    api.listGiaoVienQuanLy()
      .then((rows) => setGvs(rows || []))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  const gvChon = gvs.find((g) => String(g.id) === String(gvId))

  return (
    <div className="flex flex-col gap-4">
      {error && (
        <p className="text-danger text-sm bg-danger-soft rounded-md px-3 py-2">
          {error}
          <button onClick={() => setError('')} className="ml-2 font-bold">✕</button>
        </p>
      )}

      <Card>
        <CardHeader
          title="Quản lý nội dung theo giáo viên"
          subtitle="Chọn một giáo viên để xem, sửa hoặc xóa chuyên đề / dạng / câu hỏi của họ. Mọi thay đổi sẽ gửi thông báo cho giáo viên."
        />
        <CardBody>
          {loading ? (
            <p className="text-muted text-sm">Đang tải danh sách giáo viên...</p>
          ) : gvs.length === 0 ? (
            <p className="text-muted text-sm">Chưa có giáo viên nào.</p>
          ) : (
            <Select
              label="Giáo viên"
              className="max-w-md"
              value={gvId}
              onChange={(e) => setGvId(e.target.value)}
              options={[
                { value: '', label: '— Chọn giáo viên —' },
                ...gvs.map((g) => ({ value: String(g.id), label: `${g.ho_ten} (${g.dang_nhap})` })),
              ]}
            />
          )}
        </CardBody>
      </Card>

      {gvChon && (
        <>
          <div className="flex gap-1">
            {TABS.map((t) => (
              <button
                key={t.key}
                onClick={() => setTab(t.key)}
                className={`px-4 py-2 rounded-lg text-sm font-semibold border transition-colors ${
                  tab === t.key
                    ? 'bg-primary text-white border-primary'
                    : 'bg-surface text-ink border-border hover:border-primary'
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>

          <p className="text-sm text-muted">
            Đang quản lý nội dung của <b className="text-ink">{gvChon.ho_ten}</b>
          </p>

          {/* key theo gvId+tab để component tải lại đúng phạm vi khi đổi GV */}
          {tab === 'danh_muc' && (
            <QuanLyDanhMuc key={`dm-${gvChon.id}`} gvId={gvChon.id} toanQuyen />
          )}
          {tab === 'cau_hoi' && (
            <QuanLyCauHoi key={`ch-${gvChon.id}`} gvId={gvChon.id} toanQuyen />
          )}
        </>
      )}
    </div>
  )
}
