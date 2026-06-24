import { useEffect, useMemo, useState } from 'react'
import { api } from '../../api'
import { Badge, Button, Card, CardBody, CardHeader, Input, Select } from '../../components/ui'
import Formula from '../../components/Formula'

function renderTex(text) {
  return String(text)
    .split(/(\$[^$]+\$)/g)
    .map((p, i) =>
      p.startsWith('$') ? <Formula key={i} latex={p.slice(1, -1)} /> : <span key={i}>{p}</span>
    )
}

export default function AISinhCauHoi() {
  const [danhMuc, setDanhMuc] = useState([])
  const [form, setForm] = useState({
    chuyen_de: '',
    dang_id: null,
    loai_cau: 'TLN',
    do_kho: 'tb',
    so_luong: 2,
  })
  const [dangSinh, setDangSinh] = useState(false)
  const [error, setError] = useState('')
  const [nhap, setNhap] = useState([])
  const [choDuyet, setChoDuyet] = useState([])

  const dangList = useMemo(() => {
    const cd = danhMuc.find((c) => c.ten === form.chuyen_de)
    return cd ? cd.dang_list : []
  }, [danhMuc, form.chuyen_de])

  function taiChoDuyet() {
    api.listChoDuyet().then(setChoDuyet).catch(() => {})
  }
  useEffect(() => {
    api.getDanhMuc().then((dm) => {
      setDanhMuc(dm)
      if (dm.length > 0) setForm((f) => ({ ...f, chuyen_de: dm[0].ten }))
    }).catch(() => {})
    taiChoDuyet()
  }, [])

  async function sinh() {
    setDangSinh(true)
    setError('')
    try {
      const res = await api.genQuestions(form)
      setNhap(res)
      taiChoDuyet()
    } catch (e) {
      setError(e.message)
    } finally {
      setDangSinh(false)
    }
  }

  async function duyet(id, hanh_dong) {
    await api.duyetCau(id, hanh_dong)
    setNhap((ns) => ns.filter((n) => n.id !== id))
    taiChoDuyet()
  }

  return (
    <div className="flex flex-col gap-5">
      <Card>
        <CardHeader title="Sinh câu hỏi bằng AI" subtitle="Câu sinh ra ở trạng thái Chờ duyệt; chỉ Đã duyệt mới tới học sinh." />
        <CardBody className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3 items-end">
          <Select
            label="Chuyên đề"
            value={form.chuyen_de}
            onChange={(e) => setForm((f) => ({ ...f, chuyen_de: e.target.value, dang_id: null }))}
            options={danhMuc.map((c) => ({ value: c.ten, label: c.ten }))}
          />
          <Select
            label="Dạng (tùy chọn)"
            value={form.dang_id ?? ''}
            onChange={(e) => setForm((f) => ({ ...f, dang_id: e.target.value ? Number(e.target.value) : null }))}
            options={[
              { value: '', label: '— không chọn dạng —' },
              ...dangList.map((d) => ({ value: String(d.id), label: d.ten })),
            ]}
          />
          <Select
            label="Loại câu"
            value={form.loai_cau}
            onChange={(e) => setForm((f) => ({ ...f, loai_cau: e.target.value }))}
            options={[
              { value: 'TLN', label: 'Trả lời ngắn' },
              { value: 'TN4PA', label: 'Trắc nghiệm A–D' },
              { value: 'TNDS', label: 'Đúng/Sai 4 ý' },
            ]}
          />
          <Select
            label="Độ khó"
            value={form.do_kho}
            onChange={(e) => setForm((f) => ({ ...f, do_kho: e.target.value }))}
            options={[
              { value: 'de', label: 'Dễ (2 gợi ý)' },
              { value: 'tb', label: 'Trung bình (3 gợi ý)' },
              { value: 'kho', label: 'Khó (4 gợi ý)' },
            ]}
          />
          <Input
            label="Số lượng"
            type="number"
            min={1}
            max={10}
            value={form.so_luong}
            onChange={(e) => setForm((f) => ({ ...f, so_luong: Number(e.target.value) }))}
          />
          <div className="sm:col-span-4">
            <Button onClick={sinh} disabled={dangSinh}>
              {dangSinh ? 'Đang sinh...' : 'Sinh câu hỏi'}
            </Button>
          </div>
          {error && (
            <p className="sm:col-span-4 text-danger text-sm bg-danger-soft rounded-md px-3 py-2">
              {error}
            </p>
          )}
        </CardBody>
      </Card>

      {nhap.length > 0 && (
        <Card>
          <CardHeader title="Bản nháp vừa sinh" subtitle="Duyệt để đưa vào ngân hàng, hoặc loại." />
          <CardBody className="flex flex-col gap-3">
            {nhap.map((c) => (
              <div key={c.id} className="rounded-md border border-border px-3 py-3 flex flex-col gap-2">
                <div className="flex items-center gap-2">
                  <Badge tone="primary">{c.loai_cau}</Badge>
                  <Badge tone="neutral">{c.do_kho}</Badge>
                  {c.canh_bao.length === 0 ? (
                    <Badge tone="success">Hợp lệ</Badge>
                  ) : (
                    <Badge tone="warning">{c.canh_bao.length} cảnh báo</Badge>
                  )}
                </div>
                <p className="text-sm text-ink">{renderTex(c.de_bai)}</p>
                {c.canh_bao.length > 0 && (
                  <ul className="text-xs text-warning list-disc pl-5">
                    {c.canh_bao.map((w, i) => (
                      <li key={i}>{w}</li>
                    ))}
                  </ul>
                )}
                <div className="flex gap-2">
                  <Button size="sm" variant="success" onClick={() => duyet(c.id, 'duyet')}>
                    Duyệt
                  </Button>
                  <Button size="sm" variant="secondary" onClick={() => duyet(c.id, 'loai')}>
                    Loại
                  </Button>
                </div>
              </div>
            ))}
          </CardBody>
        </Card>
      )}

      <Card>
        <CardHeader title="Hàng đợi chờ duyệt" subtitle={`${choDuyet.length} câu đang chờ`} />
        <CardBody className="flex flex-col gap-2">
          {choDuyet.length === 0 ? (
            <p className="text-sm text-muted">Không còn câu nào chờ duyệt.</p>
          ) : (
            choDuyet.map((c) => (
              <div key={c.id} className="flex items-center justify-between rounded-md border border-border px-3 py-2">
                <span className="text-sm text-ink truncate mr-2">
                  <Badge tone="primary">{c.loai_cau}</Badge> {c.chuyen_de}
                </span>
                <div className="flex gap-2 shrink-0">
                  <Button size="sm" variant="success" onClick={() => duyet(c.id, 'duyet')}>
                    Duyệt
                  </Button>
                  <Button size="sm" variant="secondary" onClick={() => duyet(c.id, 'loai')}>
                    Loại
                  </Button>
                </div>
              </div>
            ))
          )}
        </CardBody>
      </Card>
    </div>
  )
}
