"""API cho giáo viên: hồ sơ cá nhân, quản lý lớp & học sinh thuộc phạm vi của mình."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.deps import CurrentUser, require_role
from app.db.session import get_db
from app.models.user import VaiTro
from app.schemas.gv import (
    DoiTrangThaiRequest,
    GanLopRequest,
    GuiNhanXetRequest,
    HoSoUpdate,
    ImportHSBatchRequest,
    ImportLopRequest,
    KiemTraHSRequest,
    KiemTraTrungRequest,
    SuaHocSinhRequest,
    SuaLopGVRequest,
    TaoHocSinhRequest,
    TaoLopGVRequest,
)
from app.services import gv_service

router = APIRouter(prefix="/api/gv", tags=["gv"])
_GV = [require_role(VaiTro.gv)]


@router.get("/tong-quan", dependencies=_GV)
def tong_quan(current_user: CurrentUser, db: Session = Depends(get_db)):
    return gv_service.tong_quan_gv(db, current_user.id)


@router.get("/ho-so", dependencies=_GV)
def ho_so(current_user: CurrentUser):
    return gv_service.ho_so(current_user)


@router.patch("/ho-so", dependencies=_GV)
def cap_nhat_ho_so(body: HoSoUpdate, current_user: CurrentUser, db: Session = Depends(get_db)):
    gv = gv_service.cap_nhat_ho_so(db, current_user, body.ho_ten, body.mat_khau)
    return gv_service.ho_so(gv)


@router.get("/lop", dependencies=_GV)
def lop(current_user: CurrentUser, db: Session = Depends(get_db)):
    return gv_service.lop_cua_gv(db, current_user.id)


@router.post("/lop", dependencies=_GV)
def them_lop(body: TaoLopGVRequest, current_user: CurrentUser, db: Session = Depends(get_db)):
    try:
        lop_ = gv_service.tao_lop_gv(db, current_user.id, body.ten)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"id": lop_.id, "ten": lop_.ten}


@router.post("/lop/kiem-tra-trung", dependencies=_GV)
def kiem_tra_trung(body: KiemTraTrungRequest, current_user: CurrentUser,
                   db: Session = Depends(get_db)):
    """Kiểm tra tên nào trong danh sách đã tồn tại trong lớp của GV này."""
    return gv_service.kiem_tra_trung_ten_lop(db, current_user.id, body.ten_lops)


@router.post("/lop/import-batch", dependencies=_GV)
def import_lop_batch(body: ImportLopRequest, current_user: CurrentUser, db: Session = Depends(get_db)):
    """Tạo nhiều lớp cùng lúc từ danh sách tên. Bỏ qua tên trùng hoặc rỗng."""
    da_tao, bo_qua = [], []
    for ten in body.ten_lops:
        ten = ten.strip()
        if not ten:
            continue
        try:
            lop_ = gv_service.tao_lop_gv(db, current_user.id, ten)
            da_tao.append(lop_.ten)
        except ValueError:
            bo_qua.append(ten)
    return {"da_tao": da_tao, "bo_qua": bo_qua}


@router.patch("/lop/{lop_id}", dependencies=_GV)
def sua_lop(lop_id: int, body: SuaLopGVRequest, current_user: CurrentUser,
            db: Session = Depends(get_db)):
    try:
        lop_ = gv_service.sua_lop_gv(db, current_user.id, lop_id, body.ten)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"id": lop_.id, "ten": lop_.ten}


@router.delete("/lop/{lop_id}", dependencies=_GV)
def xoa_lop(lop_id: int, current_user: CurrentUser, db: Session = Depends(get_db)):
    try:
        gv_service.xoa_lop_gv(db, current_user.id, lop_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"ok": True}


@router.get("/hoc-sinh", dependencies=_GV)
def hoc_sinh(current_user: CurrentUser, db: Session = Depends(get_db)):
    return gv_service.danh_sach_hs_gv(db, current_user.id)


@router.post("/hoc-sinh", dependencies=_GV)
def tao_hoc_sinh(body: TaoHocSinhRequest, current_user: CurrentUser,
                 db: Session = Depends(get_db)):
    try:
        hs = gv_service.tao_hs_gv(db, current_user.id, body.ho_ten, body.dang_nhap,
                                  body.mat_khau, body.lop_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"id": hs.id, "dang_nhap": hs.dang_nhap}


@router.patch("/hoc-sinh/{hs_id}", dependencies=_GV)
def sua_hoc_sinh(hs_id: int, body: SuaHocSinhRequest, current_user: CurrentUser,
                 db: Session = Depends(get_db)):
    try:
        hs = gv_service.sua_hs_gv(db, current_user.id, hs_id, body.model_dump(exclude_unset=True))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"id": hs.id, "ho_ten": hs.ho_ten, "dang_nhap": hs.dang_nhap}


@router.patch("/hoc-sinh/{hs_id}/lop", dependencies=_GV)
def gan_lop(hs_id: int, body: GanLopRequest, current_user: CurrentUser,
            db: Session = Depends(get_db)):
    try:
        hs = gv_service.gan_lop_hs_gv(db, current_user.id, hs_id, body.lop_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"id": hs.id, "lop_id": hs.lop_id}


@router.patch("/hoc-sinh/{hs_id}/trang-thai", dependencies=_GV)
def doi_trang_thai(hs_id: int, body: DoiTrangThaiRequest, current_user: CurrentUser,
                   db: Session = Depends(get_db)):
    try:
        hs = gv_service.khoa_hs_gv(db, current_user.id, hs_id, body.trang_thai)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"id": hs.id, "trang_thai": hs.trang_thai.value}


@router.delete("/hoc-sinh/{hs_id}", dependencies=_GV)
def xoa_hoc_sinh(hs_id: int, current_user: CurrentUser, db: Session = Depends(get_db)):
    try:
        gv_service.xoa_hs_gv(db, current_user.id, hs_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"ok": True}


@router.post("/lop/{lop_id}/kiem-tra-hs", dependencies=_GV)
def kiem_tra_hs(lop_id: int, body: KiemTraHSRequest, db: Session = Depends(get_db)):
    """Kiểm tra tên đăng nhập nào đã tồn tại trong toàn hệ thống."""
    trung = gv_service.kiem_tra_trung_dang_nhap(db, body.dang_nhaps)
    return {"trung": trung}


@router.post("/lop/{lop_id}/import-hs-batch", dependencies=_GV)
def import_hs_batch(lop_id: int, body: ImportHSBatchRequest, current_user: CurrentUser,
                    db: Session = Depends(get_db)):
    """Tạo hàng loạt học sinh vào lớp. Bỏ qua tên đăng nhập đã tồn tại."""
    try:
        result = gv_service.import_hs_batch(
            db, current_user.id, lop_id,
            [h.model_dump() for h in body.hoc_sinhs],
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return result


@router.get("/hoc-sinh/{hs_id}/nhan-xet-nhap", dependencies=_GV)
def nhan_xet_nhap(hs_id: int, current_user: CurrentUser, db: Session = Depends(get_db)):
    """Bản nháp nhận xét gợi ý (AI/luật) để GV duyệt/sửa trước khi gửi."""
    try:
        return {"noi_dung": gv_service.nhap_nhan_xet(db, current_user.id, hs_id)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/hoc-sinh/{hs_id}/nhan-xet", dependencies=_GV)
def gui_nhan_xet(hs_id: int, body: GuiNhanXetRequest, current_user: CurrentUser,
                 db: Session = Depends(get_db)):
    """GV gửi nhận xét cho HS (hiện trên Trang chủ HS + thông báo)."""
    try:
        return gv_service.gui_nhan_xet(db, current_user.id, hs_id, body.noi_dung)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
