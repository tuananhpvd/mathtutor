"""API giám sát: gắn cờ thủ công, xem danh sách cờ, xem lịch sử turn.

Phân quyền: GV CHỈ thấy dữ liệu học sinh lớp mình (nguyên tắc bất biến #6, CLAUDE.md
mục 3) — Admin/tài khoản Quản lý (`co_toan_quyen`) thấy toàn hệ thống. Mọi endpoint ở
đây thao tác trên dữ liệu của HS (cờ/turn/phiên) nên PHẢI kiểm quyền qua session/HS,
không chỉ kiểm vai trò GV chung chung.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.deps import CurrentUser, co_toan_quyen, require_role
from app.db.session import get_db
from app.models.flag import Flag, LoaiCo, TrangThaiCo
from app.models.session import Session as SessionModel
from app.models.turn import Turn
from app.models.user import VaiTro
from app.services.progress_service import hoc_sinh_thuoc_gv, hs_ids_cua_gv

router = APIRouter(prefix="/api/monitor", tags=["monitor"])


def _kiem_tra_quyen_session(db: Session, current_user, session: SessionModel | None) -> None:
    """403 nếu GV (không phải Admin/Quản lý) không sở hữu học sinh của phiên này."""
    if session is None:
        return
    if co_toan_quyen(current_user):
        return
    if not hoc_sinh_thuoc_gv(db, current_user.id, session.hoc_sinh_id):
        raise HTTPException(status_code=403, detail="Không có quyền xem học sinh này")


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
        except ValueError as e:
            raise HTTPException(status_code=400, detail="Trạng thái không hợp lệ") from e

    # GV chỉ thấy cờ của học sinh lớp mình — lọc TRƯỚC limit để không bị cờ của GV
    # khác chiếm hết 100 dòng đầu.
    if not co_toan_quyen(current_user):
        hs_ids = hs_ids_cua_gv(db, current_user.id)
        if not hs_ids:
            return []
        session_ids = [
            s.id for s in db.query(SessionModel.id)
            .filter(SessionModel.hoc_sinh_id.in_(hs_ids)).all()
        ]
        if not session_ids:
            return []
        q = q.filter(Flag.session_id.in_(session_ids))

    flags = q.order_by(Flag.tao_luc.desc()).limit(100).all()

    # Bổ sung tên HS + bài để GV biết gắn cờ cho ai / phần nào (A4).
    from app.models.problem import Problem
    from app.models.user import User

    s_ids = {f.session_id for f in flags if f.session_id}
    sessions = (
        {s.id: s for s in db.query(SessionModel).filter(SessionModel.id.in_(s_ids)).all()}
        if s_ids else {}
    )
    hs_ids_hien = {s.hoc_sinh_id for s in sessions.values()}
    p_ids = {s.problem_id for s in sessions.values()}
    hs_ten = (
        {u.id: u.ho_ten for u in db.query(User).filter(User.id.in_(hs_ids_hien)).all()}
        if hs_ids_hien else {}
    )
    problems = (
        {p.id: p for p in db.query(Problem).filter(Problem.id.in_(p_ids)).all()}
        if p_ids else {}
    )

    out = []
    for f in flags:
        s = sessions.get(f.session_id)
        p = problems.get(s.problem_id) if s else None
        out.append({
            "id": f.id,
            "session_id": f.session_id,
            "turn_id": f.turn_id,
            "loai_co": f.loai_co.value,
            "trang_thai": f.trang_thai.value,
            "ghi_chu": f.ghi_chu,
            "tao_luc": f.tao_luc.isoformat(),
            "hoc_sinh_ten": hs_ten.get(s.hoc_sinh_id) if s else None,
            "chuyen_de": p.chuyen_de if p else None,
            "dang_ten": (p.dang.ten if p and p.dang else None),
        })
    return out


@router.post("/flags", dependencies=[require_role(VaiTro.gv, VaiTro.admin)])
def gan_co_thu_cong(
    session_id: int,
    current_user: CurrentUser,
    ghi_chu: str = "",
    db: Session = Depends(get_db),
):
    session = db.get(SessionModel, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Phiên không tồn tại")
    _kiem_tra_quyen_session(db, current_user, session)

    flag = Flag(
        session_id=session_id,
        loai_co=LoaiCo.thu_cong,
        ghi_chu=ghi_chu,
        xu_ly_boi=current_user.dang_nhap,
    )
    db.add(flag)
    db.commit()
    db.refresh(flag)
    return {"id": flag.id, "loai_co": flag.loai_co.value, "trang_thai": flag.trang_thai.value}


@router.patch("/flags/{flag_id}", dependencies=[require_role(VaiTro.gv, VaiTro.admin)])
def cap_nhat_co(
    flag_id: int,
    trang_thai: str,
    current_user: CurrentUser,
    loi_nhan: str = "",
    db: Session = Depends(get_db),
):
    flag = db.get(Flag, flag_id)
    if flag is None:
        raise HTTPException(status_code=404, detail="Cờ không tồn tại")
    session = db.get(SessionModel, flag.session_id) if flag.session_id else None
    _kiem_tra_quyen_session(db, current_user, session)

    try:
        flag.trang_thai = TrangThaiCo(trang_thai)
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Trạng thái không hợp lệ") from e
    flag.xu_ly_boi = current_user.dang_nhap
    db.commit()

    # Khép vòng: GV để lại lời nhắn → báo cho HS (A4).
    loi_nhan = (loi_nhan or "").strip()
    if loi_nhan and session is not None:
        from app.models.thong_bao import LoaiThongBao
        from app.services import thong_bao_service

        thong_bao_service.tao(
            db, nguoi_nhan_id=session.hoc_sinh_id, noi_dung=loi_nhan,
            loai=LoaiThongBao.co, nguoi_gui_id=current_user.id,
            tieu_de="Lời nhắn từ thầy/cô",
            lien_ket_loai="session", lien_ket_id=session.id,
        )
    return {"id": flag.id, "trang_thai": flag.trang_thai.value}


@router.get("/sessions/{session_id}/turns", dependencies=[require_role(VaiTro.gv, VaiTro.admin)])
def xem_lich_su_turn(session_id: int, current_user: CurrentUser, db: Session = Depends(get_db)):
    session = db.get(SessionModel, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy turn")
    _kiem_tra_quyen_session(db, current_user, session)

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
    """Nhật ký các phiên đã hoàn thành (kèm thời gian làm bài) cho GV/Admin theo dõi.

    GV chỉ thấy phiên của học sinh lớp mình; Admin/Quản lý thấy toàn hệ thống."""
    from app.models.problem import Problem
    from app.models.session import TrangThaiSession
    from app.models.user import User

    q = db.query(SessionModel).filter(SessionModel.trang_thai == TrangThaiSession.hoan_thanh)
    if not co_toan_quyen(current_user):
        hs_ids = hs_ids_cua_gv(db, current_user.id)
        if not hs_ids:
            return []
        q = q.filter(SessionModel.hoc_sinh_id.in_(hs_ids))

    rows = q.order_by(SessionModel.cap_nhat_luc.desc()).limit(100).all()
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
