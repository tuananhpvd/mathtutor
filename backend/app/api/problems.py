
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.auth.deps import CurrentUser, require_role
from app.db.session import get_db
from app.models.problem import PhamVi, Problem, TrangThaiDuyet
from app.models.user import VaiTro
from app.schemas.problem import ImportBatchRequest, ProblemCreate, ProblemUpdate
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


def _problem_full(p: Problem) -> dict:
    """Dữ liệu đầy đủ cho GV xem & sửa (gồm đáp án + các bước)."""
    return {
        "id": p.id,
        "chuyen_de": p.chuyen_de,
        "dang_id": p.dang_id,
        "dang_ten": p.dang.ten if p.dang else None,
        "loai_cau": p.loai_cau.value,
        "do_kho": p.do_kho.value,
        "de_bai": p.de_bai,
        "loai_dap_an_nhap": p.loai_dap_an_nhap,
        "che_do_so_khop": p.che_do_so_khop.value,
        "trang_thai_duyet": p.trang_thai_duyet.value,
        "pham_vi": p.pham_vi.value,
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


def _strip_answers(p: Problem) -> dict:
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
        "chuyen_de": p.chuyen_de,
        "dang_id": p.dang_id,
        "dang_ten": p.dang.ten if p.dang else None,
        "loai_cau": p.loai_cau.value,
        "do_kho": p.do_kho.value,
        "de_bai": p.de_bai,
        "loai_dap_an_nhap": p.loai_dap_an_nhap,
        "meta": meta_safe,
    }


@router.get("", dependencies=[require_role(VaiTro.hs, VaiTro.gv)])
def danh_sach_bai(current_user: CurrentUser, db: Session = Depends(get_db)):
    q = db.query(Problem)
    if current_user.vai_tro == VaiTro.hs:
        # HS chỉ thấy bài đã duyệt + kho chung (riêng_tư phải được giao qua nhiệm vụ)
        q = q.filter(
            Problem.trang_thai_duyet == TrangThaiDuyet.da_duyet,
            Problem.pham_vi == PhamVi.chung,
            Problem.bi_an == False,  # noqa: E712
        )
        return [_strip_answers(p) for p in q.all()]

    # GV: bài của mình (mọi pham_vi) + bài kho chung của người khác
    if current_user.vai_tro == VaiTro.gv:
        q = q.filter(
            or_(
                Problem.nguoi_tao_id == current_user.id,
                Problem.pham_vi == PhamVi.chung,
            )
        )

    # Admin: xem tất cả
    problems = sorted(
        q.all(),
        key=lambda p: (p.tao_luc.isoformat() if p.tao_luc else "", p.id),
        reverse=True,
    )
    return [
        {"id": p.id, "chuyen_de": p.chuyen_de, "dang_id": p.dang_id,
         "dang_ten": p.dang.ten if p.dang else None,
         "loai_cau": p.loai_cau.value, "do_kho": p.do_kho.value,
         "de_bai": p.de_bai,
         "meta": _meta_cho_gv(p),
         "trang_thai_duyet": p.trang_thai_duyet.value,
         "pham_vi": p.pham_vi.value,
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
        if (p.trang_thai_duyet != TrangThaiDuyet.da_duyet
                or p.bi_an
                or p.pham_vi == PhamVi.rieng_tu):
            raise HTTPException(status_code=404, detail="Không tìm thấy bài")
        return _strip_answers(p)
    return _problem_full(p)


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
    return _problem_full(p)


@router.patch("/{problem_id}", dependencies=[require_role(VaiTro.gv, VaiTro.admin)])
def cap_nhat_bai(problem_id: int, body: ProblemUpdate, current_user: CurrentUser,
                 db: Session = Depends(get_db)):
    p = db.get(Problem, problem_id)
    if p is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy câu hỏi")
    # Chỉ người tạo hoặc admin mới được sửa
    if current_user.vai_tro != VaiTro.admin and p.nguoi_tao_id != current_user.id:
        raise HTTPException(status_code=403, detail="Bạn không có quyền sửa câu hỏi này")
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
    return _problem_full(p)


@router.delete("/{problem_id}", dependencies=[require_role(VaiTro.gv, VaiTro.admin)])
def xoa_bai(problem_id: int, current_user: CurrentUser, db: Session = Depends(get_db)):
    p = db.get(Problem, problem_id)
    if p is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy câu hỏi")
    if current_user.vai_tro != VaiTro.admin and p.nguoi_tao_id != current_user.id:
        raise HTTPException(status_code=403, detail="Bạn không có quyền xóa câu hỏi này")
    try:
        return xoa_problem(db, problem_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{problem_id}/khoi-phuc", dependencies=[require_role(VaiTro.gv, VaiTro.admin)])
def khoi_phuc_bai(problem_id: int, current_user: CurrentUser, db: Session = Depends(get_db)):
    p = db.get(Problem, problem_id)
    if p is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy câu hỏi")
    if current_user.vai_tro != VaiTro.admin and p.nguoi_tao_id != current_user.id:
        raise HTTPException(status_code=403, detail="Bạn không có quyền khôi phục câu hỏi này")
    try:
        khoi_phuc_problem(db, problem_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"ok": True}


@router.post("/{problem_id}/chia-se", dependencies=[require_role(VaiTro.gv, VaiTro.admin)])
def chia_se_bai(problem_id: int, current_user: CurrentUser, db: Session = Depends(get_db)):
    """Toggle phạm vi câu hỏi: rieng_tu ↔ chung. Chỉ áp dụng cho câu đã duyệt."""
    p = db.get(Problem, problem_id)
    if p is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy câu hỏi")
    if current_user.vai_tro != VaiTro.admin and p.nguoi_tao_id != current_user.id:
        raise HTTPException(status_code=403, detail="Chỉ người tạo mới được thay đổi phạm vi câu hỏi này")
    if p.trang_thai_duyet != TrangThaiDuyet.da_duyet:
        raise HTTPException(status_code=400, detail="Câu hỏi phải được duyệt trước khi thay đổi phạm vi")
    p.pham_vi = PhamVi.rieng_tu if p.pham_vi == PhamVi.chung else PhamVi.chung
    db.commit()
    return {"ok": True, "pham_vi": p.pham_vi.value}


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
    if current_user.vai_tro != VaiTro.admin and p.nguoi_tao_id != current_user.id:
        raise HTTPException(status_code=403, detail="Bạn không có quyền xóa vĩnh viễn câu hỏi này")
    try:
        return xoa_vinh_vien_problem(db, problem_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
