"""API thông báo — mỗi người dùng chỉ đọc/đánh dấu thông báo của chính mình."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.deps import CurrentUser
from app.db.session import get_db
from app.services import thong_bao_service

router = APIRouter(prefix="/api/thong-bao", tags=["thong-bao"])


@router.get("")
def danh_sach(current_user: CurrentUser, db: Session = Depends(get_db)):
    return thong_bao_service.danh_sach(db, current_user.id)


@router.get("/chua-doc")
def chua_doc(current_user: CurrentUser, db: Session = Depends(get_db)):
    return {"so_luong": thong_bao_service.dem_chua_doc(db, current_user.id)}


@router.post("/{tb_id}/da-doc")
def da_doc(tb_id: int, current_user: CurrentUser, db: Session = Depends(get_db)):
    return {"ok": thong_bao_service.danh_dau_da_doc(db, current_user.id, tb_id)}


@router.post("/doc-het")
def doc_het(current_user: CurrentUser, db: Session = Depends(get_db)):
    return {"so_luong": thong_bao_service.danh_dau_het(db, current_user.id)}
