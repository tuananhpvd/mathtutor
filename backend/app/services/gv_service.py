"""Service cho giáo viên: hồ sơ cá nhân, quản lý lớp & học sinh thuộc phạm vi của mình."""

from sqlalchemy.orm import Session

from app.auth.security import hash_password
from app.models.lop import Lop
from app.models.progress import Progress
from app.models.session import Session as SessionModel
from app.models.user import TrangThaiUser, User, VaiTro


def _hs_dict(u: User) -> dict:
    return {
        "id": u.id, "ho_ten": u.ho_ten, "dang_nhap": u.dang_nhap,
        "trang_thai": u.trang_thai.value, "lop_id": u.lop_id,
    }


def _so_huu_lop(db: Session, gv_id: int, lop_id: int) -> bool:
    lop = db.get(Lop, lop_id)
    return lop is not None and lop.gv_id == gv_id


def _so_huu_hs(db: Session, gv_id: int, hs_id: int) -> bool:
    hs = db.get(User, hs_id)
    if hs is None or hs.vai_tro != VaiTro.hs or hs.lop_id is None:
        return False
    return _so_huu_lop(db, gv_id, hs.lop_id)


# ---------- Hồ sơ cá nhân ----------

def ho_so(gv: User) -> dict:
    return {
        "id": gv.id, "ho_ten": gv.ho_ten, "dang_nhap": gv.dang_nhap,
        "vai_tro": gv.vai_tro.value, "trang_thai": gv.trang_thai.value,
    }


def cap_nhat_ho_so(db: Session, gv: User, ho_ten: str | None, mat_khau: str | None) -> User:
    if ho_ten:
        gv.ho_ten = ho_ten.strip()
    if mat_khau:
        gv.mat_khau_hash = hash_password(mat_khau)
    db.commit()
    db.refresh(gv)
    return gv


# ---------- Lớp của GV ----------

def lop_cua_gv(db: Session, gv_id: int) -> list[dict]:
    lops = db.query(Lop).filter(Lop.gv_id == gv_id).order_by(Lop.ten).all()
    hs_by_lop: dict = {}
    for hs in db.query(User).filter(User.vai_tro == VaiTro.hs).all():
        hs_by_lop.setdefault(hs.lop_id, []).append(hs)
    return [
        {
            "id": lop.id, "ten": lop.ten,
            "so_hoc_sinh": len(hs_by_lop.get(lop.id, [])),
            "hoc_sinhs": [_hs_dict(h) for h in hs_by_lop.get(lop.id, [])],
        }
        for lop in lops
    ]


def tao_lop_gv(db: Session, gv_id: int, ten: str) -> Lop:
    if not ten or not ten.strip():
        raise ValueError("Tên lớp không được rỗng")
    lop = Lop(ten=ten.strip(), gv_id=gv_id)
    db.add(lop)
    db.commit()
    db.refresh(lop)
    return lop


def sua_lop_gv(db: Session, gv_id: int, lop_id: int, ten: str) -> Lop:
    if not _so_huu_lop(db, gv_id, lop_id):
        raise ValueError("Không có quyền với lớp này")
    if not ten or not ten.strip():
        raise ValueError("Tên lớp không được rỗng")
    lop = db.get(Lop, lop_id)
    lop.ten = ten.strip()
    db.commit()
    db.refresh(lop)
    return lop


def xoa_lop_gv(db: Session, gv_id: int, lop_id: int) -> None:
    if not _so_huu_lop(db, gv_id, lop_id):
        raise ValueError("Không có quyền với lớp này")
    for hs in db.query(User).filter(User.lop_id == lop_id).all():
        hs.lop_id = None
    db.delete(db.get(Lop, lop_id))
    db.commit()


# ---------- Học sinh của GV ----------

def danh_sach_hs_gv(db: Session, gv_id: int) -> list[dict]:
    lop_ids = [lop.id for lop in db.query(Lop).filter(Lop.gv_id == gv_id).all()]
    if not lop_ids:
        return []
    lop_ten = {lop.id: lop.ten for lop in db.query(Lop).filter(Lop.id.in_(lop_ids)).all()}
    hss = (
        db.query(User)
        .filter(User.vai_tro == VaiTro.hs, User.lop_id.in_(lop_ids))
        .order_by(User.ho_ten)
        .all()
    )
    return [{**_hs_dict(h), "lop_ten": lop_ten.get(h.lop_id)} for h in hss]


def tao_hs_gv(db: Session, gv_id: int, ho_ten: str, dang_nhap: str,
              mat_khau: str, lop_id: int) -> User:
    if not _so_huu_lop(db, gv_id, lop_id):
        raise ValueError("Phải chọn một lớp bạn phụ trách")
    if db.query(User).filter(User.dang_nhap == dang_nhap).first():
        raise ValueError("Tên đăng nhập đã tồn tại")
    hs = User(
        vai_tro=VaiTro.hs, ho_ten=ho_ten.strip(), dang_nhap=dang_nhap.strip(),
        mat_khau_hash=hash_password(mat_khau), lop_id=lop_id,
    )
    db.add(hs)
    db.commit()
    db.refresh(hs)
    return hs


def sua_hs_gv(db: Session, gv_id: int, hs_id: int, du_lieu: dict) -> User:
    if not _so_huu_hs(db, gv_id, hs_id):
        raise ValueError("Không có quyền với học sinh này")
    hs = db.get(User, hs_id)
    if "dang_nhap" in du_lieu and du_lieu["dang_nhap"]:
        dn = du_lieu["dang_nhap"].strip()
        if dn != hs.dang_nhap and db.query(User).filter(
            User.dang_nhap == dn, User.id != hs_id
        ).first():
            raise ValueError("Tên đăng nhập đã tồn tại")
        hs.dang_nhap = dn
    if "ho_ten" in du_lieu and du_lieu["ho_ten"]:
        hs.ho_ten = du_lieu["ho_ten"].strip()
    if "mat_khau" in du_lieu and du_lieu["mat_khau"]:
        hs.mat_khau_hash = hash_password(du_lieu["mat_khau"])
    db.commit()
    db.refresh(hs)
    return hs


def gan_lop_hs_gv(db: Session, gv_id: int, hs_id: int, lop_id: int) -> User:
    if not _so_huu_hs(db, gv_id, hs_id):
        raise ValueError("Không có quyền với học sinh này")
    if not _so_huu_lop(db, gv_id, lop_id):
        raise ValueError("Chỉ được gán vào lớp bạn phụ trách")
    hs = db.get(User, hs_id)
    hs.lop_id = lop_id
    db.commit()
    db.refresh(hs)
    return hs


def khoa_hs_gv(db: Session, gv_id: int, hs_id: int, trang_thai: str) -> User:
    if not _so_huu_hs(db, gv_id, hs_id):
        raise ValueError("Không có quyền với học sinh này")
    hs = db.get(User, hs_id)
    hs.trang_thai = TrangThaiUser(trang_thai)
    db.commit()
    db.refresh(hs)
    return hs


def xoa_hs_gv(db: Session, gv_id: int, hs_id: int) -> None:
    if not _so_huu_hs(db, gv_id, hs_id):
        raise ValueError("Không có quyền với học sinh này")
    if db.query(SessionModel).filter(SessionModel.hoc_sinh_id == hs_id).count() > 0:
        raise ValueError("Học sinh đã có dữ liệu làm bài, không thể xóa — hãy Khóa tài khoản")
    db.query(Progress).filter(Progress.hoc_sinh_id == hs_id).delete()
    db.delete(db.get(User, hs_id))
    db.commit()
