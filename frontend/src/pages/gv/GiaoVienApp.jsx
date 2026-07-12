import { lazy, Suspense, useEffect, useState } from 'react'
import RoleLayout from '../../components/RoleLayout'
import { getSession, clearSession, updateHoTen } from '../../auth'

// Mỗi trang tách riêng 1 chunk (code-splitting) — chỉ tải khi GV thật sự mở trang đó.
const TongQuan = lazy(() => import('./TongQuan'))
const QuanLyCauHoi = lazy(() => import('./QuanLyCauHoi'))
const QuanLyDanhMuc = lazy(() => import('./QuanLyDanhMuc'))
const AISinhCauHoi = lazy(() => import('./AISinhCauHoi'))
const QuanLyCo = lazy(() => import('./QuanLyCo'))
const TheoDoiTienBo = lazy(() => import('./TheoDoiTienBo'))
const TaiKhoanCaNhan = lazy(() => import('./TaiKhoanCaNhan'))
const QuanLyLopGV = lazy(() => import('./QuanLyLopGV'))
const QuanLyHocSinhGV = lazy(() => import('./QuanLyHocSinhGV'))
const HoTroHocSinh = lazy(() => import('./HoTroHocSinh'))
const GiaoNhiemVu = lazy(() => import('./GiaoNhiemVu'))
const QuanLyDeThi = lazy(() => import('./QuanLyDeThi'))
const QuanLyNoiDungGV = lazy(() => import('./QuanLyNoiDungGV'))

const NAV = [
  { key: 'tong_quan', label: 'Tổng quan' },
  { key: 'danh_muc', label: 'Danh mục' },
  { key: 'cau_hoi', label: 'Câu hỏi' },
  { key: 'ai_sinh', label: 'AI sinh câu hỏi' },
  { key: 'co', label: 'Cờ theo dõi' },
  { key: 'ho_tro', label: 'Hỗ trợ học sinh' },
  { key: 'nhiem_vu', label: 'Giao nhiệm vụ' },
  { key: 'de_thi', label: 'Đề thi thử' },
  { key: 'tien_bo', label: 'Tiến bộ học sinh' },
  { key: 'lop', label: 'Quản lý lớp' },
  { key: 'hoc_sinh', label: 'Quản lý học sinh' },
  { key: 'tai_khoan', label: 'Tài khoản cá nhân' },
]

// Tài khoản Quản lý: chỉ quản lý nội dung của các GV + tài khoản cá nhân.
const NAV_QUAN_LY = [
  { key: 'noi_dung_gv', label: 'Quản lý nội dung GV' },
  { key: 'tai_khoan', label: 'Tài khoản cá nhân' },
]

const TIEU_DE = {
  tong_quan: 'Tổng quan',
  danh_muc: 'Quản lý danh mục chuyên đề / dạng',
  cau_hoi: 'Quản lý câu hỏi',
  ai_sinh: 'AI sinh câu hỏi',
  co: 'Cờ theo dõi',
  ho_tro: 'Hỗ trợ học sinh (Nhờ thầy/cô)',
  nhiem_vu: 'Giao bài / nhiệm vụ',
  tien_bo: 'Theo dõi tiến bộ học sinh',
  lop: 'Quản lý lớp',
  hoc_sinh: 'Quản lý học sinh',
  tai_khoan: 'Tài khoản cá nhân',
  noi_dung_gv: 'Quản lý nội dung theo giáo viên',
}

export default function GiaoVienApp({ onLogout }) {
  const sess = getSession() || {}
  const [hoTen, setHoTen] = useState(sess.ho_ten || '')
  const la_quan_ly = sess.la_quan_ly
  const nav = la_quan_ly ? NAV_QUAN_LY : NAV

  function capNhatHoTen(ten) {
    updateHoTen(ten)
    setHoTen(ten)
  }
  const navKeys = nav.map((n) => n.key)
  const defaultPage = navKeys[0]

  function pageFromHash() {
    const h = window.location.hash.slice(1)
    return navKeys.includes(h) ? h : defaultPage
  }

  const [page, setPage] = useState(pageFromHash)
  // { id, ts } | null — yêu cầu "Nhờ thầy/cô" cần nhảy tới + làm nổi bật khi GV bấm thông
  // báo "Học sinh nhờ trợ giúp" ở chuông. "ts" đổi mỗi lần bấm để ép hiệu ứng chạy lại kể
  // cả bấm trùng đúng yêu cầu đã focus trước đó.
  const [focusYc, setFocusYc] = useState(null)
  // { id, ts } | null — cờ theo dõi cần nhảy tới + làm nổi bật khi GV bấm thông báo
  // "⚠️/🆘 ..." ở chuông (nội dung không phù hợp / khẩn cấp).
  const [focusCo, setFocusCo] = useState(null)

  function navigate(key) {
    window.location.hash = key
    setPage(key)
  }

  // ChuongThongBao gọi hàm này cho MỌI loại thông báo có liên kết — mỗi loại nhảy tới đúng
  // trang tương ứng ở app GV: "yeu_cau_tro_giup" → Hỗ trợ học sinh, "co" → Cờ theo dõi.
  function moTuThongBao(tb) {
    if (tb.lien_ket_loai === 'yeu_cau_tro_giup' && navKeys.includes('ho_tro')) {
      setFocusYc({ id: tb.lien_ket_id, ts: Date.now() })
      navigate('ho_tro')
    } else if (tb.lien_ket_loai === 'co' && navKeys.includes('co')) {
      setFocusCo({ id: tb.lien_ket_id, ts: Date.now() })
      navigate('co')
    }
  }

  useEffect(() => {
    function onHashChange() {
      setPage(pageFromHash())
    }
    window.addEventListener('hashchange', onHashChange)
    return () => window.removeEventListener('hashchange', onHashChange)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return (
    <RoleLayout
      vai_tro="gv"
      ho_ten={hoTen}
      nav={nav}
      active={page}
      onNavigate={navigate}
      onLogout={() => {
        clearSession()
        onLogout()
      }}
      title={TIEU_DE[page]}
      onMoLienKet={moTuThongBao}
    >
      <Suspense fallback={<p className="text-muted text-sm">Đang tải...</p>}>
        {page === 'noi_dung_gv' && <QuanLyNoiDungGV />}
        {page === 'tong_quan' && <TongQuan onNavigate={navigate} />}
        {page === 'danh_muc' && <QuanLyDanhMuc />}
        {page === 'cau_hoi' && <QuanLyCauHoi />}
        {page === 'ai_sinh' && <AISinhCauHoi />}
        {page === 'co' && (
          <QuanLyCo focusId={focusCo} onFocusDone={() => setFocusCo(null)} />
        )}
        {page === 'ho_tro' && (
          <HoTroHocSinh focusYc={focusYc} onFocusDone={() => setFocusYc(null)} />
        )}
        {page === 'nhiem_vu' && <GiaoNhiemVu />}
        {page === 'de_thi' && <QuanLyDeThi />}
        {page === 'tien_bo' && <TheoDoiTienBo />}
        {page === 'lop' && <QuanLyLopGV />}
        {page === 'hoc_sinh' && <QuanLyHocSinhGV />}
        {page === 'tai_khoan' && <TaiKhoanCaNhan onHoTenChange={capNhatHoTen} />}
      </Suspense>
    </RoleLayout>
  )
}
