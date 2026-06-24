from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.problems import _strip_answers
from app.auth.deps import CurrentUser, require_role
from app.core.guard.safety import kiem_tra_an_toan
from app.db.session import get_db
from app.llm.client import get_llm_client
from app.models.problem import Problem, TrangThaiDuyet
from app.models.session import Session as SessionModel
from app.models.session import TrangThaiSession
from app.models.turn import Turn
from app.models.user import VaiTro
from app.schemas.session import (
    ChiTietPhienResponse,
    GửiTinRequest,
    PhanHoiResponse,
    PhienDangDoResponse,
    TaoPhienRequest,
    TaoPhienResponse,
    TurnResponse,
)
from app.services.tutor_service import tao_phien, xu_ly_luot

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


def _buoc_info(problem, buoc_so: int) -> tuple[str | None, int | None]:
    """Trả (mo_ta bước hiện tại, tổng số bước) từ solution_steps."""
    steps = problem.solution_steps if problem else []
    tong = len(steps) if steps else None
    mo_ta = next((s.mo_ta for s in steps if s.thu_tu == buoc_so), None)
    return mo_ta, tong


@router.post("", response_model=TaoPhienResponse, dependencies=[require_role(VaiTro.hs)])
def tao_phien_moi(
    body: TaoPhienRequest,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    problem = db.get(Problem, body.problem_id)
    if problem is None or problem.trang_thai_duyet != TrangThaiDuyet.da_duyet:
        raise HTTPException(status_code=404, detail="Bài không tồn tại hoặc chưa được duyệt")

    llm = get_llm_client()
    session, van_ban = tao_phien(db, current_user.id, body.problem_id, llm)
    mo_ta, tong = _buoc_info(problem, session.buoc_hien_tai)
    return TaoPhienResponse(
        session_id=session.id,
        van_ban=van_ban,
        buoc_hien_tai=session.buoc_hien_tai,
        loai_cau=problem.loai_cau.value,
        y_hien_tai=session.y_hien_tai,
        buoc_mo_ta=mo_ta,
        tong_buoc=tong,
    )


@router.get("/dang-do", response_model=list[PhienDangDoResponse],
            dependencies=[require_role(VaiTro.hs)])
def phien_dang_do(current_user: CurrentUser, db: Session = Depends(get_db)):
    """Danh sách phiên HS đang làm dở để 'làm tiếp'."""
    rows = (
        db.query(SessionModel)
        .filter(
            SessionModel.hoc_sinh_id == current_user.id,
            SessionModel.trang_thai == TrangThaiSession.dang_lam,
        )
        .order_by(SessionModel.cap_nhat_luc.desc())
        .all()
    )
    ket_qua = []
    for s in rows:
        p = db.get(Problem, s.problem_id)
        if p is None:
            continue
        ket_qua.append(PhienDangDoResponse(
            session_id=s.id,
            problem_id=s.problem_id,
            loai_cau=p.loai_cau.value,
            chuyen_de=p.chuyen_de,
            de_bai=p.de_bai,
            buoc_hien_tai=s.buoc_hien_tai,
            y_hien_tai=s.y_hien_tai,
            trang_thai_y=s.trang_thai_y,
            cap_goi_y_hien_tai=s.cap_goi_y_hien_tai,
            cap_nhat_luc=s.cap_nhat_luc.isoformat(),
        ))
    return ket_qua


@router.get("/{session_id}", response_model=ChiTietPhienResponse,
            dependencies=[require_role(VaiTro.hs)])
def chi_tiet_phien(session_id: int, current_user: CurrentUser, db: Session = Depends(get_db)):
    """Chi tiết phiên + lịch sử lượt để HS làm tiếp (chỉ phiên của chính mình)."""
    session = db.get(SessionModel, session_id)
    if session is None or session.hoc_sinh_id != current_user.id:
        raise HTTPException(status_code=404, detail="Phiên không tồn tại")
    problem = db.get(Problem, session.problem_id)
    meta_safe = _strip_answers(problem)["meta"] if problem else {}
    turns = db.query(Turn).filter(Turn.session_id == session_id).order_by(Turn.id).all()
    return ChiTietPhienResponse(
        session_id=session.id,
        problem_id=session.problem_id,
        loai_cau=problem.loai_cau.value if problem else "",
        chuyen_de=problem.chuyen_de if problem else "",
        dang_ten=(problem.dang.ten if problem and problem.dang else None),
        de_bai=problem.de_bai if problem else "",
        meta=meta_safe,
        trang_thai=session.trang_thai.value,
        buoc_hien_tai=session.buoc_hien_tai,
        y_hien_tai=session.y_hien_tai,
        trang_thai_y=session.trang_thai_y,
        cap_goi_y_hien_tai=session.cap_goi_y_hien_tai,
        diem=session.diem,
        thoi_gian_giay=session.thoi_gian_giay,
        turns=[
            TurnResponse(
                vai_tro=t.vai_tro.value,
                noi_dung=t.noi_dung,
                dap_an_nhap=t.dap_an_nhap,
                cap_goi_y=t.cap_goi_y,
            )
            for t in turns
        ],
    )


@router.post("/{session_id}/message", response_model=PhanHoiResponse,
             dependencies=[require_role(VaiTro.hs)])
def gui_tin(
    session_id: int,
    body: GửiTinRequest,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    session = db.get(SessionModel, session_id)
    if session is None or session.hoc_sinh_id != current_user.id:
        raise HTTPException(status_code=404, detail="Phiên không tồn tại")
    if session.trang_thai.value == "hoan_thanh":
        raise HTTPException(status_code=400, detail="Phiên đã hoàn thành")

    ks = kiem_tra_an_toan(body.noi_dung)
    if not ks.an_toan:
        raise HTTPException(status_code=400, detail=f"Nội dung không hợp lệ: {ks.ly_do}")

    problem = db.get(Problem, session.problem_id)
    llm = get_llm_client()
    result = xu_ly_luot(
        db, session, problem,
        noi_dung=body.noi_dung,
        dap_an_nhap=body.dap_an_nhap,
        yeu_cau_goi_y=body.yeu_cau_goi_y,
        llm=llm,
    )
    mo_ta, tong = _buoc_info(problem, result["buoc_hien_tai"])
    result["buoc_mo_ta"] = mo_ta
    result["tong_buoc"] = tong
    return PhanHoiResponse(**result)
