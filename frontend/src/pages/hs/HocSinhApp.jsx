import { lazy, Suspense, useEffect, useState } from 'react'
import RoleLayout from '../../components/RoleLayout'
import { getSession, clearSession, updateHoTen } from '../../auth'
import { useConfirm } from '../../components/ui'

// Mỗi trang tách riêng 1 chunk (code-splitting) — chỉ tải khi HS thật sự mở trang đó.
const TrangChu = lazy(() => import('./TrangChu'))
const ChonBai = lazy(() => import('./ChonBai'))
const PhongHoc = lazy(() => import('./PhongHoc'))
const TienDo = lazy(() => import('./TienDo'))
const NhiemVu = lazy(() => import('./NhiemVu'))
const MucTieu = lazy(() => import('./MucTieu'))
const LyThuyet = lazy(() => import('./LyThuyet'))
const ThiThu = lazy(() => import('./ThiThu'))
const TaiKhoanCaNhan = lazy(() => import('./TaiKhoanCaNhan'))

const NAV = [
  { key: 'trang_chu', label: 'Trang chủ' },
  { key: 'nhiem_vu', label: 'Nhiệm vụ' },
  { key: 'muc_tieu', label: 'Mục tiêu' },
  { key: 'ly_thuyet', label: 'Lý thuyết' },
  { key: 'chon_bai', label: 'Chọn bài' },
  { key: 'thi_thu', label: 'Thi thử' },
  { key: 'tien_do', label: 'Tiến độ' },
  { key: 'tai_khoan', label: 'Tài khoản' },
]

const NAV_KEYS = NAV.map((n) => n.key)
const DEFAULT_PAGE = 'trang_chu'
const PHONG_HOC_KEY = 'hs_phong_hoc'

function pageFromHash() {
  const h = window.location.hash.slice(1)
  if (h === 'phong_hoc') return 'phong_hoc'
  return NAV_KEYS.includes(h) ? h : DEFAULT_PAGE
}

