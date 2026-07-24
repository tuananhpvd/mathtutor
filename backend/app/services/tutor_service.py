"""
TutorService: ghép matching → orchestrator (3 loại) → LLM diễn đạt.
Chưa có guard (Phase 4).
"""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.guard.leak import MucDoRoRi, kiem_tra_ro_ri
from app.core.matching.cas import KetQuaSoKhop
from app.core.matching.matcher import so_khop, so_khop_tnds_mot_y
from app.core.matching.scoring import diem_bac_thang
from app.core.orchestrator.rules import xu_ly_tln, xu_ly_tn4pa, xu_ly_tnds
from app.core.orchestrator.state import TrangThaiPhien
from app.llm.client import LLMClient
from app.models.problem import Problem
from app.models.session import Session as SessionModel
from app.models.session import TrangThaiSession
from app.models.turn import Turn, VaiTroTurn
from app.services.progress_service import cap_nhat_tien_do


def _nguong_nghi_giay(db: Session) -> int:
    """Ngưỡng nghỉ (giây) từ cấu hình admin; lỗi → mặc định 180s."""
    try:
        from app.services.admin_service import lay_cau_hinh
        return int(lay_cau_hinh(db).get("nguong_nghi_giay", 180))
    except Exception:
        return 180


def _nguong_co_khong_hieu(db: Session) -> int:
    """Số lần 'không hiểu' trong 1 phiên để tự gắn cờ cho GV; lỗi → mặc định 3."""
    try:
        from app.services.admin_service import lay_cau_hinh
        return int(lay_cau_hinh(db).get("nguong_co_khong_hieu", 3))
    except Exception:
        return 3


def _tu_dong_gan_co_khong_hieu(db: Session, session: SessionModel) -> None:
    """Tự gắn cờ 'không hiểu nhiều' khi HS bí vượt ngưỡng. Kích hoạt khi ONE trong hai:
    (a) tổng số lần xin gợi ý/không hiểu ≥ ngưỡng, HOẶC (b) đã cạn SẠCH thang gợi ý ≥ 1 lần
    — lấp lỗ hổng bài Dễ (2 gợi ý) cạn sạch nhưng dưới ngưỡng 3 nên trước đây không báo GV.
    Chỉ gắn MỘT lần cho mỗi phiên (idempotent) để GV không bị spam cờ ở các lượt sau."""
    from app.models.flag import Flag, LoaiCo, TrangThaiCo

    nguong = _nguong_co_khong_hieu(db)
    do_xin_goi_y = nguong > 0 and (session.so_lan_khong_hieu or 0) >= nguong
    do_het_goi_y = (session.so_lan_het_goi_y or 0) >= 1
    if not (do_xin_goi_y or do_het_goi_y):
        return
    da_co = (
        db.query(Flag)
        .filter(Flag.session_id == session.id, Flag.loai_co == LoaiCo.khong_hieu_nhieu)
        .first()
    )
    if da_co is not None:
        return
    if do_het_goi_y:
        ghi_chu = (f"Học sinh đã dùng CẠN thang gợi ý {session.so_lan_het_goi_y} lần "
                   f"(xin gợi ý tổng {session.so_lan_khong_hieu} lần) — nên hỗ trợ thêm.")
    else:
        ghi_chu = (f"Học sinh đã 'không hiểu'/xin gợi ý {session.so_lan_khong_hieu} lần "
                   f"(ngưỡng {nguong}) — nên hỗ trợ thêm.")
    db.add(Flag(
        session_id=session.id,
        loai_co=LoaiCo.khong_hieu_nhieu,
        trang_thai=TrangThaiCo.cho_xu_ly,
        ghi_chu=ghi_chu,
    ))
    _bao_hs_gap_kho(db, session)


def _bao_hs_gap_kho(db: Session, session: SessionModel) -> None:
    """Báo HS (trung tính, minh bạch) rằng đang gặp khó ở phần nào — kèm gợi ý
    'Nhờ thầy/cô'. Tạo trong cùng transaction (không commit lẻ)."""
    from app.models.thong_bao import LoaiThongBao, ThongBao

    p = db.get(Problem, session.problem_id)
    phan = p.chuyen_de if p else "bài tập"
    if p and p.dang:
        phan += f" › {p.dang.ten}"
    vi_tri = ""
    if session.y_hien_tai:
        vi_tri = f" (ý {session.y_hien_tai})"
    elif session.buoc_hien_tai:
        vi_tri = f" (bước {session.buoc_hien_tai})"
    noi_dung = (
        f"Hệ thống nhận thấy em đang gặp khó ở «{phan}»{vi_tri}. "
        f"Thầy/cô đã được báo để hỗ trợ em. Em có thể bấm '🙋 Nhờ thầy/cô' "
        f"ngay trong bài nếu cần giúp đỡ nhé."
    )
    db.add(ThongBao(
        nguoi_nhan_id=session.hoc_sinh_id,
        loai=LoaiThongBao.co,
        tieu_de="Em đang cần hỗ trợ?",
        noi_dung=noi_dung,
        lien_ket_loai="session",
        lien_ket_id=session.id,
    ))


