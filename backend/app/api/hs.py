"""API cho học sinh: hồ sơ cá nhân."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.deps import CurrentUser, require_role
from app.db.session import get_db
from app.models.user import VaiTro
from app.schemas.hs import HoSoUpdate
from app.services import hs_service

router = APIRouter(prefix="/api/hs", tags=["hs"])
_HS = [require_role(VaiTro.hs)]


@router.get("/ho-so", dependencies=_HS)
def ho_so(current_user: CurrentUser, db: Session = Depends(get_db)):
    return hs_service.ho_so(db, current_user)


@router.patch("/ho-so", dependencies=_HS)
def cap_nhat_ho_so(body: HoSoUpdate, current_user: CurrentUser, db: Session = Depends(get_db)):
    hs = hs_service.cap_nhat_ho_so(db, current_user, body.ho_ten, body.mat_khau)
    return hs_service.ho_so(db, hs)
