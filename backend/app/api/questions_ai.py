"""API AI sinh câu hỏi + GV duyệt (Phase 5)."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.deps import CurrentUser, require_role
from app.db.session import get_db
from app.llm.client import get_llm_client
from app.models.problem import Nguon, Problem, TrangThaiDuyet
from app.models.user import VaiTro
from app.schemas.question_gen import CauHoiNhapResponse, DuyetRequest, SinhCauHoiRequest
from app.services.admin_service import lay_cau_hinh
from app.services.question_gen_service import duyet_cau, sinh_va_luu

router = APIRouter(prefix="/api/questions-ai", tags=["questions-ai"])


@router.post("/generate", response_model=list[CauHoiNhapResponse],
             dependencies=[require_role(VaiTro.gv, VaiTro.admin)])
def sinh_cau_hoi(
    body: SinhCauHoiRequest,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    if body.loai_cau not in {"TN4PA", "TNDS", "TLN"}:
        raise HTTPException(status_code=400, detail="loai_cau không hợp lệ")
    llm = get_llm_client(lay_cau_hinh(db))
    try:
        ket_qua = sinh_va_luu(db, body.model_dump(), current_user.id, llm)
    except Exception as e:  # KHÔNG để lộ 500 — báo lỗi rõ ràng để GV thử lại
        db.rollback()
        raise HTTPException(
            status_code=502,
            detail="Không sinh được câu hỏi (mô hình AI lỗi hoặc trả dữ liệu không hợp lệ). "
                   "Vui lòng thử lại sau giây lát. Chi tiết: " + str(e)[:200],
        )
    if not ket_qua:
        raise HTTPException(
            status_code=502,
            detail="Mô hình AI không tạo được câu hỏi hợp lệ. Vui lòng thử lại "
                   "hoặc đổi nhà cung cấp/model trong Cấu hình.",
        )
    return ket_qua


@router.get("/cho-duyet", dependencies=[require_role(VaiTro.gv, VaiTro.admin)])
def danh_sach_cho_duyet(current_user: CurrentUser, db: Session = Depends(get_db)):
    q = db.query(Problem).filter(
        Problem.nguon == Nguon.ai_sinh,
        Problem.trang_thai_duyet == TrangThaiDuyet.cho_duyet,
    )
    return [
        {"id": p.id, "loai_cau": p.loai_cau.value, "do_kho": p.do_kho.value,
         "chuyen_de": p.chuyen_de, "dang_ten": (p.dang.ten if p.dang else None),
         "de_bai": p.de_bai, "meta": p.meta or {}}
        for p in q.all()
    ]


@router.post("/{problem_id}/duyet", dependencies=[require_role(VaiTro.gv, VaiTro.admin)])
def duyet(
    problem_id: int,
    body: DuyetRequest,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    try:
        problem = duyet_cau(db, problem_id, body.hanh_dong)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"id": problem.id, "trang_thai_duyet": problem.trang_thai_duyet.value}
