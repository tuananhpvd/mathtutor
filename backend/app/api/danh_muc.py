"""API quản lý danh mục chuyên đề / dạng. Danh mục thuộc riêng từng GV.

- GV: xem/sửa/xóa danh mục của chính mình.
- HS: xem danh mục của GV chủ nhiệm lớp (để lọc bài luyện).
- Quản lý/Admin: xem/sửa/xóa danh mục của mọi GV (chọn qua ?gv_id=); khi sửa/xóa
  của GV khác thì gửi thông báo cho GV đó.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.deps import CurrentUser, co_toan_quyen, require_role
from app.db.session import get_db
from app.models.danh_muc import ChuyenDe, Dang
from app.models.lop import Lop
from app.models.thong_bao import LoaiThongBao
from app.models.user import User, VaiTro
from app.schemas.danh_muc import ChuyenDeCreate, ChuyenDeUpdate, DangCreate, DangUpdate
from app.services import thong_bao_service
from app.services.danh_muc_service import (
    lay_toan_bo_danh_muc,
    sua_chuyen_de,
    sua_dang,
    tao_chuyen_de,
    tao_dang,
    xoa_chuyen_de,
    xoa_dang,
)

router = APIRouter(prefix="/api/danh-muc", tags=["danh-muc"])

_GV_ADMIN = [require_role(VaiTro.gv, VaiTro.admin)]
_ALL = [require_role(VaiTro.hs, VaiTro.gv, VaiTro.admin)]


def _gv_id_cua_lop_hs(db: Session, hs: User) -> int | None:
    if hs.lop_id is None:
        return None
    lop = db.get(Lop, hs.lop_id)
    return lop.gv_id if lop else None


def _bao_quan_ly(db: Session, actor: User, owner_id: int | None, hanh_dong: str, ten: str) -> None:
    """Quản lý sửa/xóa danh mục của GV khác → thông báo cho chủ sở hữu."""
    if owner_id is None or owner_id == actor.id:
        return
    if actor.vai_tro != VaiTro.admin and not actor.la_quan_ly:
        return
    thong_bao_service.tao(
        db,
        nguoi_nhan_id=owner_id,
        noi_dung=f"{actor.ho_ten} {hanh_dong}: {ten}",
        loai=LoaiThongBao.quan_ly,
        nguoi_gui_id=actor.id,
        tieu_de="Quản lý cập nhật danh mục",
    )


def _quyen_tren_cd(user: User, cd: ChuyenDe) -> bool:
    return co_toan_quyen(user) or cd.nguoi_tao_id == user.id


def _quyen_tren_dang(user: User, d: Dang) -> bool:
    return co_toan_quyen(user) or d.nguoi_tao_id == user.id


# ---------- Danh sách GV (cho tài khoản Quản lý/Admin) ----------

@router.get("/giao-vien", dependencies=_GV_ADMIN)
def danh_sach_giao_vien(current_user: CurrentUser, db: Session = Depends(get_db)):
    """Danh sách GV thường để Quản lý chọn xem/sửa nội dung. Chỉ Quản lý/Admin."""
    if not co_toan_quyen(current_user):
        raise HTTPException(status_code=403, detail="Chỉ Quản lý hoặc Admin được xem danh sách này")
    gvs = (
        db.query(User)
        .filter(User.vai_tro == VaiTro.gv, User.la_quan_ly == False)  # noqa: E712
        .order_by(User.ho_ten)
        .all()
    )
    return [{"id": g.id, "ho_ten": g.ho_ten, "dang_nhap": g.dang_nhap} for g in gvs]


# ---------- GET cây danh mục ----------

@router.get("", dependencies=_ALL)
def get_danh_muc(current_user: CurrentUser, gv_id: int | None = None, db: Session = Depends(get_db)):
    if current_user.vai_tro == VaiTro.hs:
        # HS thấy danh mục của GV chủ nhiệm lớp mình.
        owner = _gv_id_cua_lop_hs(db, current_user)
        return lay_toan_bo_danh_muc(db, owner) if owner else []
    if co_toan_quyen(current_user):
        # Quản lý/Admin: theo gv_id nếu có, mặc định toàn bộ.
        return lay_toan_bo_danh_muc(db, gv_id)
    # GV thường: chỉ danh mục của mình.
    return lay_toan_bo_danh_muc(db, current_user.id)


# ---------- ChuyenDe CRUD ----------

@router.post("/chuyen-de", dependencies=_GV_ADMIN)
def them_chuyen_de(body: ChuyenDeCreate, current_user: CurrentUser, db: Session = Depends(get_db)):
    try:
        cd = tao_chuyen_de(db, body.ten, body.mo_ta, body.thu_tu, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return {"id": cd.id, "ten": cd.ten, "mo_ta": cd.mo_ta, "thu_tu": cd.thu_tu}


@router.patch("/chuyen-de/{cd_id}", dependencies=_GV_ADMIN)
def cap_nhat_chuyen_de(cd_id: int, body: ChuyenDeUpdate, current_user: CurrentUser,
                       db: Session = Depends(get_db)):
    cd = db.get(ChuyenDe, cd_id)
    if cd is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy chuyên đề")
    if not _quyen_tren_cd(current_user, cd):
        raise HTTPException(status_code=403, detail="Bạn không có quyền sửa chuyên đề này")
    owner_id, ten_cu = cd.nguoi_tao_id, cd.ten
    try:
        cd = sua_chuyen_de(db, cd_id, body.model_dump(exclude_none=True))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    _bao_quan_ly(db, current_user, owner_id, "đã sửa chuyên đề", ten_cu)
    return {"id": cd.id, "ten": cd.ten, "mo_ta": cd.mo_ta, "thu_tu": cd.thu_tu}


@router.delete("/chuyen-de/{cd_id}", dependencies=_GV_ADMIN)
def xoa_chuyen_de_api(cd_id: int, current_user: CurrentUser, db: Session = Depends(get_db)):
    cd = db.get(ChuyenDe, cd_id)
    if cd is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy chuyên đề")
    if not _quyen_tren_cd(current_user, cd):
        raise HTTPException(status_code=403, detail="Bạn không có quyền xóa chuyên đề này")
    owner_id, ten_cu = cd.nguoi_tao_id, cd.ten
    try:
        xoa_chuyen_de(db, cd_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    _bao_quan_ly(db, current_user, owner_id, "đã xóa chuyên đề", ten_cu)
    return {"ok": True}


# ---------- Dang CRUD ----------

@router.post("/dang", dependencies=_GV_ADMIN)
def them_dang(body: DangCreate, current_user: CurrentUser, db: Session = Depends(get_db)):
    cd = db.get(ChuyenDe, body.chuyen_de_id)
    if cd is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy chuyên đề")
    if not _quyen_tren_cd(current_user, cd):
        raise HTTPException(status_code=403, detail="Bạn không có quyền thêm dạng vào chuyên đề này")
    # Dạng thuộc cùng chủ sở hữu với chuyên đề (kể cả khi Quản lý thêm hộ).
    try:
        d = tao_dang(db, body.chuyen_de_id, body.ten, body.mo_ta, body.thu_tu, cd.nguoi_tao_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    _bao_quan_ly(db, current_user, cd.nguoi_tao_id, "đã thêm dạng vào chuyên đề", cd.ten)
    return {"id": d.id, "chuyen_de_id": d.chuyen_de_id, "ten": d.ten, "mo_ta": d.mo_ta, "thu_tu": d.thu_tu}


@router.patch("/dang/{dang_id}", dependencies=_GV_ADMIN)
def cap_nhat_dang(dang_id: int, body: DangUpdate, current_user: CurrentUser,
                  db: Session = Depends(get_db)):
    d = db.get(Dang, dang_id)
    if d is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy dạng")
    if not _quyen_tren_dang(current_user, d):
        raise HTTPException(status_code=403, detail="Bạn không có quyền sửa dạng này")
    owner_id, ten_cu = d.nguoi_tao_id, d.ten
    try:
        d = sua_dang(db, dang_id, body.model_dump(exclude_none=True))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    _bao_quan_ly(db, current_user, owner_id, "đã sửa dạng", ten_cu)
    return {"id": d.id, "chuyen_de_id": d.chuyen_de_id, "ten": d.ten, "mo_ta": d.mo_ta, "thu_tu": d.thu_tu}


@router.delete("/dang/{dang_id}", dependencies=_GV_ADMIN)
def xoa_dang_api(dang_id: int, current_user: CurrentUser, db: Session = Depends(get_db)):
    d = db.get(Dang, dang_id)
    if d is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy dạng")
    if not _quyen_tren_dang(current_user, d):
        raise HTTPException(status_code=403, detail="Bạn không có quyền xóa dạng này")
    owner_id, ten_cu = d.nguoi_tao_id, d.ten
    try:
        xoa_dang(db, dang_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    _bao_quan_ly(db, current_user, owner_id, "đã xóa dạng", ten_cu)
    return {"ok": True}