export default function HocSinhApp({ onLogout }) {
  const confirm = useConfirm()
  const [hoTen, setHoTen] = useState(() => (getSession() || {}).ho_ten || '')
  const [page, setPage] = useState(pageFromHash)
  // Session ĐANG active trong phòng học (nếu page === 'phong_hoc') — PhongHoc tự báo lên qua
  // onSid, kể cả khi mở bài mới chưa có sessionId ban đầu. Dùng để chuông thông báo biết HS
  // có đang ở sẵn đúng bài trong thông báo hay không.
  const [activeSid, setActiveSid] = useState(null)
  // { id, ts } | null — nhảy tới + làm nổi bật đúng nhiệm vụ/đề thi khi HS bấm thông báo
  // tương ứng ở chuông. "ts" đổi mỗi lần bấm để ép hiệu ứng chạy lại kể cả bấm trùng.
  const [focusNv, setFocusNv] = useState(null)
  const [focusDeThi, setFocusDeThi] = useState(null)

  function capNhatHoTen(ten) {
    updateHoTen(ten)
    setHoTen(ten)
  }
  const [phongHoc, setPhongHoc] = useState(() => {
    // Khôi phục state phòng học khi F5 với hash #phong_hoc
    if (window.location.hash.slice(1) === 'phong_hoc') {
      try { return JSON.parse(sessionStorage.getItem(PHONG_HOC_KEY)) } catch { return null }
    }
    return null
  })
  const [locBai, setLocBai] = useState(null) // bộ lọc ban đầu cho ChonBai

  function moBaiMoi(problemId) {
    const state = { problemId }
    sessionStorage.setItem(PHONG_HOC_KEY, JSON.stringify(state))
    setPhongHoc(state)
    window.location.hash = 'phong_hoc'
    setPage('phong_hoc')
  }
  function lamTiep(sessionId) {
    const state = { sessionId }
    sessionStorage.setItem(PHONG_HOC_KEY, JSON.stringify(state))
    setPhongHoc(state)
    window.location.hash = 'phong_hoc'
    setPage('phong_hoc')
  }
  function luyenDang(r) {
    setLocBai({ chuyen_de: r.chuyen_de, dang_id: r.dang_id })
    window.location.hash = 'chon_bai'
    setPage('chon_bai')
  }

  // Bấm vào 1 thông báo gắn với phòng học (vd "Thầy/cô trả lời") ở chuông thông báo.
  async function moPhongHocTuThongBao(sessionId) {
    if (!sessionId) return
    if (page === 'phong_hoc' && activeSid === sessionId) {
      // Đang ở sẵn đúng bài này — tải lại trang để cập nhật câu trả lời mới của GV.
      window.location.reload()
      return
    }
    if (page === 'phong_hoc') {
      // Đang làm dở bài khác — hỏi trước khi rời, tránh mất dở dang không báo trước.
      const dongY = await confirm(
        'Bạn đang làm dở một bài khác. Bạn có muốn rời khỏi bài này để chuyển đến bài trong thông báo không?'
      )
      if (!dongY) return
    }
    lamTiep(sessionId)
  }

  // ChuongThongBao gọi hàm này cho MỌI loại thông báo có liên kết — mỗi loại nhảy tới đúng
  // trang tương ứng ở app HS: "session" → phòng học, "nhiem_vu" → trang Nhiệm vụ,
  // "de_thi" → trang Thi thử (danh sách đề), làm nổi bật đúng mục.
  function moTuThongBao(tb) {
    if (tb.lien_ket_loai === 'session') {
      moPhongHocTuThongBao(tb.lien_ket_id)
    } else if (tb.lien_ket_loai === 'nhiem_vu') {
      setFocusNv({ id: tb.lien_ket_id, ts: Date.now() })
      dieuHuong('nhiem_vu')
    } else if (tb.lien_ket_loai === 'de_thi') {
      setFocusDeThi({ id: tb.lien_ket_id, ts: Date.now() })
      dieuHuong('thi_thu')
    }
  }

  function dieuHuong(key) {
    setLocBai(null)
    if (key !== 'phong_hoc') sessionStorage.removeItem(PHONG_HOC_KEY)
    window.location.hash = key
    setPage(key)
  }

  useEffect(() => {
    function onHashChange() {
      const newPage = pageFromHash()
      setLocBai(null)
      if (newPage !== 'phong_hoc') {
        sessionStorage.removeItem(PHONG_HOC_KEY)
        setPhongHoc(null)
      }
      setPage(newPage)
    }
    window.addEventListener('hashchange', onHashChange)
    return () => window.removeEventListener('hashchange', onHashChange)
  }, [])

  return (
    <RoleLayout
      vai_tro="hs"
      ho_ten={hoTen}
      nav={NAV}
      active={page === 'phong_hoc' ? 'chon_bai' : page}
      onNavigate={dieuHuong}
      onLogout={() => {
        clearSession()
        onLogout()
      }}
      onMoLienKet={moTuThongBao}
    >
      <Suspense fallback={<p className="text-muted text-sm">Đang tải...</p>}>
        {page === 'trang_chu' && (
          <TrangChu onChonBai={() => dieuHuong('chon_bai')} onLamTiep={lamTiep} />
        )}
        {page === 'chon_bai' && (
          <ChonBai onChon={moBaiMoi} onLamTiep={lamTiep} locBanDau={locBai} />
        )}
        {page === 'phong_hoc' && phongHoc && (
          <PhongHoc
            // key: ép mount lại hoàn toàn khi chuyển thẳng từ phòng học này sang phòng học
            // khác (vd bấm thông báo trả lời trong lúc đang làm dở bài khác) — tránh sót lại
            // state UI phụ (hộp "nhờ thầy/cô" đang mở, ảnh đang zoom...) của bài trước.
            key={phongHoc.sessionId || phongHoc.problemId || 'moi'}
            problemId={phongHoc.problemId}
            sessionId={phongHoc.sessionId}
            onTrangChu={() => dieuHuong('trang_chu')}
            onChonBai={() => dieuHuong('chon_bai')}
            onSid={setActiveSid}
          />
        )}
        {page === 'nhiem_vu' && (
          <NhiemVu onChon={moBaiMoi} focusId={focusNv} onFocusDone={() => setFocusNv(null)} />
        )}
        {page === 'thi_thu' && (
          <ThiThu onLuyenBai={moBaiMoi} focusId={focusDeThi} onFocusDone={() => setFocusDeThi(null)} />
        )}
        {page === 'muc_tieu' && <MucTieu />}
        {page === 'ly_thuyet' && <LyThuyet />}
        {page === 'tien_do' && <TienDo onLuyenDang={luyenDang} />}
        {page === 'tai_khoan' && <TaiKhoanCaNhan onHoTenChange={capNhatHoTen} />}
      </Suspense>
    </RoleLayout>
  )
}
