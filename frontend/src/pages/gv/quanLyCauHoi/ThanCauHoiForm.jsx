import { useCallback, useEffect, useRef, useState } from 'react'
import { api } from '../../../api'
import { Button, Input, Select } from '../../../components/ui'
import VeDoThiDialog from '../../../components/gv/VeDoThiDialog'
import VeBBTDialog from '../../../components/gv/VeBBTDialog'
import { BangCongThuc } from './BangCongThuc'
import ChuyenDoiLatexSympy from './ChuyenDoiLatexSympy'
import { TexField } from './TexField'
import { NHAN_LOAI } from './constants'
import { templateTheoLoai } from './templateTheoLoai'

// Thân form chung cho cả Sửa và Tạo câu hỏi.
export function ThanCauHoiForm({ bai, setBai, dangOptions, choChonLoai, onLuu, onDong, dangLuu, nutLuuText, nutLuuDisabled = false, xacNhanDapAn = null }) {
  const activeInsert = useRef(null)
  const register = (fn) => { activeInsert.current = fn }
  const chen = (s, b) => activeInsert.current?.(s, b)

  const [dangUpload, setDangUpload] = useState(false)
  const [loiUpload, setLoiUpload] = useState('')
  // Uploader dùng chung cho cả chọn file lẫn dán clipboard. Xóa hinh_spec cũ (nếu có) vì ảnh
  // mới không còn phải là đồ thị đã vẽ — tránh nút "Vẽ lại" áp nhầm cho ảnh không liên quan.
  const taiLenFile = useCallback(async (file) => {
    if (!file) return
    setLoiUpload('')
    setDangUpload(true)
    try {
      const { url } = await api.uploadHinh(file)
      setBai((b) => {
        const meta = { ...b.meta }
        delete meta.hinh_spec
        return { ...b, hinh_anh: url, meta }
      })
    } catch (err) {
      setLoiUpload(err.message)
    } finally {
      setDangUpload(false)
    }
  }, [setBai])
  function chonHinh(e) {
    const file = e.target.files?.[0]
    e.target.value = ''
    taiLenFile(file)
  }
  // Dán ảnh chụp màn hình bằng Ctrl+V (Win+Shift+S): bắt paste cấp document khi form mở.
  // Chỉ xử lý khi clipboard có ảnh → dán chữ vào ô đề bài vẫn hoạt động bình thường.
  useEffect(() => {
    function danAnh(e) {
      const item = [...(e.clipboardData?.items || [])].find((i) => i.type.startsWith('image/'))
      if (!item) return
      e.preventDefault()
      const file = item.getAsFile()
      if (file) taiLenFile(file)
    }
    document.addEventListener('paste', danAnh)
    return () => document.removeEventListener('paste', danAnh)
  }, [taiLenFile])

  // Vẽ đồ thị (GĐ3A) / bảng biến thiên (GĐ3B) từ hàm số — CAS tự phân tích, GV chỉ nhập f(x).
  const [veDoThiMo, setVeDoThiMo] = useState(false)
  const [veBBTMo, setVeBBTMo] = useState(false)
  function xongVeHinh(url, spec) {
    setBai((b) => ({ ...b, hinh_anh: url, meta: { ...b.meta, hinh_spec: spec } }))
    setVeDoThiMo(false)
    setVeBBTMo(false)
  }

  function doiLoai(loai) {
    const t = templateTheoLoai(loai)
    setBai((b) => ({ ...b, loai_cau: loai, meta: t.meta, solution_steps: t.solution_steps }))
  }

  function setMeta(patch) {
    setBai((b) => ({ ...b, meta: { ...b.meta, ...patch } }))
  }
  function setY(idx, patch) {
    setBai((b) => {
      const y = [...(b.meta.y || [])]
      y[idx] = { ...y[idx], ...patch }
      return { ...b, meta: { ...b.meta, y } }
    })
  }
  function setStep(idx, patch) {
    setBai((b) => {
      const steps = [...b.solution_steps]
      steps[idx] = { ...steps[idx], ...patch }
      return { ...b, solution_steps: steps }
    })
  }
  function setGoiY(si, gi, val) {
    setBai((b) => {
      const steps = [...b.solution_steps]
      const gs = [...(steps[si].danh_sach_goi_y || [])]
      gs[gi] = val
      steps[si] = { ...steps[si], danh_sach_goi_y: gs }
      return { ...b, solution_steps: steps }
    })
  }
  function themGoiY(si) {
    setBai((b) => {
      const steps = [...b.solution_steps]
      steps[si] = { ...steps[si], danh_sach_goi_y: [...(steps[si].danh_sach_goi_y || []), ''] }
      return { ...b, solution_steps: steps }
    })
  }
  function xoaGoiY(si, gi) {
    setBai((b) => {
      const steps = [...b.solution_steps]
      steps[si] = {
        ...steps[si],
        danh_sach_goi_y: steps[si].danh_sach_goi_y.filter((_, i) => i !== gi),
      }
      return { ...b, solution_steps: steps }
    })
  }
  function themBuoc() {
    setBai((b) => ({
      ...b,
      solution_steps: [
        ...b.solution_steps,
        { thu_tu: b.solution_steps.length + 1, pham_vi: 'ca_bai', mo_ta: '', bieu_thuc_ket_qua: '', danh_sach_goi_y: [''] },
      ],
    }))
  }
  function xoaBuoc(si) {
    setBai((b) => ({ ...b, solution_steps: b.solution_steps.filter((_, i) => i !== si) }))
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[1fr_18rem] gap-5">
      {/* Cột trái: form */}
            <div className="flex flex-col gap-4">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                {choChonLoai && (
                  <Select
                    label="Loại câu hỏi"
                    value={bai.loai_cau}
                    onChange={(e) => doiLoai(e.target.value)}
                    options={[
                      { value: 'TN4PA', label: NHAN_LOAI.TN4PA },
                      { value: 'TNDS', label: NHAN_LOAI.TNDS },
                      { value: 'TLN', label: NHAN_LOAI.TLN },
                    ]}
                  />
                )}
                <Select
                  label="Chuyên đề › Dạng"
                  value={String(bai.dang_id || '')}
                  onChange={(e) => setBai((b) => ({ ...b, dang_id: e.target.value || null }))}
                  options={dangOptions}
                />
                <Select
                  label="Mức độ"
                  value={bai.do_kho}
                  onChange={(e) => setBai((b) => ({ ...b, do_kho: e.target.value }))}
                  options={[
                    { value: 'de', label: 'Dễ' },
                    { value: 'tb', label: 'Trung bình' },
                    { value: 'kho', label: 'Khó' },
                  ]}
                />
              </div>

              <TexField
                label={`Đề bài (loại: ${NHAN_LOAI[bai.loai_cau] || bai.loai_cau})`}
                value={bai.de_bai}
                onChange={(v) => setBai((b) => ({ ...b, de_bai: v }))}
                multiline
                registerActive={register}
              />

              {/* Hình minh họa (tùy chọn) — hiện ở cột phải màn HS làm bài */}
              <div className="flex flex-col gap-1.5">
                <p className="text-xs text-muted">
                  Hình minh họa (không bắt buộc — PNG/JPG/WebP, tối đa 3MB)
                </p>
                {bai.hinh_anh ? (
                  <div className="flex items-start gap-3">
                    <img
                      src={bai.hinh_anh}
                      alt="Hình minh họa"
                      className="max-h-40 max-w-full rounded-md border border-border"
                    />
                    <div className="flex flex-col gap-1.5">
                      <Button
                        type="button"
                        size="sm"
                        variant="secondary"
                        onClick={() => setBai((b) => {
                          const meta = { ...b.meta }
                          delete meta.hinh_spec
                          return { ...b, hinh_anh: null, meta }
                        })}
                      >
                        Gỡ ảnh
                      </Button>
                      {bai.meta?.hinh_spec?.loai === 'do_thi' && (
                        <Button type="button" size="sm" variant="secondary" onClick={() => setVeDoThiMo(true)}>
                          📈 Vẽ lại
                        </Button>
                      )}
                      {bai.meta?.hinh_spec?.loai === 'bang_bien_thien' && (
                        <Button type="button" size="sm" variant="secondary" onClick={() => setVeBBTMo(true)}>
                          📋 Vẽ lại
                        </Button>
                      )}
                    </div>
                  </div>
                ) : (
                  <div className="flex flex-col gap-2">
                    <div className="flex flex-wrap items-center gap-3">
                      <label className="inline-flex w-fit cursor-pointer items-center gap-2 rounded-md border border-dashed border-border px-3 py-2 text-sm text-primary hover:border-primary">
                        <input
                          type="file"
                          accept="image/png,image/jpeg,image/webp"
                          className="hidden"
                          onChange={chonHinh}
                          disabled={dangUpload}
                        />
                        {dangUpload ? 'Đang tải ảnh...' : '＋ Chọn ảnh minh họa'}
                      </label>
                      <span className="text-xs text-muted">
                        hoặc chụp màn hình rồi <b>Ctrl&nbsp;+&nbsp;V</b> để dán
                      </span>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      <Button type="button" size="sm" variant="secondary" onClick={() => setVeDoThiMo(true)}>
                        📈 Vẽ đồ thị từ hàm số
                      </Button>
                      <Button type="button" size="sm" variant="secondary" onClick={() => setVeBBTMo(true)}>
                        📋 Vẽ bảng biến thiên
                      </Button>
                    </div>
                  </div>
                )}
                {loiUpload && <p className="text-xs text-danger">{loiUpload}</p>}
                {veDoThiMo && (
                  <VeDoThiDialog
                    initialSpec={bai.meta?.hinh_spec?.loai === 'do_thi' ? bai.meta.hinh_spec : null}
                    onDong={() => setVeDoThiMo(false)}
                    onXongHinh={xongVeHinh}
                  />
                )}
                {veBBTMo && (
                  <VeBBTDialog
                    initialSpec={bai.meta?.hinh_spec?.loai === 'bang_bien_thien' ? bai.meta.hinh_spec : null}
                    onDong={() => setVeBBTMo(false)}
                    onXongHinh={xongVeHinh}
                  />
                )}
              </div>

              {/* Đáp án theo loại câu */}
              {bai.loai_cau === 'TN4PA' && bai.meta?.phuong_an && (
                <div className="flex flex-col gap-2">
                  <p className="text-xs text-muted">Phương án & đáp án đúng</p>
                  {['A', 'B', 'C', 'D'].map((k) => (
                    <div key={k} className="flex items-center gap-2">
                      <label className="flex items-center gap-1 text-sm font-bold w-8">
                        <input
                          type="radio"
                          name="dapan"
                          checked={bai.meta.dap_an_dung === k}
                          onChange={() => setMeta({ dap_an_dung: k })}
                        />
                        {k}
                      </label>
                      <div className="flex-1">
                        <TexField
                          value={bai.meta.phuong_an[k]}
                          onChange={(v) => setMeta({ phuong_an: { ...bai.meta.phuong_an, [k]: v } })}
                          registerActive={register}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {bai.loai_cau === 'TN4PA' && (
                <div className="rounded-md border border-border bg-surface-2 px-3 py-2.5">
                  <Select
                    label="Trước khi chọn đáp án, học sinh:"
                    value={bai.meta?.bat_buoc_suy_luan ? 'co' : 'khong'}
                    onChange={(e) => setMeta({ bat_buoc_suy_luan: e.target.value === 'co' })}
                    options={[
                      { value: 'khong', label: 'Được chọn đáp án ngay' },
                      { value: 'co', label: 'Phải làm đúng tối thiểu 1 bước suy luận' },
                    ]}
                  />
                  <p className="text-[11px] text-muted mt-1">
                    Nếu bắt buộc suy luận: học sinh phải nhập đúng kết quả của bước (máy chấm bằng
                    CAS) thì nút A/B/C/D mới mở. Cần điền "Biểu thức kết quả" ở bước bên dưới.
                  </p>
                </div>
              )}

              {bai.loai_cau === 'TNDS' && bai.meta?.y && (
                <div className="flex flex-col gap-2">
                  <p className="text-xs text-muted">4 mệnh đề (chọn Đúng/Sai + cấu hình suy luận từng ý)</p>
                  {bai.meta.y.map((item, idx) => (
                    <div key={item.ky_hieu} className="rounded-md border border-border p-2.5 flex flex-col gap-2">
                      <div className="flex items-start gap-2">
                        <span className="text-sm font-bold w-5 pt-2">{item.ky_hieu})</span>
                        <div className="flex-1">
                          <TexField
                            value={item.noi_dung_y}
                            onChange={(v) => setY(idx, { noi_dung_y: v })}
                            registerActive={register}
                          />
                        </div>
                        <Select
                          className="w-24"
                          value={item.dap_an}
                          onChange={(e) => setY(idx, { dap_an: e.target.value })}
                          options={[
                            { value: 'Dung', label: 'Đúng' },
                            { value: 'Sai', label: 'Sai' },
                          ]}
                        />
                      </div>
                      <label className="flex items-center gap-2 text-xs text-ink pl-5">
                        <input
                          type="checkbox"
                          checked={!!item.bat_buoc_suy_luan}
                          onChange={(e) => setY(idx, { bat_buoc_suy_luan: e.target.checked })}
                        />
                        Bắt buộc suy luận (nhập biểu thức, CAS chấm) trước khi chốt Đúng/Sai —
                        cần điền "Biểu thức kết quả" ở bước ý {item.ky_hieu} bên dưới.
                      </label>
                    </div>
                  ))}
                </div>
              )}

              {bai.loai_cau === 'TLN' && (
                <div>
                  <Input
                    label="Đáp án cuối (để máy đối chiếu)"
                    value={bai.meta?.dap_an_cuoi ?? ''}
                    onChange={(e) => setMeta({ dap_an_cuoi: e.target.value })}
                  />
                  <p className="text-[11px] text-muted mt-1">
                    Số nguyên hoặc thập phân, tối đa 4 ký tự (ví dụ: <code>3</code>, <code>-2</code>, <code>1,5</code>)
                  </p>
                </div>
              )}

              {/* Các bước lời giải */}
              <div className="flex flex-col gap-3">
                <div className="flex items-center justify-between">
                  <p className="text-xs text-muted">Các bước & gợi ý</p>
                  <Button size="sm" variant="secondary" onClick={themBuoc}>+ Thêm bước</Button>
                </div>
                {bai.solution_steps.map((s, si) => (
                  <div key={si} className="rounded-md border border-border p-3 flex flex-col gap-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-primary">
                        Bước {s.thu_tu}{s.pham_vi && s.pham_vi !== 'ca_bai' ? ` · ý ${s.pham_vi}` : ''}
                      </span>
                      <button onClick={() => xoaBuoc(si)} className="text-danger text-xs hover:underline">
                        Xóa bước
                      </button>
                    </div>
                    <TexField
                      label="Mô tả bước"
                      value={s.mo_ta}
                      onChange={(v) => setStep(si, { mo_ta: v })}
                      registerActive={register}
                    />
                    <div>
                      <p className="text-xs text-muted mb-1">Biểu thức kết quả (cú pháp SymPy — KHÔNG bọc $)</p>
                      <input
                        value={s.bieu_thuc_ket_qua || ''}
                        onChange={(e) => setStep(si, { bieu_thuc_ket_qua: e.target.value })}
                        placeholder="vd: 3*x**2 - 6*x"
                        className="w-full rounded-md border border-border bg-surface px-2.5 py-1.5 text-sm font-mono focus:border-primary focus:outline-none"
                      />
                    </div>
                    <div className="flex flex-col gap-1.5">
                      <div className="flex items-center justify-between">
                        <p className="text-xs text-muted">Gợi ý (leo thang)</p>
                        <button onClick={() => themGoiY(si)} className="text-primary text-xs hover:underline">
                          + Gợi ý
                        </button>
                      </div>
                      {(s.danh_sach_goi_y || []).map((g, gi) => (
                        <div key={gi} className="flex items-start gap-2">
                          <span className="text-xs text-muted pt-2 w-4">{gi + 1}.</span>
                          <div className="flex-1">
                            <TexField
                              value={g}
                              onChange={(v) => setGoiY(si, gi, v)}
                              multiline
                              registerActive={register}
                            />
                          </div>
                          <button
                            onClick={() => xoaGoiY(si, gi)}
                            className="text-danger text-xs hover:underline pt-2"
                          >
                            ✕
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>

              {/* Lời giải chi tiết — khác các bước/gợi ý Socratic ở trên (dùng LÚC ĐANG học);
                  đây là bài giải đầy đủ CHỈ hiện cho HS sau khi hoàn thành, nếu GV bật. */}
              <div className="flex flex-col gap-2 rounded-md border border-border bg-surface-2 p-3">
                <TexField
                  label="Lời giải chi tiết (tùy chọn — HS chỉ thấy sau khi hoàn thành bài)"
                  value={bai.loi_giai_chi_tiet || ''}
                  onChange={(v) => setBai((b) => ({ ...b, loi_giai_chi_tiet: v }))}
                  multiline
                  rows={6}
                  registerActive={register}
                  splitPreview
                />
                <label className="flex items-center gap-2 text-xs text-ink">
                  <input
                    type="checkbox"
                    checked={!!bai.hien_loi_giai_chi_tiet}
                    onChange={(e) => setBai((b) => ({ ...b, hien_loi_giai_chi_tiet: e.target.checked }))}
                  />
                  Cho phép học sinh xem lời giải chi tiết khi xem lại bài (sau khi hoàn thành)
                </label>
              </div>

              {xacNhanDapAn}

              <div className="flex gap-2 pt-1">
                <Button onClick={onLuu} disabled={dangLuu || nutLuuDisabled}>
                  {dangLuu ? 'Đang lưu...' : (nutLuuText || 'Lưu thay đổi')}
                </Button>
                <Button variant="secondary" onClick={onDong}>Hủy</Button>
              </div>
            </div>

            {/* Cột phải: bảng công thức + chuyển đổi LaTeX→SymPy (sticky) */}
            <div className="sticky top-0 self-start max-h-screen overflow-y-auto flex flex-col gap-3 pb-4">
              <BangCongThuc onChen={chen} />
              <ChuyenDoiLatexSympy />
            </div>
    </div>
  )
}
