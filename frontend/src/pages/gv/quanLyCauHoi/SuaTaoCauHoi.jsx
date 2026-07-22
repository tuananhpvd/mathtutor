import { useEffect, useState } from 'react'
import { api } from '../../../api'
import { useConfirm } from '../../../components/ui'
import { chuanHoaSteps, dungDangOptions, kiemTraDapAnTLN } from '../../../utils/cauHoi'
import { ThanCauHoiForm } from './ThanCauHoiForm'
import { templateTheoLoai } from './templateTheoLoai'

// Vỏ modal chung (overlay phải) cho Sửa / Tạo.
function KhungModal({ tieu_de, error, children, onDong }) {
  return (
    <div className="fixed inset-0 z-20 bg-black/30 flex justify-end">
      <div className="w-full lg:w-2/3 lg:min-w-[620px] bg-surface h-full overflow-y-auto
        p-4 sm:p-6 shadow-[var(--shadow-pop)]">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-ink">{tieu_de}</h3>
          <button onClick={onDong} className="text-muted hover:text-ink text-lg">✕</button>
        </div>
        {error && <p className="text-danger text-sm bg-danger-soft rounded-md px-3 py-2 mb-3">{error}</p>}
        {children}
      </div>
    </div>
  )
}

export function SuaCauHoi({ id, danhMuc, onDong, onLuuXong }) {
  const [bai, setBai] = useState(null)
  const [error, setError] = useState('')
  const [dangLuu, setDangLuu] = useState(false)
  // Lỗ hổng từng bị bỏ sót (sự cố v137): màn "Sinh câu hỏi AI" đã bắt GV tích xác nhận trước
  // khi Duyệt, nhưng GV cũng có thể vào SỬA một câu AI-sinh đang chờ duyệt từ đây (modal này
  // dùng chung cho mọi nguồn, mở từ cả AISinhCauHoi.jsx lẫn QuanLyCauHoi.jsx) rồi bấm "Duyệt
  // luôn" ở hộp thoại xác nhận bên dưới — HOÀN TOÀN bỏ qua checkbox ở màn AI. Chặn lại tại
  // đây: chỉ câu AI SINH đang chờ duyệt mới cần tích; câu GV tự nhập/import thì GV đã tự viết
  // đáp án nên không có rủi ro AI chép khuôn mẫu.
  const [daXacNhanDapAn, setDaXacNhanDapAn] = useState(false)
  const confirm = useConfirm()

  useEffect(() => {
    api.getProblem(id).then(setBai).catch((e) => setError(e.message))
  }, [id])

  const dangOptions = dungDangOptions(danhMuc)
  const laAiSinhChoDuyet = bai?.nguon === 'ai_sinh' && bai?.trang_thai_duyet !== 'da_duyet'

  async function luu() {
    setError('')
    if (bai.loai_cau === 'TLN') {
      const err = kiemTraDapAnTLN(bai.meta?.dap_an_cuoi)
      if (err) { setError(err); return }
    }
    setDangLuu(true)
    try {
      const opt = dangOptions.find((o) => o.value === String(bai.dang_id || ''))
      await api.updateProblem(id, {
        de_bai: bai.de_bai,
        do_kho: bai.do_kho,
        dang_id: bai.dang_id ? Number(bai.dang_id) : null,
        chuyen_de: opt?.cd || bai.chuyen_de,
        hinh_anh: bai.hinh_anh ?? null,
        meta: bai.meta,
        solution_steps: chuanHoaSteps(bai.solution_steps),
        loi_giai_chi_tiet: bai.loi_giai_chi_tiet || '',
        hien_loi_giai_chi_tiet: !!bai.hien_loi_giai_chi_tiet,
      })
      // Câu chưa duyệt → hỏi ngay có duyệt luôn không, đỡ phải quay lại tìm trong danh sách.
      // Riêng câu AI sinh: CHỈ hỏi khi GV đã tích xác nhận đối chiếu đáp án — chưa tích thì
      // lưu xong vẫn giữ nguyên chờ duyệt, GV duyệt sau từ danh sách (đã có checkbox riêng).
      if (bai.trang_thai_duyet !== 'da_duyet' && (!laAiSinhChoDuyet || daXacNhanDapAn)) {
        const muonDuyet = await confirm(
          'Đã lưu câu hỏi. Thầy/cô có muốn DUYỆT LUÔN để học sinh thấy được ngay không?',
          { title: 'Lưu thành công', labelYes: 'Duyệt luôn', labelNo: 'Chỉ lưu, duyệt sau' }
        )
        if (muonDuyet) {
          try { await api.duyetCau(id, 'duyet') } catch (e) { setError(e.message) }
        }
      }
      onLuuXong()
    } catch (e) {
      setError(e.message)
    } finally {
      setDangLuu(false)
    }
  }

  return (
    <KhungModal tieu_de={`Sửa câu hỏi #${id}`} error={error} onDong={onDong}>
      {!bai ? (
        <p className="text-muted text-sm">Đang tải...</p>
      ) : (
        <ThanCauHoiForm
          bai={bai} setBai={setBai} dangOptions={dangOptions}
          onLuu={luu} onDong={onDong} dangLuu={dangLuu} nutLuuText="Lưu thay đổi"
          xacNhanDapAn={laAiSinhChoDuyet ? (
            <label className="flex items-start gap-2 text-sm text-ink bg-warning-soft/60 rounded-md px-3 py-2 cursor-pointer">
              <input type="checkbox" className="mt-0.5 shrink-0" checked={daXacNhanDapAn}
                onChange={(e) => setDaXacNhanDapAn(e.target.checked)} />
              <span>
                Câu này do <b>AI sinh</b>, chưa duyệt. Tôi đã đối chiếu <b>đáp án</b> với{' '}
                <b>lời giải chi tiết</b> bên trên và xác nhận khớp nhau — chưa tích thì lưu xong
                vẫn giữ trạng thái chờ duyệt (không hỏi duyệt luôn).
              </span>
            </label>
          ) : null}
        />
      )}
    </KhungModal>
  )
}