def _gan_co_ro_ri_neu_bi_chot(db: Session, session: SessionModel, turn: Turn, bi_chot: bool) -> None:
    """Gắn cờ 'ro_ri_dap_an' cho ĐÚNG lượt bị chốt chặn — khác 'chot_chan_nhieu' (cờ TỔNG
    HỢP chỉ gắn 1 lần khi vượt ngưỡng nhiều lần). Cờ này cho GV thấy được TỪNG lần cụ thể,
    kèm turn_id để tra lại đúng câu đã bị viết lại trước khi gửi HS."""
    if not bi_chot:
        return
    from app.models.flag import Flag, LoaiCo

    db.flush()  # turn vừa add, cần flush để có turn.id trước khi gắn vào Flag
    db.add(Flag(
        session_id=session.id,
        turn_id=turn.id,
        loai_co=LoaiCo.ro_ri_dap_an,
        ghi_chu="Phản hồi của gia sư AI có dấu hiệu lộ đáp án — đã được viết lại "
                "trước khi gửi học sinh.",
    ))


def _gv_cua_session(db: Session, session: SessionModel) -> int | None:
    from app.models.lop import Lop
    from app.models.user import User

    hs = db.get(User, session.hoc_sinh_id)
    if hs is None or hs.lop_id is None:
        return None
    lop = db.get(Lop, hs.lop_id)
    return lop.gv_id if lop else None


def bao_gv_noi_dung_khong_phu_hop(
    db: Session, session: SessionModel, ly_do: str, *, ngu_canh: str = "", khan_cap: bool = False
) -> None:
    """Gắn cờ 'noi_dung_khong_phu_hop' + báo GV NGAY (khác các cờ khác chỉ nằm chờ trong
    hàng đợi) — nội dung bị lớp lọc an toàn phát hiện có thể liên quan tới an toàn của HS
    (vd từ khoá nhạy cảm), nên không đợi GV tự vào xem 'Cờ theo dõi' mà đẩy thông báo ngay.
    khan_cap=True (dấu hiệu khủng hoảng/tự hại): nâng mức ưu tiên rõ rệt (🆘) để GV phân biệt
    ngay với các cờ "cần chú ý" thông thường (⚠️, vd ngôn từ không phù hợp, ngoài phạm vi).
    Tự commit vì có thể được gọi từ điểm dừng sớm ở API layer (không đi tiếp vào xu_ly_luot).
    """
    from app.models.flag import Flag, LoaiCo
    from app.models.thong_bao import LoaiThongBao

    tien_to = "🆘 KHẨN CẤP" if khan_cap else "Hệ thống phát hiện"
    ghi_chu = f"{tien_to}: {ly_do}"
    if ngu_canh:
        ghi_chu += f" — nội dung: “{ngu_canh[:200]}”"
    flag = Flag(session_id=session.id, loai_co=LoaiCo.noi_dung_khong_phu_hop, ghi_chu=ghi_chu)
    db.add(flag)
    db.flush()  # cần flag.id để thông báo trỏ đúng cờ (không phải chỉ trỏ chung tới session)

    gv_id = _gv_cua_session(db, session)
    if gv_id:
        from app.services import thong_bao_service

        if khan_cap:
            tieu_de = "🆘 Cần quan tâm khẩn cấp"
            noi_dung = (
                f"Hệ thống phát hiện học sinh có dấu hiệu cần được quan tâm ngay ({ly_do}). "
                f"Thầy/cô nên liên hệ trực tiếp với em càng sớm càng tốt."
            )
        else:
            tieu_de = "⚠️ Nội dung cần chú ý"
            noi_dung = (
                f"Hệ thống phát hiện 1 nội dung cần chú ý từ học sinh trong lúc học "
                f"({ly_do}). Thầy/cô xem chi tiết ở mục Cờ theo dõi."
            )
        thong_bao_service.tao(
            db, nguoi_nhan_id=gv_id, noi_dung=noi_dung, loai=LoaiThongBao.co, tieu_de=tieu_de,
            # Trỏ thẳng vào ĐÚNG cờ (không phải session) — bấm vào thông báo mở đúng dòng ở
            # "Cờ theo dõi" để GV xử lý ngay, khỏi phải tự tìm trong danh sách.
            lien_ket_loai="co", lien_ket_id=flag.id,
        )
    db.commit()


