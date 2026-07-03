
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text as sql_text
from sqlalchemy.orm import Session

from app.auth.deps import CurrentUser, co_toan_quyen, require_role
from app.db.session import get_db
from app.models.lop import Lop
from app.models.problem import Problem, TrangThaiDuyet
from app.models.thong_bao import LoaiThongBao
from app.models.user import User, VaiTro
from app.schemas.problem import ImportBatchRequest, ProblemCreate, ProblemUpdate
from app.services import thong_bao_service
from app.services.problem_service import (
    anh_huong_xoa_vinh_vien,
    import_batch,
    khoi_phuc_problem,
    sua_problem,
    tao_problem,
    xoa_problem,
    xoa_vinh_vien_problem,
)

router = APIRouter(prefix="/api/problems", tags=["problems"])


def _gv_id_cua_lop_hs(db: Session, hs: User) -> int | None:
    """GV chủ nhiệm lớp của HS — nguồn bài cho HS tự luyện."""
    if hs.lop_id is None:
        return None
    lop = db.get(Lop, hs.lop_id)
    return lop.gv_id if lop else None


def _bao_quan_ly(db: Session, actor: User, owner_id: int | None, hanh_dong: str, mo_ta: str) -> None:
    """Quản lý sửa/xóa nội dung của GV khác → gửi thông báo cho chủ sở hữu."""
    if owner_id is None or owner_id == actor.id:
        return
    if actor.vai_tro != VaiTro.admin and not actor.la_quan_ly:
        return
    thong_bao_service.tao(
        db,
        nguoi_nhan_id=owner_id,
        noi_dung=f"{actor.ho_ten} {hanh_dong}: {mo_ta}",
        loai=LoaiThongBao.quan_ly,
        nguoi_gui_id=actor.id,
        tieu_de="Quản lý cập nhật nội dung",
    )


def _quyen_tren_bai(current_user: User, p: Problem) -> bool:
    """Được thao tác nếu là chủ bài hoặc có toàn quyền (admin/Quản lý)."""
    return co_toan_quyen(current_user) or p.nguoi_tao_id == current_user.id


def _lay_dang_cd_map(db: Session) -> dict[int, str]:
    """Lookup dict: dang_id → tên chuyên đề LIVE từ DB (raw SQL, không qua ORM cache)."""
    rows = db.execute(sql_text(
        "SELECT d.id, cd.ten FROM dang d JOIN chuyen_de cd ON cd.id = d.chuyen_de_id"
    )).fetchall()
    return {r[0]: r[1] for r in rows}


def _chuyen_de_ten(p: Problem, dang_cd: dict[int, str]) -> str:
    """Trả tên chuyên đề LIVE. Fallback về cột text nếu dang_id không có trong map."""
    if p.dang_id and p.dang_id in dang_cd:
        return dang_cd[p.dang_id]
    return p.chuyen_de


def _steps_full(p: Problem) -> list[dict]:
    return [
        {
            "thu_tu": s.thu_tu,
            "pham_vi": s.pham_vi,
            "mo_ta": s.mo_ta,
            "bieu_thuc_ket_qua": s.bieu_thuc_ket_qua,
            "danh_sach_goi_y": s.danh_sach_goi_y,
        }
        for s in p.solution_steps
    ]


def _problem_full(p: Problem, dang_cd: dict[int, str]) -> dict:
    """Dữ liệu đầy đủ cho GV xem & sửa (gồm đáp án + các bước)."""
    return {
        "id": p.id,
        "chuyen_de": _chuyen_de_ten(p, dang_cd),
        "dang_id": p.dang_id,
        "dang_ten": p.dang.ten if p.dang else None,
        "loai_cau": p.loai_cau.value,
        "do_kho": p.do_kho.value,
        "de_bai": p.de_bai,
        "loai_dap_an_nhap": p.loai_dap_an_nhap,
        "che_do_so_khop": p.che_do_so_khop.value,
        "trang_thai_duyet": p.trang_thai_duyet.value,
        "nguoi_tao_id": p.nguoi_tao_id,
        "meta": p.meta,
        "solution_steps": _steps_full(p),
    }


def _meta_cho_gv(p: Problem) -> dict:
    """Meta trong danh sách GV: chỉ phương án/ý để hiển thị, không lộ đáp án đúng."""
    meta = p.meta or {}
    if p.loai_cau.value == "TN4PA":
        return {"phuong_an": meta.get("phuong_an") or {}}
    if p.loai_cau.value == "TNDS":
        return {"y": [{"ky_hieu": y.get("ky_hieu", ""), "noi_dung_y": y.get("noi_dung_y", "")}
                      for y in meta.get("y") or []]}
    return {}


