"""API cho học sinh: hồ sơ cá nhân."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.deps import CurrentUser, require_role
from app.db.session import get_db
from app.models.user import VaiTro
from app.schemas.hs import HoSoUpdate
from app.services import chuoi_ngay_service, hs_service

router = APIRouter(prefix="/api/hs", tags=["hs"])
_HS = [require_role(VaiTro.hs)]


@router.get("/ho-so", dependencies=_HS)
def ho_so(current_user: CurrentUser, db: Session = Depends(get_db)):
    return hs_service.ho_so(db, current_user)


@router.patch("/ho-so", dependencies=_HS)
def cap_nhat_ho_so(body: HoSoUpdate, current_user: CurrentUser, db: Session = Depends(get_db)):
    hs = hs_service.cap_nhat_ho_so(db, current_user, body.ho_ten, body.mat_khau)
    return hs_service.ho_so(db, hs)


@router.get("/chuoi-ngay", dependencies=_HS)
def chuoi_ngay(current_user: CurrentUser, db: Session = Depends(get_db)):
    return chuoi_ngay_service.ho_so_chuoi_va_moc(db, current_user.id)


@router.post("/da-xem-huong-dan-phong-hoc", dependencies=_HS)
def da_xem_huong_dan_phong_hoc(current_user: CurrentUser, db: Session = Depends(get_db)):
    """Đánh dấu HS đã xem hướng dẫn 3 bước lúc vào phòng học — chỉ hiện 1 lần/tài khoản."""
    hs_service.danh_dau_da_xem_huong_dan(db, current_user)
    return {"ok": True}