# Câu trả lời CỐ ĐỊNH (không qua LLM) khi phát hiện dấu hiệu khủng hoảng/tự hại — tuyệt đối
# không để AI tự ứng biến với chủ đề nhạy cảm này, dù có thể diễn đạt hay hơn nhưng rủi ro
# nói sai/nói hớ là không chấp nhận được.
TIN_NHAN_KHAN_CAP = (
    "Thầy/cô rất quan tâm đến em và đã được báo để hỗ trợ ngay. Nếu em đang thấy quá sức, "
    "hãy nói chuyện với người em tin tưởng (bố mẹ, thầy cô, bạn bè) nhé — em không đơn độc đâu."
)


def xu_ly_noi_dung_khan_cap(
    db: Session, session: SessionModel, ngu_canh: str, ly_do: str
) -> str:
    """HS gửi nội dung có dấu hiệu khủng hoảng/tự hại trong lúc chat với AI — KHÔNG cho AI
    tự do trả lời (tránh AI ứng biến vụng về với chủ đề nhạy cảm). Vẫn ghi lại đúng lời HS
    vào hội thoại (để GV xem lại được ngữ cảnh khi cần), trả một câu ấm áp CỐ ĐỊNH, và gắn cờ
    + báo GV mức ưu tiên cao nhất. Trả về văn bản đã "gửi" HS (để API layer đưa vào response).
    """
    db.add(Turn(session_id=session.id, vai_tro=VaiTroTurn.hoc_sinh, noi_dung=ngu_canh))
    db.add(Turn(session_id=session.id, vai_tro=VaiTroTurn.gia_su, noi_dung=TIN_NHAN_KHAN_CAP))
    bao_gv_noi_dung_khong_phu_hop(db, session, ly_do, ngu_canh=ngu_canh, khan_cap=True)
    return TIN_NHAN_KHAN_CAP


# Câu trả lời CỐ ĐỊNH khi nội dung không phù hợp lứa tuổi (không phải khủng hoảng) — thân
# thiện, KHÔNG lặp lại từ khóa đã khớp (không cần thiết và hơi thô), hướng thẳng về bài học.
TIN_NHAN_KHONG_PHU_HOP = (
    "Nội dung này không phù hợp để mình trao đổi trong giờ học nhé. Chúng ta quay lại bài "
    "toán đang làm thôi em — em thử tiếp tục xem sao!"
)

# Câu trả lời CỐ ĐỊNH khi HS hỏi việc ngoài phạm vi môn Toán (vd nhờ viết code, dịch bài) —
# không phải vấn đề an toàn, chỉ nhắc nhở nhẹ nhàng quay lại đúng trọng tâm.
TIN_NHAN_NGOAI_PHAM_VI = (
    "Câu này nằm ngoài nội dung Toán mình đang học rồi em ơi. Mình tập trung vào bài này "
    "nhé, em thử tiếp tục xem sao!"
)


def xu_ly_noi_dung_khong_phu_hop(
    db: Session, session: SessionModel, ngu_canh: str, ly_do: str
) -> str:
    """HS gửi nội dung không phù hợp lứa tuổi (không phải khủng hoảng) — KHÔNG cho AI tự do
    trả lời, thay bằng câu nhắc nhở thân thiện CỐ ĐỊNH ngay trong khung chat (không phải lỗi
    HTTP kỹ thuật, không lặp lại từ khóa) + vẫn gắn cờ, báo GV như cũ."""
    db.add(Turn(session_id=session.id, vai_tro=VaiTroTurn.hoc_sinh, noi_dung=ngu_canh))
    db.add(Turn(session_id=session.id, vai_tro=VaiTroTurn.gia_su, noi_dung=TIN_NHAN_KHONG_PHU_HOP))
    bao_gv_noi_dung_khong_phu_hop(db, session, ly_do, ngu_canh=ngu_canh)
    return TIN_NHAN_KHONG_PHU_HOP


