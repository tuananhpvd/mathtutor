from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.deps import CurrentUser, require_role
from app.db.session import get_db
from app.models.user import VaiTro
from app.services.dat_lai_service import dat_lai_tien_do

gv_router = APIRouter(prefix="/api/gv/dat-lai", tags=["dat-lai"])


@gv_router.post("/{hs_id}", dependencies=[require_role(VaiTro.gv)])
def gv_dat_lai(hs_id: int, current_user: CurrentUser, db: Session = Depends(get_db)):
    try:
        result = dat_lai_tien_do(db, hs_id, current_user.id)
        return {"ok": True, **result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
