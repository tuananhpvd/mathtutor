"""API tiến độ học tập (Phase 6)."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.deps import CurrentUser, require_role
from app.db.session import get_db
from app.models.user import VaiTro
from app.services.progress_service import tien_do_cua_hs, tien_do_lop

router = APIRouter(prefix="/api/progress", tags=["progress"])


@router.get("/me", dependencies=[require_role(VaiTro.hs)])
def tien_do_cua_toi(current_user: CurrentUser, db: Session = Depends(get_db)):
    return tien_do_cua_hs(db, current_user.id)


@router.get("/students", dependencies=[require_role(VaiTro.gv, VaiTro.admin)])
def tien_do_hoc_sinh(current_user: CurrentUser, db: Session = Depends(get_db)):
    return tien_do_lop(db, current_user.id)