def xu_ly_ngoai_pham_vi(db: Session, session: SessionModel, ngu_canh: str) -> str:
    """HS hỏi việc ngoài phạm vi môn Toán — không phải vấn đề an toàn nên KHÔNG gắn cờ/báo
    GV, chỉ nhắc nhở thân thiện ngay trong khung chat và hướng về bài học."""
    db.add(Turn(session_id=session.id, vai_tro=VaiTroTurn.hoc_sinh, noi_dung=ngu_canh))
    db.add(Turn(session_id=session.id, vai_tro=VaiTroTurn.gia_su, noi_dung=TIN_NHAN_NGOAI_PHAM_VI))
    db.commit()
    return TIN_NHAN_NGOAI_PHAM_VI


def _nguong_co_chot_chan(db: Session) -> int:
    """Số lần phản hồi bị chốt chặn rò rỉ trong 1 phiên để gắn cờ; lỗi → mặc định 3."""
    try:
        from app.services.admin_service import lay_cau_hinh
        return int(lay_cau_hinh(db).get("nguong_co_chot_chan", 3))
    except Exception:
        return 3


def _tu_dong_gan_co_chot_chan(db: Session, session: SessionModel, bi_chot_lan_nay: bool) -> None:
    """Tự gắn cờ 'chốt chặn nhiều' khi số lượt phản hồi bị chốt chặn (rò rỉ đáp án) trong
    phiên vượt ngưỡng — dấu hiệu nội dung/câu hỏi có vấn đề. Chỉ gắn MỘT lần/phiên."""
    if not bi_chot_lan_nay:
        return
    from app.models.flag import Flag, LoaiCo, TrangThaiCo

    nguong = _nguong_co_chot_chan(db)
    if nguong <= 0:
        return
    db.flush()  # để lượt vừa thêm được tính vào số đếm
    so_chot = (
        db.query(Turn)
        .filter(Turn.session_id == session.id, Turn.co_bi_chot_chan.is_(True))
        .count()
    )
    if so_chot < nguong:
        return
    da_co = (
        db.query(Flag)
        .filter(Flag.session_id == session.id, Flag.loai_co == LoaiCo.chot_chan_nhieu)
        .first()
    )
    if da_co is not None:
        return
    db.add(Flag(
        session_id=session.id,
        loai_co=LoaiCo.chot_chan_nhieu,
        trang_thai=TrangThaiCo.cho_xu_ly,
        ghi_chu=f"Phản hồi bị chốt chặn rò rỉ đáp án {so_chot} lần (ngưỡng {nguong}) "
                f"— nên kiểm tra lại nội dung câu hỏi / gợi ý.",
    ))


def _steps_to_list(problem: Problem) -> list[dict]:
    return [
        {
            "thu_tu": s.thu_tu,
            "pham_vi": s.pham_vi,
            "mo_ta": s.mo_ta,
            "bieu_thuc_ket_qua": s.bieu_thuc_ket_qua,
            "danh_sach_goi_y": s.danh_sach_goi_y,
        }
        for s in problem.solution_steps
    ]


def _restore_state(session: SessionModel, problem: Problem) -> TrangThaiPhien:
    return TrangThaiPhien(
        loai_cau=problem.loai_cau.value,
        buoc_hien_tai=session.buoc_hien_tai,
        y_hien_tai=session.y_hien_tai,
        trang_thai_y=dict(session.trang_thai_y or {}),
        cap_goi_y_hien_tai=session.cap_goi_y_hien_tai,
        so_lan_sai_lien_tiep=session.so_lan_sai_lien_tiep,
        so_lan_khong_hieu=session.so_lan_khong_hieu,
        tong_so_lan_sai=session.tong_so_lan_sai,
        so_y_dung=session.so_y_dung,
        da_suy_luan=session.da_suy_luan,
        steps=_steps_to_list(problem),
        de_bai=problem.de_bai,
    )


def _da_can_thang_goi_y(st: TrangThaiPhien) -> bool:
    """True nếu bước/ý hiện tại đã cạn SẠCH thang gợi ý (mức gợi ý chạm trần) — cùng điều
    kiện với `_da_het_goi_y` (orchestrator) và `hetGoiY` (frontend, nơi khối 3 liên kết hiện)."""
    return st.cap_goi_y_hien_tai >= st.so_goi_y_buoc() - 1


def _tinh_diem_qua_trinh(tong_so_lan_sai: int, so_lan_khong_hieu: int) -> float:
    """Điểm quá trình (0-1, chỉ để GV tham khảo — KHÔNG phải điểm chính thức của bài):
    trừ dần theo số lần sai + số lần xin gợi ý/không hiểu cả phiên, không xuống dưới 0."""
    diem = 1.0 - 0.1 * tong_so_lan_sai - 0.15 * so_lan_khong_hieu
    return round(max(0.0, diem), 2)


