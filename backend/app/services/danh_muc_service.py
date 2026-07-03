"""CRUD danh mục ChuyenDe / Dang. GV và Admin có quyền thêm/sửa/xóa."""

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.danh_muc import ChuyenDe, Dang
from app.models.problem import Problem

# ---------- ChuyenDe ----------

def lay_tat_ca_chuyen_de(db: Session, owner_id: int | None = None) -> list[ChuyenDe]:
    q = db.query(ChuyenDe)
    if owner_id is not None:
        q = q.filter(ChuyenDe.nguoi_tao_id == owner_id)
    return q.order_by(ChuyenDe.thu_tu, ChuyenDe.id).all()


def tao_chuyen_de(db: Session, ten: str, mo_ta: str | None, thu_tu: int, nguoi_tao_id: int) -> ChuyenDe:
    # Tên chỉ cần duy nhất trong phạm vi của chính người tạo.
    trung = db.query(ChuyenDe).filter(
        ChuyenDe.ten == ten, ChuyenDe.nguoi_tao_id == nguoi_tao_id
    ).first()
    if trung:
        raise ValueError(f"Chuyên đề '{ten}' đã tồn tại")
    cd = ChuyenDe(ten=ten, mo_ta=mo_ta, thu_tu=thu_tu, nguoi_tao_id=nguoi_tao_id)
    db.add(cd)
    db.commit()
    db.refresh(cd)
    return cd


def sua_chuyen_de(db: Session, cd_id: int, du_lieu: dict) -> ChuyenDe:
    cd = db.get(ChuyenDe, cd_id)
    if cd is None:
        raise ValueError("Không tìm thấy chuyên đề")
    ten_moi = du_lieu.get("ten")
    doi_ten = ten_moi and ten_moi != cd.ten
    if doi_ten:
        trung = db.query(ChuyenDe).filter(
            ChuyenDe.ten == ten_moi, ChuyenDe.nguoi_tao_id == cd.nguoi_tao_id
        ).first()
        if trung:
            raise ValueError(f"Chuyên đề '{ten_moi}' đã tồn tại")
    for k, v in du_lieu.items():
        if v is not None:
            setattr(cd, k, v)
    if doi_ten:
        # Cascade: đồng bộ tên denormalized trên tất cả câu hỏi thuộc chuyên đề này.
        db.execute(
            text("UPDATE problems SET chuyen_de = :ten WHERE dang_id IN "
                 "(SELECT id FROM dang WHERE chuyen_de_id = :cd_id)"),
            {"ten": ten_moi, "cd_id": cd_id},
        )
    db.commit()
    db.refresh(cd)
    return cd


def xoa_chuyen_de(db: Session, cd_id: int) -> None:
    cd = db.get(ChuyenDe, cd_id)
    if cd is None:
        raise ValueError("Không tìm thấy chuyên đề")
    if db.query(Dang).filter(Dang.chuyen_de_id == cd_id).count() > 0:
        raise ValueError("Chuyên đề còn dạng, hãy xóa hết dạng trước")
    db.delete(cd)
    db.commit()


# ---------- Dang ----------

def lay_dang_theo_chuyen_de(db: Session, cd_id: int) -> list[Dang]:
    return db.query(Dang).filter(Dang.chuyen_de_id == cd_id).order_by(Dang.thu_tu, Dang.id).all()


def tao_dang(db: Session, chuyen_de_id: int, ten: str, mo_ta: str | None, thu_tu: int, nguoi_tao_id: int) -> Dang:
    cd = db.get(ChuyenDe, chuyen_de_id)
    if cd is None:
        raise ValueError("Không tìm thấy chuyên đề")
    if db.query(Dang).filter(Dang.chuyen_de_id == chuyen_de_id, Dang.ten == ten).first():
        raise ValueError(f"Dạng '{ten}' đã tồn tại trong chuyên đề này")
    dang = Dang(chuyen_de_id=chuyen_de_id, ten=ten, mo_ta=mo_ta, thu_tu=thu_tu, nguoi_tao_id=nguoi_tao_id)
    db.add(dang)
    db.commit()
    db.refresh(dang)
    return dang


def sua_dang(db: Session, dang_id: int, du_lieu: dict) -> Dang:
    dang = db.get(Dang, dang_id)
    if dang is None:
        raise ValueError("Không tìm thấy dạng")
    for k, v in du_lieu.items():
        if v is not None:
            setattr(dang, k, v)
    db.commit()
    db.refresh(dang)
    return dang


def xoa_dang(db: Session, dang_id: int) -> None:
    dang = db.get(Dang, dang_id)
    if dang is None:
        raise ValueError("Không tìm thấy dạng")
    if db.query(Problem).filter(Problem.dang_id == dang_id).count() > 0:
        raise ValueError("Dạng còn câu hỏi, hãy gỡ câu hỏi khỏi dạng trước")
    db.delete(dang)
    db.commit()


def lay_toan_bo_danh_muc(db: Session, owner_id: int | None = None) -> list[dict]:
    """Trả cây chuyên đề → dạng. owner_id=None → tất cả (admin/Quản lý xem tổng)."""
    cds = lay_tat_ca_chuyen_de(db, owner_id)
    result = []
    for cd in cds:
        result.append({
            "id": cd.id,
            "ten": cd.ten,
            "mo_ta": cd.mo_ta,
            "thu_tu": cd.thu_tu,
            "nguoi_tao_id": cd.nguoi_tao_id,
            "dang_list": [
                {
                    "id": d.id,
                    "ten": d.ten,
                    "mo_ta": d.mo_ta,
                    "thu_tu": d.thu_tu,
                    "so_cau": db.query(Problem).filter(Problem.dang_id == d.id).count(),
                }
                for d in cd.dang_list
            ],
        })
    return result