export function TaoCauHoi({ danhMuc, onDong, onLuuXong }) {
  const [bai, setBai] = useState(() => ({
    loai_cau: 'TN4PA', do_kho: 'tb', dang_id: null, de_bai: '',
    loi_giai_chi_tiet: '', hien_loi_giai_chi_tiet: false,
    ...templateTheoLoai('TN4PA'),
  }))
  const [error, setError] = useState('')
  const [dangLuu, setDangLuu] = useState(false)

  const dangOptions = dungDangOptions(danhMuc)

  async function tao() {
    setError('')
    if (!bai.de_bai.trim()) { setError('Vui lòng nhập đề bài.'); return }
    if (!bai.dang_id) { setError('Vui lòng chọn Chuyên đề › Dạng.'); return }
    if (bai.loai_cau === 'TLN') {
      const err = kiemTraDapAnTLN(bai.meta?.dap_an_cuoi)
      if (err) { setError(err); return }
    }
    setDangLuu(true)
    try {
      const opt = dangOptions.find((o) => o.value === String(bai.dang_id || ''))
      await api.createProblem({
        loai_cau: bai.loai_cau,
        do_kho: bai.do_kho,
        dang_id: Number(bai.dang_id),
        chuyen_de: opt?.cd || '',
        de_bai: bai.de_bai,
        hinh_anh: bai.hinh_anh || null,
        meta: bai.meta,
        solution_steps: chuanHoaSteps(bai.solution_steps),
        loi_giai_chi_tiet: bai.loi_giai_chi_tiet || '',
        hien_loi_giai_chi_tiet: !!bai.hien_loi_giai_chi_tiet,
      })
      onLuuXong()
    } catch (e) {
      setError(e.message)
    } finally {
      setDangLuu(false)
    }
  }

  return (
    <KhungModal tieu_de="Tạo câu hỏi mới" error={error} onDong={onDong}>
      <p className="text-[12px] text-muted bg-surface-2 rounded-md px-3 py-2 mb-3">
        Chọn loại câu hỏi để hiện đúng cấu trúc nhập. Câu mới được lưu <b>đã duyệt, sẵn sàng dùng ngay</b> —
        học sinh trong lớp em phụ trách tự chọn luyện được, hoặc giao thẳng qua "Giao nhiệm vụ".
      </p>
      <ThanCauHoiForm
        bai={bai} setBai={setBai} dangOptions={dangOptions} choChonLoai
        onLuu={tao} onDong={onDong} dangLuu={dangLuu} nutLuuText="Tạo câu hỏi"
      />
    </KhungModal>
  )
}