def _la_chon_dap_an(dap_an_nhap) -> bool:
    """TN4PA: True nếu HS gửi một chữ cái A/B/C/D (chọn đáp án), False nếu là biểu thức."""
    if dap_an_nhap is None:
        return False
    return str(dap_an_nhap).strip().upper() in ("A", "B", "C", "D")


def _la_chon_dung_sai(dap_an_nhap) -> bool:
    """TNDS: True nếu HS gửi 'Dung'/'Sai' (chốt ý), False nếu là biểu thức suy luận."""
    if dap_an_nhap is None:
        return False
    return str(dap_an_nhap).strip().lower() in ("dung", "sai")


def _y_bat_buoc_suy_luan(meta, ky_hieu) -> bool:
    """TNDS: ý `ky_hieu` có bắt buộc suy luận trước khi chốt Đúng/Sai không."""
    for y in (meta or {}).get("y", []):
        if y.get("ky_hieu") == ky_hieu:
            return bool(y.get("bat_buoc_suy_luan", False))
    return False


def _dispatch(trang_thai, ket_qua, ngu_canh_hs, yeu_cau_goi_y, dap_an_nhap, loai_cau, meta=None):
    """Gọi đúng hàm orchestrator theo loại câu."""
    if loai_cau == "TLN":
        return xu_ly_tln(trang_thai, ket_qua, ngu_canh_hs, yeu_cau_goi_y)
    if loai_cau == "TN4PA":
        bat_buoc = bool((meta or {}).get("bat_buoc_suy_luan", False))
        return xu_ly_tn4pa(
            trang_thai, ket_qua, ngu_canh_hs, yeu_cau_goi_y,
            bat_buoc_suy_luan=bat_buoc,
            la_chon_dap_an=_la_chon_dap_an(dap_an_nhap),
        )
    if loai_cau == "TNDS":
        bat_buoc = _y_bat_buoc_suy_luan(meta, trang_thai.y_hien_tai)
        return xu_ly_tnds(
            trang_thai, ket_qua, ngu_canh_hs, yeu_cau_goi_y,
            bat_buoc_suy_luan_y=bat_buoc,
            la_chon_dung_sai=_la_chon_dung_sai(dap_an_nhap),
        )
    raise ValueError(f"Loại câu không hỗ trợ: {loai_cau}")


def _tim_phien_dang_lam(db: Session, hoc_sinh_id: int, problem_id: int) -> SessionModel | None:
    """Phiên dang_lam (chưa hoàn thành, chưa bị ẩn) gần nhất của HS cho ĐÚNG bài này, nếu có."""
    return (
        db.query(SessionModel)
        .filter(
            SessionModel.hoc_sinh_id == hoc_sinh_id,
            SessionModel.problem_id == problem_id,
            SessionModel.trang_thai == TrangThaiSession.dang_lam,
            SessionModel.bi_an == False,  # noqa: E712
        )
        .order_by(SessionModel.cap_nhat_luc.desc())
        .first()
    )


