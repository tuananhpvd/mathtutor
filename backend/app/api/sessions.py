from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sympy import latex as sympy_latex

from app.api.problems import _chuyen_de_ten, _lay_dang_cd_map, _strip_answers
from app.auth.deps import CurrentUser, require_role
from app.core.guard.safety import kiem_tra_an_toan
from app.core.matching.cas import parse_bieu_thuc_an_toan
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
from app.services.admin_service import lay_cau_hinh
from app.services.llm_quota_service import ap_quota_hoi_thoai
from app.services.tutor_service import tao_phien, xu_ly_luot

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


def _buoc_info(problem, buoc_so: int, y_hien_tai: str | None = None) -> tuple[str | None, int | None]:
    """Trả (mo_ta bước hiện tại, tổng số bước) từ solution_steps.

    TNDS: mỗi ý có 1 bước riêng (pham_vi = ký hiệu ý) → lấy mô tả theo ý đang xét
    để HS biết cần làm gì cho ý hiện tại. Các loại khác lấy theo thứ tự bước.
    """
    steps = problem.solution_steps if problem else []
    tong = len(steps) if steps else None
    if problem and problem.loai_cau.value == "TNDS" and y_hien_tai:
        mo_ta = next((s.mo_ta for s in steps if s.pham_vi == y_hien_tai), None)
    else:
        mo_ta = next((s.mo_ta for s in steps if s.thu_tu == buoc_so), None)
    return mo_ta, tong


def _cho_chon_dap_an(problem, buoc_hien_tai: int) -> bool | None:
    """TN4PA: đã mở khóa cho HS chọn A/B/C/D chưa.

    - Không bắt buộc suy luận → mở ngay.
    - Bắt buộc suy luận → mở sau khi làm đúng tối thiểu 1 bước (buoc_hien_tai > 1).
    Các loại câu khác trả None (không áp dụng).
    """
    if problem is None or problem.loai_cau.value != "TN4PA":
        return None
    bat_buoc = bool((problem.meta or {}).get("bat_buoc_suy_luan", False))
    return (not bat_buoc) or buoc_hien_tai > 1


def _cho_chon_dung_sai(problem, session) -> bool | None:
    """TNDS: đã mở khóa cho HS chốt Đúng/Sai ý hiện tại chưa.

    - Ý hiện tại không bắt buộc suy luận → mở ngay.
    - Bắt buộc suy luận → mở sau khi đã suy luận đúng (session.da_suy_luan).
    """
    if problem is None or problem.loai_cau.value != "TNDS":
        return None
    ky = session.y_hien_tai
    bat_buoc = False
    for y in (problem.meta or {}).get("y", []):
        if y.get("ky_hieu") == ky:
            bat_buoc = bool(y.get("bat_buoc_suy_luan", False))
            break
    return (not bat_buoc) or bool(session.da_suy_luan)


def _dap_an_y_neu_xong(problem, da_xong: bool) -> dict | None:
    """TNDS: đáp án đúng từng ý {a: 'Dung', ...} — CHỈ trả khi phiên đã hoàn thành.

    Giữ nguyên tắc không lộ đáp án lúc HS đang làm; sau khi xong mới dùng để ôn tập.
    """
    if not da_xong or problem is None or problem.loai_cau.value != "TNDS":
        return None
    return {y["ky_hieu"]: y["dap_an"] for y in (problem.meta or {}).get("y", [])}


@router.post("", response_model=TaoPhienResponse, dependencies=[require_role(VaiTro.hs)])
def tao_phien_moi(
    body: TaoPhienRequest,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    problem = db.get(Problem, body.problem_id)
    if problem is None or problem.trang_thai_duyet != TrangThaiDuyet.da_duyet:
        raise HTTPException(status_code=404, detail="Bài không tồn tại hoặc chưa được duyệt")

    cau_hinh = lay_cau_hinh(db)
    llm = ap_quota_hoi_thoai(db, cau_hinh, current_user.id, get_llm_client(cau_hinh))
    session, van_ban = tao_phien(db, current_user.id, body.problem_id, llm)
    mo_ta, tong = _buoc_info(problem, session.buoc_hien_tai, session.y_hien_tai)
    return TaoPhienResponse(
        session_id=session.id,
        van_ban=van_ban,
        buoc_hien_tai=session.buoc_hien_tai,
        loai_cau=problem.loai_cau.value,
        y_hien_tai=session.y_hien_tai,
        buoc_mo_ta=mo_ta,
        tong_buoc=tong,
        cho_chon_dap_an=_cho_chon_dap_an(problem, session.buoc_hien_tai),
        cho_chon_dung_sai=_cho_chon_dung_sai(problem, session),
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
            SessionModel.bi_an == False,  # noqa: E712
        )
        .order_by(SessionModel.cap_nhat_luc.desc())
        .all()
    )
    dang_cd = _lay_dang_cd_map(db)
    ket_qua = []
    for s in rows:
        p = db.get(Problem, s.problem_id)
        if p is None:
            continue
        ket_qua.append(PhienDangDoResponse(
            session_id=s.id,
            problem_id=s.problem_id,
            loai_cau=p.loai_cau.value,
            chuyen_de=_chuyen_de_ten(p, dang_cd),
            dang_ten=(p.dang.ten if p.dang else None),
            de_bai=p.de_bai,
            buoc_hien_tai=s.buoc_hien_tai,
            y_hien_tai=s.y_hien_tai,
            trang_thai_y=s.trang_thai_y,
            cap_goi_y_hien_tai=s.cap_goi_y_hien_tai,
            cap_nhat_luc=s.cap_nhat_luc.isoformat(),
        ))
    return ket_qua