def _strip_answers(p: Problem, dang_cd: dict[int, str]) -> dict:
    """Trả dữ liệu bài cho HS — lọc bỏ mọi trường đáp án."""
    meta_safe: dict = {}
    if p.loai_cau.value == "TN4PA":
        meta_safe = {"phuong_an": p.meta.get("phuong_an", {})}
    elif p.loai_cau.value == "TNDS":
        meta_safe = {
            "y": [{"ky_hieu": y["ky_hieu"], "noi_dung_y": y["noi_dung_y"]}
                  for y in p.meta.get("y", [])]
        }
    # TLN: không trả gì trong meta
    return {
        "id": p.id,
        "chuyen_de": _chuyen_de_ten(p, dang_cd),
        "dang_id": p.dang_id,
        "dang_ten": p.dang.ten if p.dang else None,
        "loai_cau": p.loai_cau.value,
        "do_kho": p.do_kho.value,
        "de_bai": p.de_bai,
        "loai_dap_an_nhap": p.loai_dap_an_nhap,
        "meta": meta_safe,
    }


@router.get("", dependencies=[require_role(VaiTro.hs, VaiTro.gv)])
def danh_sach_bai(
    current_user: CurrentUser, gv_id: int | None = None, db: Session = Depends(get_db)
):
    dang_cd = _lay_dang_cd_map(db)
    q = db.query(Problem)
    if current_user.vai_tro == VaiTro.hs:
        # HS tự luyện: chỉ bài đã duyệt, chưa ẩn, của GV chủ nhiệm lớp mình.
        gv_lop = _gv_id_cua_lop_hs(db, current_user)
        if gv_lop is None:
            return []
        q = q.filter(
            Problem.trang_thai_duyet == TrangThaiDuyet.da_duyet,
            Problem.nguoi_tao_id == gv_lop,
            Problem.bi_an == False,  # noqa: E712
        )
        return [_strip_answers(p, dang_cd) for p in q.all()]

    # GV thường: chỉ bài của mình. Quản lý/Admin: theo gv_id (nếu có), mặc định tất cả.
    if co_toan_quyen(current_user):
        if gv_id is not None:
            q = q.filter(Problem.nguoi_tao_id == gv_id)
    else:
        q = q.filter(Problem.nguoi_tao_id == current_user.id)

    problems = sorted(
        q.all(),
        key=lambda p: (p.tao_luc.isoformat() if p.tao_luc else "", p.id),
        reverse=True,
    )
    return [
        {"id": p.id, "chuyen_de": _chuyen_de_ten(p, dang_cd), "dang_id": p.dang_id,
         "dang_ten": p.dang.ten if p.dang else None,
         "loai_cau": p.loai_cau.value, "do_kho": p.do_kho.value,
         "de_bai": p.de_bai,
         "meta": _meta_cho_gv(p),
         "trang_thai_duyet": p.trang_thai_duyet.value,
         "nguoi_tao_id": p.nguoi_tao_id,
         "la_cua_toi": (p.nguoi_tao_id == current_user.id),
         "nguon": p.nguon.value, "bi_an": p.bi_an,
         "tao_luc": p.tao_luc.isoformat() if p.tao_luc else None}
        for p in problems
    ]


@router.get("/{problem_id}", dependencies=[require_role(VaiTro.hs, VaiTro.gv)])
def chi_tiet_bai(problem_id: int, current_user: CurrentUser, db: Session = Depends(get_db)):
    p = db.get(Problem, problem_id)
    if p is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy bài")
    if current_user.vai_tro == VaiTro.hs:
        if p.trang_thai_duyet != TrangThaiDuyet.da_duyet or p.bi_an:
            raise HTTPException(status_code=404, detail="Không tìm thấy bài")
        # HS được truy cập nếu bài của GV chủ nhiệm lớp mình HOẶC được giao qua nhiệm vụ.
        cho_phep = p.nguoi_tao_id == _gv_id_cua_lop_hs(db, current_user)
        if not cho_phep:
            from app.models.nhiem_vu import NhiemVuBai, NhiemVuHocSinh
            assigned = (
                db.query(NhiemVuBai)
                .join(NhiemVuHocSinh, NhiemVuBai.nhiem_vu_id == NhiemVuHocSinh.nhiem_vu_id)
                .filter(
                    NhiemVuBai.problem_id == problem_id,
                    NhiemVuHocSinh.hoc_sinh_id == current_user.id,
                )
                .first()
            )
            if not assigned:
                raise HTTPException(status_code=404, detail="Không tìm thấy bài")
        dang_cd = _lay_dang_cd_map(db)
        return _strip_answers(p, dang_cd)
    # GV thường chỉ xem bài của mình; Quản lý/Admin xem mọi bài.
    if not _quyen_tren_bai(current_user, p):
        raise HTTPException(status_code=403, detail="Bạn không có quyền xem câu hỏi này")
    dang_cd = _lay_dang_cd_map(db)
    return _problem_full(p, dang_cd)