def tao_phien(
    db: Session,
    hoc_sinh_id: int,
    problem_id: int,
    llm: LLMClient,
) -> tuple[SessionModel, str]:
    problem = db.get(Problem, problem_id)
    if problem is None:
        raise ValueError(f"Không tìm thấy bài {problem_id}")

    # Tránh tạo phiên TRÙNG cho cùng 1 bài: các lối "bắt đầu bài" (Nhiệm vụ, Thi thử...) đều
    # gọi thẳng hàm này mà không tự kiểm tra HS đã có phiên dang_lam của đúng bài chưa — nếu
    # có, dùng lại phiên đó (không tạo mới/không gọi LLM lần nữa) để "Bài đang làm dở" không
    # hiện trùng bài. FE sẽ tự tải lại đầy đủ hội thoại qua GET /sessions/{id} sau khi nhận
    # session_id (giống hệt luồng "làm tiếp"), nên trả về turn gia_sư GẦN NHẤT làm van_ban
    # là đủ — không cần dựng lại toàn bộ lịch sử ở đây.
    phien_cu = _tim_phien_dang_lam(db, hoc_sinh_id, problem_id)
    if phien_cu is not None:
        turn_cuoi = (
            db.query(Turn)
            .filter(Turn.session_id == phien_cu.id, Turn.vai_tro == VaiTroTurn.gia_su)
            .order_by(Turn.id.desc())
            .first()
        )
        return phien_cu, (turn_cuoi.noi_dung if turn_cuoi else "")

    session = SessionModel(
        hoc_sinh_id=hoc_sinh_id,
        problem_id=problem_id,
        buoc_hien_tai=1,
        cap_goi_y_hien_tai=0,
    )
    db.add(session)
    db.flush()

    trang_thai = TrangThaiPhien(
        loai_cau=problem.loai_cau.value,
        steps=_steps_to_list(problem),
        de_bai=problem.de_bai,
    )
    chi_thi, trang_thai_moi = _dispatch(
        trang_thai, None, "", False, None, problem.loai_cau.value, problem.meta
    )

    # Đồng bộ y_hien_tai cho TNDS
    session.y_hien_tai = trang_thai_moi.y_hien_tai
    session.trang_thai_y = trang_thai_moi.trang_thai_y or {}

    van_ban_raw = llm.dien_dat(chi_thi.to_dict())

    # Chốt chặn: kiểm tra rò rỉ đáp án trước khi gửi HS — kể cả lời chào mở đầu phiên,
    # đúng tinh thần bất biến #3 (CLAUDE.md): rà MỌI phản hồi, không chỉ các lượt sau.
    gia_tri_chuan = (problem.meta or {}).get("dap_an_cuoi") or (problem.meta or {}).get("dap_an_dung")
    chot = kiem_tra_ro_ri(van_ban_raw, gia_tri_chuan, problem.loai_cau.value)
    van_ban = chot.van_ban_thay_the if chot.muc_do == MucDoRoRi.ro_ri else van_ban_raw
    bi_chot = chot.muc_do == MucDoRoRi.ro_ri

    turn_mo_dau = Turn(session_id=session.id, vai_tro=VaiTroTurn.gia_su, noi_dung=van_ban,
                       cap_goi_y=0, co_bi_chot_chan=bi_chot)
    db.add(turn_mo_dau)
    _gan_co_ro_ri_neu_bi_chot(db, session, turn_mo_dau, bi_chot)
    _tu_dong_gan_co_chot_chan(db, session, bi_chot)
    db.commit()
    db.refresh(session)
    return session, van_ban


