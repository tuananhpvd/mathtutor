"""API quản trị (Phase 10): thống kê, tài khoản, cấu hình."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.deps import CurrentUser, require_role
from app.db.session import get_db
from app.models.user import VaiTro
from app.schemas.admin import (
    DatCauHinhRequest,
    DoiTrangThaiRequest,
    GanLopRequest,
    HoSoUpdate,
    ImportTaiKhoanRequest,
    KiemTraDangNhapRequest,
    KiemTraTuKhoaRequest,
    SuaLopRequest,
    SuaTaiKhoanRequest,
    TaoLopRequest,
    TaoTaiKhoanRequest,
)
from app.schemas.gv import ImportHSBatchRequest, KiemTraHSRequest
from app.services.admin_service import (
    cap_nhat_ho_so_admin,
    danh_sach_giao_vien,
    danh_sach_hoc_sinh,
    danh_sach_lop,
    danh_sach_lop_chi_tiet,
    danh_sach_tai_khoan,
    dat_cau_hinh,
    doi_trang_thai_tai_khoan,
    gan_lop_tai_khoan,
    ho_so_admin,
    import_tai_khoan_batch,
    lay_cau_hinh_an_toan,
    sua_lop,
    sua_tai_khoan,
    tao_lop,
    tao_tai_khoan,
    thong_ke,
    xoa_lop,
    xoa_tai_khoan,
)
from app.services.gv_service import import_hs_batch_admin, kiem_tra_trung_dang_nhap

router = APIRouter(prefix="/api/admin", tags=["admin"])
_ADMIN = [require_role(VaiTro.admin)]


@router.get("/stats", dependencies=_ADMIN)
def stats(current_user: CurrentUser, db: Session = Depends(get_db)):
    return thong_ke(db)


@router.get("/ho-so", dependencies=_ADMIN)
def ho_so(current_user: CurrentUser):
    return ho_so_admin(current_user)


@router.patch("/ho-so", dependencies=_ADMIN)
def cap_nhat_ho_so(body: HoSoUpdate, current_user: CurrentUser, db: Session = Depends(get_db)):
    admin = cap_nhat_ho_so_admin(db, current_user, body.ho_ten, body.mat_khau)
    return ho_so_admin(admin)


@router.get("/llm-theo-ngay", dependencies=_ADMIN)
def llm_theo_ngay(current_user: CurrentUser, db: Session = Depends(get_db)):
    """Lượt gọi LLM thật mỗi ngày (30 ngày, theo loại) — theo dõi quota Gemini."""
    from app.services.llm_quota_service import su_dung_theo_ngay

    return su_dung_theo_ngay(db)


@router.get("/phien-theo-ngay", dependencies=_ADMIN)
def phien_theo_ngay_api(current_user: CurrentUser, db: Session = Depends(get_db)):
    """Số phiên học bắt đầu mỗi ngày toàn hệ thống (30 ngày)."""
    from app.services.admin_service import phien_theo_ngay

    return phien_theo_ngay(db)


@router.get("/users", dependencies=_ADMIN)
def users(current_user: CurrentUser, db: Session = Depends(get_db)):
    return danh_sach_tai_khoan(db)


@router.post("/users", dependencies=_ADMIN)
def tao_user(body: TaoTaiKhoanRequest, current_user: CurrentUser, db: Session = Depends(get_db)):
    try:
        u = tao_tai_khoan(db, body.ho_ten, body.dang_nhap, body.mat_khau, body.vai_tro, body.lop_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return {"id": u.id, "dang_nhap": u.dang_nhap, "vai_tro": u.vai_tro.value}


@router.post("/users/kiem-tra-dang-nhap", dependencies=_ADMIN)
def kiem_tra_dang_nhap(body: KiemTraDangNhapRequest, db: Session = Depends(get_db)):
    """Kiểm tra tên đăng nhập nào đã tồn tại trong toàn hệ thống."""
    trung = kiem_tra_trung_dang_nhap(db, body.dang_nhaps)
    return {"trung": trung}


@router.post("/users/import-batch", dependencies=_ADMIN)
def import_users_batch(body: ImportTaiKhoanRequest, db: Session = Depends(get_db)):
    """Tạo hàng loạt tài khoản GV/HS. Bỏ qua tên đăng nhập đã tồn tại."""
    try:
        result = import_tai_khoan_batch(db, [t.model_dump() for t in body.tai_khoans])
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return result


@router.patch("/users/{user_id}", dependencies=_ADMIN)
def sua_user(user_id: int, body: SuaTaiKhoanRequest, current_user: CurrentUser,
             db: Session = Depends(get_db)):
    try:
        u = sua_tai_khoan(db, user_id, body.model_dump(exclude_unset=True))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return {"id": u.id, "ho_ten": u.ho_ten, "dang_nhap": u.dang_nhap, "vai_tro": u.vai_tro.value}


@router.delete("/users/{user_id}", dependencies=_ADMIN)
def xoa_user(user_id: int, current_user: CurrentUser, db: Session = Depends(get_db)):
    try:
        xoa_tai_khoan(db, user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return {"ok": True}


@router.get("/lop", dependencies=_ADMIN)
def lop(current_user: CurrentUser, db: Session = Depends(get_db)):
    return danh_sach_lop(db)


@router.get("/lop-chi-tiet", dependencies=_ADMIN)
def lop_chi_tiet(current_user: CurrentUser, db: Session = Depends(get_db)):
    return danh_sach_lop_chi_tiet(db)


@router.post("/lop", dependencies=_ADMIN)
def them_lop(body: TaoLopRequest, current_user: CurrentUser, db: Session = Depends(get_db)):
    try:
        lop_ = tao_lop(db, body.ten, body.gv_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return {"id": lop_.id, "ten": lop_.ten, "gv_id": lop_.gv_id}


@router.patch("/lop/{lop_id}", dependencies=_ADMIN)
def cap_nhat_lop(lop_id: int, body: SuaLopRequest, current_user: CurrentUser,
                 db: Session = Depends(get_db)):
    try:
        lop_ = sua_lop(db, lop_id, body.model_dump(exclude_unset=True))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return {"id": lop_.id, "ten": lop_.ten, "gv_id": lop_.gv_id}


@router.delete("/lop/{lop_id}", dependencies=_ADMIN)
def xoa_lop_ep(lop_id: int, current_user: CurrentUser, db: Session = Depends(get_db)):
    try:
        xoa_lop(db, lop_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return {"ok": True}


@router.get("/giao-vien", dependencies=_ADMIN)
def giao_vien(current_user: CurrentUser, db: Session = Depends(get_db)):
    return danh_sach_giao_vien(db)


@router.get("/hoc-sinh", dependencies=_ADMIN)
def hoc_sinh(current_user: CurrentUser, db: Session = Depends(get_db)):
    return danh_sach_hoc_sinh(db)


@router.patch("/users/{user_id}/lop", dependencies=_ADMIN)
def gan_lop(user_id: int, body: GanLopRequest, current_user: CurrentUser,
            db: Session = Depends(get_db)):
    try:
        u = gan_lop_tai_khoan(db, user_id, body.lop_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return {"id": u.id, "lop_id": u.lop_id}


@router.patch("/users/{user_id}/trang-thai", dependencies=_ADMIN)
def doi_trang_thai(
    user_id: int,
    body: DoiTrangThaiRequest,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    try:
        u = doi_trang_thai_tai_khoan(db, user_id, body.trang_thai)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return {"id": u.id, "trang_thai": u.trang_thai.value}


@router.get("/config", dependencies=_ADMIN)
def get_config(current_user: CurrentUser, db: Session = Depends(get_db)):
    return lay_cau_hinh_an_toan(db)


@router.patch("/config", dependencies=_ADMIN)
def set_config(body: DatCauHinhRequest, current_user: CurrentUser, db: Session = Depends(get_db)):
    try:
        return dat_cau_hinh(db, body.khoa, body.gia_tri)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/tu-khoa-thu", dependencies=_ADMIN)
def tu_khoa_thu(body: KiemTraTuKhoaRequest, db: Session = Depends(get_db)):
    """'Thử trước' cho trang quản lý từ khóa an toàn — chạy kiểm tra thật với đúng danh
    sách từ khóa đang lưu (không tạo phiên học, không gắn cờ)."""
    from app.services.admin_service import kiem_tra_thu_an_toan

    ks = kiem_tra_thu_an_toan(db, body.van_ban)
    return {
        "an_toan": ks.an_toan,
        "ly_do": ks.ly_do,
        "khan_cap": ks.khan_cap,
        "ngoai_pham_vi": ks.ngoai_pham_vi,
    }


@router.post("/lop/{lop_id}/kiem-tra-hs", dependencies=_ADMIN)
def admin_kiem_tra_hs(lop_id: int, body: KiemTraHSRequest, db: Session = Depends(get_db)):
    """Kiểm tra tên đăng nhập nào đã tồn tại trong toàn hệ thống."""
    trung = kiem_tra_trung_dang_nhap(db, body.dang_nhaps)
    return {"trung": trung}


@router.post("/lop/{lop_id}/import-hs-batch", dependencies=_ADMIN)
def admin_import_hs_batch(lop_id: int, body: ImportHSBatchRequest,
                          db: Session = Depends(get_db)):
    """Admin: tạo hàng loạt học sinh vào lớp."""
    try:
        result = import_hs_batch_admin(db, lop_id, [h.model_dump() for h in body.hoc_sinhs])
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return result


@router.get("/llm-su-dung", dependencies=_ADMIN)
def llm_su_dung_hom_nay(current_user: CurrentUser, db: Session = Depends(get_db)):
    """Số lượt gọi LLM thật hôm nay + các giới hạn đang đặt (phanh chi phí)."""
    from app.services.admin_service import lay_cau_hinh
    from app.services.llm_quota_service import thong_ke_su_dung

    return thong_ke_su_dung(db, lay_cau_hinh(db))


@router.post("/phan-tich/quet", dependencies=_ADMIN)
def quet_phan_tich_ngay(current_user: CurrentUser, db: Session = Depends(get_db)):
    """Chạy quét tái sinh phân tích AI ngay (không chờ lịch nền)."""
    from app.llm.client import StubLLMClient, get_llm_client
    from app.services.admin_service import lay_cau_hinh
    from app.services.llm_quota_service import (
        LOAI_PHAN_TICH,
        LOI_HET_QUOTA,
        ghi_luot,
        vuot_nguong_he_thong,
    )
    from app.services.phan_tich_service import quet_tai_sinh

    cau_hinh = lay_cau_hinh(db)
    llm = get_llm_client(cau_hinh)
    dung_llm_that = not isinstance(llm, StubLLMClient)
    if dung_llm_that and vuot_nguong_he_thong(db, cau_hinh):
        raise HTTPException(status_code=429, detail=LOI_HET_QUOTA)
    ket = quet_tai_sinh(db, llm)
    if dung_llm_that:
        ghi_luot(db, None, LOAI_PHAN_TICH, so=ket.get("da_quet", 0))
    return ket