@router.post("/import-batch", dependencies=[require_role(VaiTro.gv, VaiTro.admin)])
def import_batch_bai(body: ImportBatchRequest, current_user: CurrentUser,
                     db: Session = Depends(get_db)):
    """Import hàng loạt câu hỏi từ file mẫu. Trạng thái: cho_duyet + rieng_tu."""
    return import_batch(db, body.items, current_user.id)


@router.post("", dependencies=[require_role(VaiTro.gv, VaiTro.admin)])
def tao_bai(body: ProblemCreate, current_user: CurrentUser, db: Session = Depends(get_db)):
    du_lieu = body.model_dump()
    try:
        p = tao_problem(db, du_lieu, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _problem_full(p, _lay_dang_cd_map(db))


@router.patch("/{problem_id}", dependencies=[require_role(VaiTro.gv, VaiTro.admin)])
def cap_nhat_bai(problem_id: int, body: ProblemUpdate, current_user: CurrentUser,
                 db: Session = Depends(get_db)):
    p = db.get(Problem, problem_id)
    if p is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy câu hỏi")
    if not _quyen_tren_bai(current_user, p):
        raise HTTPException(status_code=403, detail="Bạn không có quyền sửa câu hỏi này")
    owner_id, ten_bai = p.nguoi_tao_id, p.de_bai
    du_lieu = body.model_dump(exclude_unset=True)
    # solution_steps là list[SolutionStepIn] → chuyển về list[dict]
    if "solution_steps" in du_lieu and du_lieu["solution_steps"] is not None:
        du_lieu["solution_steps"] = [
            s if isinstance(s, dict) else s.model_dump() for s in du_lieu["solution_steps"]
        ]
    try:
        p = sua_problem(db, problem_id, du_lieu)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    _bao_quan_ly(db, current_user, owner_id, "đã sửa câu hỏi", ten_bai)
    return _problem_full(p, _lay_dang_cd_map(db))


@router.delete("/{problem_id}", dependencies=[require_role(VaiTro.gv, VaiTro.admin)])
def xoa_bai(problem_id: int, current_user: CurrentUser, db: Session = Depends(get_db)):
    p = db.get(Problem, problem_id)
    if p is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy câu hỏi")
    if not _quyen_tren_bai(current_user, p):
        raise HTTPException(status_code=403, detail="Bạn không có quyền xóa câu hỏi này")
    owner_id, ten_bai = p.nguoi_tao_id, p.de_bai
    try:
        kq = xoa_problem(db, problem_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    _bao_quan_ly(db, current_user, owner_id, "đã xóa câu hỏi", ten_bai)
    return kq


@router.patch("/{problem_id}/khoi-phuc", dependencies=[require_role(VaiTro.gv, VaiTro.admin)])
def khoi_phuc_bai(problem_id: int, current_user: CurrentUser, db: Session = Depends(get_db)):
    p = db.get(Problem, problem_id)
    if p is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy câu hỏi")
    if not _quyen_tren_bai(current_user, p):
        raise HTTPException(status_code=403, detail="Bạn không có quyền khôi phục câu hỏi này")
    try:
        khoi_phuc_problem(db, problem_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"ok": True}


@router.get("/{problem_id}/anh-huong", dependencies=[require_role(VaiTro.gv, VaiTro.admin)])
def xem_anh_huong(problem_id: int, db: Session = Depends(get_db)):
    try:
        return anh_huong_xoa_vinh_vien(db, problem_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{problem_id}/vinh-vien", dependencies=[require_role(VaiTro.gv, VaiTro.admin)])
def xoa_bai_vinh_vien(problem_id: int, current_user: CurrentUser, db: Session = Depends(get_db)):
    p = db.get(Problem, problem_id)
    if p is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy câu hỏi")
    if not _quyen_tren_bai(current_user, p):
        raise HTTPException(status_code=403, detail="Bạn không có quyền xóa vĩnh viễn câu hỏi này")
    owner_id, ten_bai = p.nguoi_tao_id, p.de_bai
    try:
        kq = xoa_vinh_vien_problem(db, problem_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    _bao_quan_ly(db, current_user, owner_id, "đã xóa vĩnh viễn câu hỏi", ten_bai)
    return kq