def xu_ly_luot(
    db: Session,
    session: SessionModel,
    problem: Problem,
    noi_dung: str,
    dap_an_nhap: str | None,
    yeu_cau_goi_y: bool,
    llm: LLMClient,
) -> dict:
    loai_cau = problem.loai_cau.value
    db.add(Turn(
        session_id=session.id,
        vai_tro=VaiTroTurn.hoc_sinh,
        noi_dung=noi_dung,
        dap_an_nhap=str(dap_an_nhap) if dap_an_nhap is not None else None,
        cap_goi_y=session.cap_goi_y_hien_tai,
    ))

    trang_thai = _restore_state(session, problem)

    # So khớp đáp án nếu có
    ket_qua: KetQuaSoKhop | None = None
    ket_qua_dict = None
    if dap_an_nhap is not None:
        che_do = problem.che_do_so_khop.value
        if loai_cau == "TNDS" and session.y_hien_tai:
            if _la_chon_dung_sai(dap_an_nhap):
                # Pha chốt: so 'Dung'/'Sai' với đáp án chuẩn của ý
                try:
                    km = so_khop_tnds_mot_y(str(dap_an_nhap), problem.meta, session.y_hien_tai)
                    ket_qua = km.ket_qua
                    ket_qua_dict = {"ket_qua": ket_qua.value, "y": session.y_hien_tai,
                                    "la_chon": True}
                except ValueError:
                    ket_qua = KetQuaSoKhop.KHONG_PHAN_TICH_DUOC
            else:
                # Pha suy luận: CAS so biểu thức HS nhập với bieu_thuc_ket_qua của ý hiện tại
                buoc = trang_thai.buoc_data()
                bieu_thuc_chuan = (buoc or {}).get("bieu_thuc_ket_qua", "")
                km = so_khop("TLN", dap_an_nhap, {"dap_an_cuoi": bieu_thuc_chuan}, che_do)
                ket_qua = km.ket_qua
                ket_qua_dict = {"ket_qua": ket_qua.value, "y": session.y_hien_tai,
                                "la_chon": False}
        elif loai_cau == "TLN":
            # TLN nhiều bước: so với bieu_thuc_ket_qua của BƯỚC hiện tại (không phải dap_an_cuoi)
            buoc = trang_thai.buoc_data()
            bieu_thuc_chuan = (buoc or {}).get("bieu_thuc_ket_qua", "") or \
                problem.meta.get("dap_an_cuoi", "")
            chuan_dict = {"dap_an_cuoi": bieu_thuc_chuan,
                          "quy_tac_lam_tron": problem.meta.get("quy_tac_lam_tron")}
            km = so_khop(loai_cau, dap_an_nhap, chuan_dict, che_do)
            ket_qua = km.ket_qua
            ket_qua_dict = {"ket_qua": ket_qua.value}
        elif loai_cau == "TN4PA":
            if _la_chon_dap_an(dap_an_nhap):
                # Pha chọn đáp án: so chữ cái với dap_an_dung
                km = so_khop(loai_cau, dap_an_nhap, problem.meta, che_do)
                ket_qua = km.ket_qua
                ket_qua_dict = {"ket_qua": ket_qua.value, "la_chon_dap_an": True}
            else:
                # Pha suy luận: so biểu thức HS nhập với bieu_thuc_ket_qua của bước hiện tại.
                # Sự cố thực tế (production): sau khi làm đúng bước bắt buộc và đã MỞ KHÓA
                # đáp án, buoc_hien_tai chuyển sang bước KẾ TIẾP — bước đó thường RỖNG
                # (TN4PA chỉ cần đúng 1 bước để mở khóa, không có bước 2 thật). Nếu lúc này
                # HS lỡ gửi lại một biểu thức (thay vì bấm A/B/C/D), so_khop() với chuẩn
                # rỗng LUÔN thất bại (KHONG_PHAN_TICH_DUOC) — báo "nhập lại biểu thức hợp
                # lệ" dù HS nhập ĐÚNG TUYỆT ĐỐI, kể cả gửi lại chính biểu thức vừa đúng.
                # Chỉ so khớp khi bước hiện tại THẬT SỰ có chuẩn để chấm.
                buoc = trang_thai.buoc_data()
                bieu_thuc_chuan = (buoc or {}).get("bieu_thuc_ket_qua", "")
                if bieu_thuc_chuan.strip():
                    km = so_khop("TLN", dap_an_nhap, {"dap_an_cuoi": bieu_thuc_chuan}, che_do)
                    ket_qua = km.ket_qua
                    ket_qua_dict = {"ket_qua": ket_qua.value, "la_chon_dap_an": False}
        else:
            km = so_khop(loai_cau, dap_an_nhap, problem.meta, che_do)
            ket_qua = km.ket_qua
            ket_qua_dict = {"ket_qua": ket_qua.value, "diem": km.diem}

    # Chụp mức gợi ý TRƯỚC khi dispatch (dispatch mutate cùng object) để phát hiện cạnh lên
    # "vừa cạn sạch thang gợi ý" của đúng bước/ý này.
    can_thang_truoc = _da_can_thang_goi_y(trang_thai)
    buoc_y_truoc = (trang_thai.buoc_hien_tai, trang_thai.y_hien_tai)

    chi_thi, trang_thai_moi = _dispatch(
        trang_thai, ket_qua, noi_dung, yeu_cau_goi_y, dap_an_nhap, loai_cau, problem.meta
    )

    # "Hết gợi ý" (khối 3 liên kết hiện) = bước/ý VỪA chạm mức cạn thang gợi ý, cùng bước/ý —
    # đếm theo cạnh lên để không đếm trùng các lượt sau khi đã cạn.
    cung_buoc_y = buoc_y_truoc == (trang_thai_moi.buoc_hien_tai, trang_thai_moi.y_hien_tai)
    if cung_buoc_y and not can_thang_truoc and _da_can_thang_goi_y(trang_thai_moi):
        session.so_lan_het_goi_y = (session.so_lan_het_goi_y or 0) + 1

    # Ý đang xét trước khi ghi đè (để dồn thời gian vào đúng ý — TNDS)
    y_truoc = session.y_hien_tai

    now = datetime.now(timezone.utc)
    # --- THỜI GIAN HOẠT ĐỘNG: cộng dồn khoảng từ lần tương tác trước, CHẶN khoảng nghỉ dài.
    # Nhờ vậy "quay lại làm sau" (rời đi nhiều giờ/ngày) chỉ tính tối đa = ngưỡng nghỉ.
    moc_truoc = session.cap_nhat_luc or session.bat_dau_luc
    if moc_truoc is not None and moc_truoc.tzinfo is None:
        moc_truoc = moc_truoc.replace(tzinfo=timezone.utc)
    nguong = _nguong_nghi_giay(db)
    them = int(max(0, min((now - moc_truoc).total_seconds(), nguong))) if moc_truoc else 0
    session.thoi_gian_hoat_dong_giay = int(session.thoi_gian_hoat_dong_giay or 0) + them
    # TNDS: dồn thời gian hoạt động của lượt này vào ý đang xét.
    if loai_cau == "TNDS" and y_truoc:
        tg = dict(session.thoi_gian_y or {})
        tg[y_truoc] = int(tg.get(y_truoc, 0)) + them
        session.thoi_gian_y = tg

    # Ghi lại trạng thái
    session.buoc_hien_tai = trang_thai_moi.buoc_hien_tai
    session.y_hien_tai = trang_thai_moi.y_hien_tai
    session.trang_thai_y = trang_thai_moi.trang_thai_y or {}
    session.cap_goi_y_hien_tai = trang_thai_moi.cap_goi_y_hien_tai
    session.so_lan_sai_lien_tiep = trang_thai_moi.so_lan_sai_lien_tiep
    session.so_lan_khong_hieu = trang_thai_moi.so_lan_khong_hieu
    session.tong_so_lan_sai = trang_thai_moi.tong_so_lan_sai
    session.so_y_dung = trang_thai_moi.so_y_dung
    session.da_suy_luan = trang_thai_moi.da_suy_luan
    session.cap_nhat_luc = now

    # Tự gắn cờ cho GV khi HS "không hiểu" vượt ngưỡng (gắn 1 lần/phiên).
    _tu_dong_gan_co_khong_hieu(db, session)

    if trang_thai_moi.da_xong:
        session.trang_thai = TrangThaiSession.hoan_thanh
        # Điểm cuối: TNDS theo bậc thang số ý đúng; TLN/TN4PA hoàn thành = 1.0
        if loai_cau == "TNDS":
            session.diem = diem_bac_thang(trang_thai_moi.so_y_dung)
        else:
            session.diem = 1.0
        # Thời gian làm bài = tổng thời gian HOẠT ĐỘNG (đã chặn nghỉ).
        session.thoi_gian_giay = int(session.thoi_gian_hoat_dong_giay or 0)
        session.diem_qua_trinh = _tinh_diem_qua_trinh(
            trang_thai_moi.tong_so_lan_sai, trang_thai_moi.so_lan_khong_hieu
        )

    van_ban_raw = llm.dien_dat(chi_thi.to_dict())

    # Chốt chặn: kiểm tra rò rỉ đáp án trước khi gửi HS
    gia_tri_chuan = (problem.meta or {}).get("dap_an_cuoi") or (problem.meta or {}).get("dap_an_dung")
    chot = kiem_tra_ro_ri(van_ban_raw, gia_tri_chuan, loai_cau)
    van_ban = chot.van_ban_thay_the if chot.muc_do == MucDoRoRi.ro_ri else van_ban_raw
    bi_chot = chot.muc_do == MucDoRoRi.ro_ri

    turn_phan_hoi = Turn(
        session_id=session.id,
        vai_tro=VaiTroTurn.gia_su,
        noi_dung=van_ban,
        ket_qua_so_khop=ket_qua_dict,
        cap_goi_y=trang_thai_moi.cap_goi_y_hien_tai,
        co_bi_chot_chan=bi_chot,
    )
    db.add(turn_phan_hoi)
    _gan_co_ro_ri_neu_bi_chot(db, session, turn_phan_hoi, bi_chot)

    # Tự gắn cờ cho GV khi phản hồi bị chốt chặn rò rỉ vượt ngưỡng (gắn 1 lần/phiên).
    _tu_dong_gan_co_chot_chan(db, session, bi_chot)

    if trang_thai_moi.da_xong:
        cap_nhat_tien_do(db, session.hoc_sinh_id, problem.chuyen_de)
        from app.services.chuoi_ngay_service import kiem_tra_va_cap_nhat_cot_moc
        kiem_tra_va_cap_nhat_cot_moc(db, session.hoc_sinh_id)

    db.commit()

    return {
        "van_ban": van_ban,
        "y_dinh": chi_thi.y_dinh,
        "buoc_hien_tai": trang_thai_moi.buoc_hien_tai,
        "cap_goi_y": trang_thai_moi.cap_goi_y_hien_tai,
        "da_xong": trang_thai_moi.da_xong,
        "diem": session.diem,
        "y_hien_tai": trang_thai_moi.y_hien_tai,
        "so_y_dung": trang_thai_moi.so_y_dung,
        "thoi_gian_giay": session.thoi_gian_giay,
        "so_lan_khong_hieu": trang_thai_moi.so_lan_khong_hieu,
        "tong_so_lan_sai": trang_thai_moi.tong_so_lan_sai,
    }
