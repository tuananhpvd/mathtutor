"""API giám sát: gắn cờ thủ công, xem danh sách cờ, xem lịch sử turn."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.deps import CurrentUser, require_role
from app.db.session import get_db
from app.models.flag import Flag, LoaiCo, TrangThaiCo
from app.models.turn import Turn
from app.models.user import VaiTro

router = APIRouter(prefix="/api/monitor", tags=["monitor"])


@router.get("/flags", dependencies=[require_role(VaiTro.gv, VaiTro.admin)])
def danh_sach_co(
    current_user: CurrentUser,
    trang_thai: str | None = None,
    db: Session = Depends(get_db),
):
    q = db.query(Flag)
    if trang_thai:
        try:
            q = q.filter(Flag.trang_thai == TrangThaiCo(trang_thai))
        except ValueError:
            raise HTTPException(status_code=400, detail="Trạng thái không hợp lệ")
    flags = q.order_by(Flag.tao_luc.desc()).limit(100).all()
    return [
        {
            "id": f.id,
            "session_id": f.session_id,
            "turn_id": f.turn_id,
            "loai_co": f.loai_co.value,
            "trang_thai": f.trang_thai.value,
            "ghi_chu": f.ghi_chu,
            "tao_luc": f.tao_luc.isoformat(),
        }
        for f in flags
    ]


@router.post("/flags", dependencies=[require_role(VaiTro.gv, VaiTro.admin)])
def gan_co_thu_cong(
    session_id: int,
    ghi_chu: str = "",
    current_user: CurrentUser = None,
    db: Session = Depends(get_db),
):
    flag = Flag(
        session_id=session_id,
        loai_co=LoaiCo.thu_cong,
        ghi_chu=ghi_chu,
        xu_ly_boi=current_user.email if current_user else None,
    )
    db.add(flag)
    db.commit()
    db.refresh(flag)
    return {"id": flag.id, "loai_co": flag.loai_co.value, "trang_thai": flag.trang_thai.value}


@router.patch("/flags/{flag_id}", dependencies=[require_role(VaiTro.gv, VaiTro.admin)])
def cap_nhat_co(
    flag_id: int,
    trang_thai: str,
    db: Session = Depends(get_db),
):
    flag = db.get(Flag, flag_id)
    if flag is None:
        raise HTTPException(status_code=404, detail="Cờ không tồn tại")
    try:
        flag.trang_thai = TrangThaiCo(trang_thai)
    except ValueError:
        raise HTTPException(status_code=400, detail="Trạng thái không hợp lệ")
    db.commit()
    return {"id": flag.id, "trang_thai": flag.trang_thai.value}


@router.get("/sessions/{session_id}/turns", dependencies=[require_role(VaiTro.gv, VaiTro.admin)])
def xem_lich_su_turn(session_id: int, db: Session = Depends(get_db)):
    turns = db.query(Turn).filter(Turn.session_id == session_id).order_by(Turn.id).all()
    if not turns:
        raise HTTPException(status_code=404, detail="Không tìm thấy turn")
    return [
        {
            "id": t.id,
            "vai_tro": t.vai_tro.value,
            "noi_dung": t.noi_dung,
            "dap_an_nhap": t.dap_an_nhap,
            "cap_goi_y": t.cap_goi_y,
            "co_bi_chot_chan": t.co_bi_chot_chan,
            "ket_qua_so_khop": t.ket_qua_so_khop,
        }
        for t in turns
    ]


@router.get("/sessions-hoan-thanh", dependencies=[require_role(VaiTro.gv, VaiTro.admin)])
def nhat_ky_hoan_thanh(current_user: CurrentUser, db: Session = Depends(get_db)):
    """Nhật ký các phiên đã hoàn thành (kèm thời gian làm bài) cho GV/Admin theo dõi."""
    from app.models.problem import Problem
    from app.models.session import Session as SessionModel
    from app.models.session import TrangThaiSession
    from app.models.user import User

    rows = (
        db.query(SessionModel)
        .filter(SessionModel.trang_thai == TrangThaiSession.hoan_thanh)
        .order_by(SessionModel.cap_nhat_luc.desc())
        .limit(100)
        .all()
    )
    ket_qua = []
    for s in rows:
        hs = db.get(User, s.hoc_sinh_id)
        p = db.get(Problem, s.problem_id)
        ket_qua.append({
            "session_id": s.id,
            "ho_ten": hs.ho_ten if hs else "?",
            "chuyen_de": p.chuyen_de if p else "?",
            "loai_cau": p.loai_cau.value if p else "?",
            "diem": s.diem,
            "thoi_gian_giay": s.thoi_gian_giay,
            "hoan_thanh_luc": s.cap_nhat_luc.isoformat(),
        })
    return ket_qua
