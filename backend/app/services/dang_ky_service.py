"""HS tự đăng ký bằng MÃ LỚP (mức 1 lộ trình gỡ nút thắt triển khai).

Bối cảnh thiết kế: trước đây chỉ GV/Admin tạo được tài khoản HS → muốn dùng sản phẩm thì
phải chờ GV nhập tay từng em. Mã lớp bỏ được rào cản đó mà KHÔNG phá vỡ chuỗi trách nhiệm:
mọi HS tự đăng ký vẫn phải thuộc một lớp có GV phụ trách.

Đây là luồng đi qua endpoint CÔNG KHAI đầu tiên của hệ thống nên mọi ràng buộc an toàn được
gom hết vào đây (không rải ở tầng API) để dễ kiểm và dễ test.
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.auth.security import hash_password
from app.core.ma_lop import chuan_hoa
from app.models.lop import Lop
from app.models.thong_bao import LoaiThongBao
from app.models.user import TrangThaiUser, User, VaiTro

# Hai lớp chặn spam khi mã bị phát tán ra ngoài lớp — lớp thật không chạm tới ngưỡng nào:
#   - theo NGÀY: chặn đợt đăng ký ồ ạt (dựa trên `users.tao_luc`);
#   - theo TỔNG sĩ số: chặn kiểu nhỏ giọt kéo dài nhiều ngày mà trần/ngày không bắt được.
TRAN_DANG_KY_NGAY = 60
TRAN_HS_MOI_LOP = 100

SO_NGAY_HIEU_LUC_MAC_DINH = 30


class LoiDangKy(ValueError):
    """Lỗi nghiệp vụ khi đăng ký. `ma_sai=True` nghĩa là lỗi do MÃ (dùng để tính throttle)."""

    def __init__(self, thong_diep: str, ma_sai: bool = False):
        super().__init__(thong_diep)
        self.ma_sai = ma_sai


def lop_theo_ma(db: Session, ma: str) -> Lop:
    """Tra lớp từ mã. Raise LoiDangKy(ma_sai=True) nếu mã không dùng được.

    CỐ Ý gộp mọi trường hợp mã hỏng vào một thông điệp: không phân biệt "mã không tồn tại"
    với "mã đã hết hạn/đã thu hồi" để người dò mã không suy ra được mã nào từng có thật.
    """
    sach = chuan_hoa(ma)
    lop = db.query(Lop).filter(Lop.ma_lop == sach).first() if sach else None
    if lop is None:
        raise LoiDangKy("Mã lớp không đúng hoặc đã hết hiệu lực", ma_sai=True)
    if lop.ma_het_han is not None:
        het_han = lop.ma_het_han
        if het_han.tzinfo is None:
            het_han = het_han.replace(tzinfo=timezone.utc)
        if het_han < datetime.now(timezone.utc):
            raise LoiDangKy("Mã lớp không đúng hoặc đã hết hiệu lực", ma_sai=True)
    # Giữ chuỗi trách nhiệm: lớp không có GV thì không ai duyệt câu hỏi, không ai trả lời
    # "Nhờ thầy/cô", không ai xử lý cờ khi em bí → không cho tự đăng ký vào.
    if lop.gv_id is None:
        raise LoiDangKy("Lớp này chưa có giáo viên phụ trách nên chưa nhận đăng ký")
    return lop


def _si_so(db: Session, lop_id: int) -> int:
    return (
        db.query(User)
        .filter(User.lop_id == lop_id, User.vai_tro == VaiTro.hs)
        .count()
    )


def _so_dang_ky_24h(db: Session, lop_id: int) -> int:
    """Số HS vào lớp này trong 24h qua. Tài khoản có TRƯỚC cột `tao_luc` mang giá trị NULL —
    chúng là tài khoản cũ nên KHÔNG tính vào cửa sổ 24h (điều kiện `is not None` cần thiết vì
    so sánh NULL >= mốc luôn trả NULL/False, dễ gây hiểu nhầm là đã lọc đúng)."""
    moc = datetime.now(timezone.utc) - timedelta(days=1)
    return (
        db.query(User)
        .filter(
            User.lop_id == lop_id,
            User.vai_tro == VaiTro.hs,
            User.tao_luc.is_not(None),
            User.tao_luc >= moc,
        )
        .count()
    )


def dang_ky_bang_ma(db: Session, ma: str, ho_ten: str, dang_nhap: str, mat_khau: str) -> User:
    """Tạo tài khoản HS và gắn vào đúng lớp của mã. Trả về User đã commit."""
    lop = lop_theo_ma(db, ma)

    dang_nhap = (dang_nhap or "").strip()
    ho_ten = (ho_ten or "").strip()
    if not dang_nhap or not ho_ten:
        raise LoiDangKy("Họ tên và tên đăng nhập không được để trống")
    if db.query(User).filter(User.dang_nhap == dang_nhap).first() is not None:
        raise LoiDangKy("Tên đăng nhập đã có người dùng, em chọn tên khác nhé")
    if _so_dang_ky_24h(db, lop.id) >= TRAN_DANG_KY_NGAY:
        raise LoiDangKy("Lớp này đã nhận quá nhiều đăng ký hôm nay, em báo thầy/cô nhé")
    if _si_so(db, lop.id) >= TRAN_HS_MOI_LOP:
        raise LoiDangKy("Lớp này đã đủ sĩ số, em báo thầy/cô nhé")

    hs = User(
        vai_tro=VaiTro.hs,           # CỨNG — không lấy từ input
        ho_ten=ho_ten,
        dang_nhap=dang_nhap,
        mat_khau_hash=hash_password(mat_khau),
        trang_thai=TrangThaiUser.hoat_dong,
        lop_id=lop.id,               # lấy từ MÃ, không lấy từ input
    )
    db.add(hs)
    db.flush()
    _bao_gv(db, lop, hs)
    db.commit()
    db.refresh(hs)
    return hs


def _bao_gv(db: Session, lop: Lop, hs: User) -> None:
    """Báo GV có HS mới tự vào lớp — thầy cô luôn biết ai đang ở trong lớp mình và khóa được
    ngay nếu thấy lạ (đây là cái bù cho việc không bắt duyệt trước)."""
    from app.services import thong_bao_service

    try:
        thong_bao_service.tao(
            db,
            nguoi_nhan_id=lop.gv_id,
            noi_dung=f"{hs.ho_ten} vừa tự đăng ký vào lớp {lop.ten} bằng mã lớp.",
            loai=LoaiThongBao.he_thong,
            tieu_de="Học sinh mới vào lớp",
        )
    except Exception:  # thông báo hỏng không được chặn việc đăng ký
        pass


# ----- GV quản lý mã -----

def tao_ma_lop(db: Session, lop: Lop, so_ngay: int = SO_NGAY_HIEU_LUC_MAC_DINH) -> Lop:
    """Sinh mã mới cho lớp (đổi mã = thu hồi mã cũ + gia hạn). Bảo đảm không trùng."""
    from app.core.ma_lop import sinh_ma

    for _ in range(20):
        ma = sinh_ma()
        if db.query(Lop).filter(Lop.ma_lop == ma).first() is None:
            lop.ma_lop = ma
            break
    else:  # gần như không thể xảy ra với không gian mã 31^8
        raise LoiDangKy("Không sinh được mã lớp, thử lại giúp tôi")
    lop.ma_het_han = (
        datetime.now(timezone.utc) + timedelta(days=so_ngay) if so_ngay else None
    )
    db.commit()
    db.refresh(lop)
    return lop


def thu_hoi_ma_lop(db: Session, lop: Lop) -> Lop:
    """Đóng lớp với người mới. `ma_lop=NULL` chính là trạng thái 'không nhận đăng ký'."""
    lop.ma_lop = None
    lop.ma_het_han = None
    db.commit()
    db.refresh(lop)
    return lop