@router.get("/cua-toi", dependencies=[require_role(VaiTro.hs)])
def phien_cua_toi(current_user: CurrentUser, db: Session = Depends(get_db)):
    """Trạng thái phiên gần nhất của HS theo từng bài (để trang chọn bài hiển thị nút).

    Trả [{problem_id, session_id, trang_thai}] — mỗi bài lấy phiên cập nhật gần nhất.
    """
    rows = (
        db.query(SessionModel)
        .filter(SessionModel.hoc_sinh_id == current_user.id, SessionModel.bi_an == False)  # noqa: E712
        .order_by(SessionModel.cap_nhat_luc.desc())
        .all()
    )
    theo_bai: dict[int, dict] = {}
    for s in rows:
        if s.problem_id not in theo_bai:  # phần tử đầu = mới nhất (do sắp xếp desc)
            theo_bai[s.problem_id] = {
                "problem_id": s.problem_id,
                "session_id": s.id,
                "trang_thai": s.trang_thai.value,
            }
    return list(theo_bai.values())


@router.get("/{session_id}", response_model=ChiTietPhienResponse,
            dependencies=[require_role(VaiTro.hs)])
def chi_tiet_phien(session_id: int, current_user: CurrentUser, db: Session = Depends(get_db)):
    """Chi tiết phiên + lịch sử lượt để HS làm tiếp (chỉ phiên của chính mình)."""
    session = db.get(SessionModel, session_id)
    if session is None or session.hoc_sinh_id != current_user.id:
        raise HTTPException(status_code=404, detail="Phiên không tồn tại")
    problem = db.get(Problem, session.problem_id)
    dang_cd = _lay_dang_cd_map(db)
    meta_safe = _strip_answers(problem, dang_cd)["meta"] if problem else {}
    turns = db.query(Turn).filter(Turn.session_id == session_id).order_by(Turn.id).all()
    return ChiTietPhienResponse(
        session_id=session.id,
        problem_id=session.problem_id,
        loai_cau=problem.loai_cau.value if problem else "",
        chuyen_de=_chuyen_de_ten(problem, dang_cd) if problem else "",
        dang_ten=(problem.dang.ten if problem and problem.dang else None),
        de_bai=problem.de_bai if problem else "",
        hinh_anh=problem.hinh_anh if problem else None,
        meta=meta_safe,
        trang_thai=session.trang_thai.value,
        buoc_hien_tai=session.buoc_hien_tai,
        y_hien_tai=session.y_hien_tai,
        trang_thai_y=session.trang_thai_y,
        cap_goi_y_hien_tai=session.cap_goi_y_hien_tai,
        diem=session.diem,
        thoi_gian_giay=session.thoi_gian_giay,
        buoc_mo_ta=_buoc_info(problem, session.buoc_hien_tai, session.y_hien_tai)[0],
        tong_buoc=_buoc_info(problem, session.buoc_hien_tai, session.y_hien_tai)[1],
        cho_chon_dap_an=_cho_chon_dap_an(problem, session.buoc_hien_tai),
        cho_chon_dung_sai=_cho_chon_dung_sai(problem, session),
        thoi_gian_y=session.thoi_gian_y,
        dap_an_y=_dap_an_y_neu_xong(problem, session.trang_thai.value == "hoan_thanh"),
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


def _bieu_thuc_latex(expr_str: str) -> str:
    """Chuyển bieu_thuc_ket_qua (cú pháp SymPy nội bộ, dùng để CAS đối chiếu — vd
    "3*x**2-3") sang LaTeX để hiển thị đẹp ở trang Xem lại bài (vd "3x^{2}-3"). Không
    parse được (rỗng, hoặc dữ liệu bất thường) → giữ nguyên chuỗi gốc, không để hỏng
    cả trang vì 1 biểu thức lỗi."""
    if not expr_str:
        return expr_str
    try:
        return sympy_latex(parse_bieu_thuc_an_toan(expr_str))
    except Exception:
        return expr_str


@router.get("/{session_id}/xem-lai",
            dependencies=[require_role(VaiTro.hs, VaiTro.gv, VaiTro.admin)])
def xem_lai_phien(session_id: int, current_user: CurrentUser, db: Session = Depends(get_db)):
    """Xem lại bài SAU KHI HOÀN THÀNH: lời giải chuẩn + hành trình hội thoại + thống kê.

    Nguyên tắc "không lộ đáp án" chỉ áp dụng LÚC ĐANG HỌC — sau khi hoàn thành, đối chiếu
    với lời giải chuẩn chính là lúc học sâu nhất. Chốt chặn tại backend: phiên chưa
    hoàn thành → 403 (không phụ thuộc việc frontend ẩn nút).
    """
    from app.services.progress_service import hoc_sinh_thuoc_gv

    session = db.get(SessionModel, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Phiên không tồn tại")
    if current_user.vai_tro == VaiTro.hs and session.hoc_sinh_id != current_user.id:
        raise HTTPException(status_code=404, detail="Phiên không tồn tại")
    if current_user.vai_tro == VaiTro.gv and not hoc_sinh_thuoc_gv(
        db, current_user.id, session.hoc_sinh_id
    ):
        raise HTTPException(status_code=403, detail="Không có quyền xem học sinh này")
    if session.trang_thai != TrangThaiSession.hoan_thanh:
        raise HTTPException(
            status_code=403,
            detail="Chỉ xem lại được bài đã hoàn thành. Em hãy hoàn thành bài trước nhé.",
        )

    problem = db.get(Problem, session.problem_id)
    if problem is None:
        raise HTTPException(status_code=404, detail="Bài không còn tồn tại")
    dang_cd = _lay_dang_cd_map(db)
    meta = problem.meta or {}

    # Đáp án chuẩn theo loại câu — CHỈ tới được đây khi phiên đã hoàn thành.
    if problem.loai_cau.value == "TN4PA":
        dap_an = {"dap_an_dung": meta.get("dap_an_dung")}
    elif problem.loai_cau.value == "TNDS":
        dap_an = {"dap_an_y": {y["ky_hieu"]: y["dap_an"] for y in meta.get("y", [])}}
    else:  # TLN
        dap_an = {"dap_an_cuoi": str(meta.get("dap_an_cuoi", "")),
                  "don_vi": meta.get("don_vi")}

    steps = sorted(problem.solution_steps, key=lambda s: s.thu_tu)
    turns = db.query(Turn).filter(Turn.session_id == session_id).order_by(Turn.id).all()
    cap_goi_y_max = max((t.cap_goi_y for t in turns), default=0)

    return {
        "session_id": session.id,
        "problem": _strip_answers(problem, dang_cd),
        "dap_an": dap_an,
        "loi_giai": [
            {"thu_tu": s.thu_tu, "pham_vi": s.pham_vi, "mo_ta": s.mo_ta,
             "bieu_thuc_ket_qua": _bieu_thuc_latex(s.bieu_thuc_ket_qua)}
            for s in steps
        ],
        "hanh_trinh": [
            {"vai_tro": t.vai_tro.value, "noi_dung": t.noi_dung,
             "dap_an_nhap": t.dap_an_nhap, "cap_goi_y": t.cap_goi_y,
             "thoi_diem": t.thoi_diem.isoformat() if t.thoi_diem else None}
            for t in turns
        ],
        "thong_ke": {
            "diem": session.diem,
            "cap_goi_y_max": cap_goi_y_max,
            "so_lan_khong_hieu": session.so_lan_khong_hieu,
            "so_luot_hs": sum(1 for t in turns if t.vai_tro.value == "hoc_sinh"),
            "thoi_gian_hoat_dong_giay": session.thoi_gian_hoat_dong_giay,
            "thoi_gian_y": session.thoi_gian_y,
        },
        # Chỉ trả khi GV đã bật hiển thị — KHÔNG đưa vào _strip_answers() vì hàm đó còn
        # dùng chung cho lúc ĐANG học (nơi tuyệt đối không được lộ lời giải).
        "loi_giai_chi_tiet": problem.loi_giai_chi_tiet if problem.hien_loi_giai_chi_tiet else None,
    }


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
    cau_hinh = lay_cau_hinh(db)
    llm = ap_quota_hoi_thoai(db, cau_hinh, current_user.id, get_llm_client(cau_hinh))
    result = xu_ly_luot(
        db, session, problem,
        noi_dung=body.noi_dung,
        dap_an_nhap=body.dap_an_nhap,
        yeu_cau_goi_y=body.yeu_cau_goi_y,
        llm=llm,
    )
    mo_ta, tong = _buoc_info(problem, result["buoc_hien_tai"], result.get("y_hien_tai"))
    result["buoc_mo_ta"] = mo_ta
    result["tong_buoc"] = tong
    result["cho_chon_dap_an"] = _cho_chon_dap_an(problem, result["buoc_hien_tai"])
    result["cho_chon_dung_sai"] = _cho_chon_dung_sai(problem, session)
    result["thoi_gian_y"] = session.thoi_gian_y
    result["dap_an_y"] = _dap_an_y_neu_xong(problem, result.get("da_xong", False))
    return PhanHoiResponse(**result)
