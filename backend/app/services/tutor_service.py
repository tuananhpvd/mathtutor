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
        so_y_dung=session.so_y_dung,
        da_suy_luan=session.da_suy_luan,
        steps=_steps_to_list(problem),
    )


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


def tao_phien(
    db: Session,
    hoc_sinh_id: int,
    problem_id: int,
    llm: LLMClient,
) -> tuple[SessionModel, str]:
    problem = db.get(Problem, problem_id)
    if problem is None:
        raise ValueError(f"Không tìm thấy bài {problem_id}")

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
    )
    chi_thi, trang_thai_moi = _dispatch(
        trang_thai, None, "", False, None, problem.loai_cau.value, problem.meta
    )

    # Đồng bộ y_hien_tai cho TNDS
    session.y_hien_tai = trang_thai_moi.y_hien_tai
    session.trang_thai_y = trang_thai_moi.trang_thai_y or {}

    van_ban = llm.dien_dat(chi_thi.to_dict())
    db.add(Turn(session_id=session.id, vai_tro=VaiTroTurn.gia_su, noi_dung=van_ban, cap_goi_y=0))
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
                # Pha suy luận: so biểu thức HS nhập với bieu_thuc_ket_qua của bước hiện tại
                buoc = trang_thai.buoc_data()
                bieu_thuc_chuan = (buoc or {}).get("bieu_thuc_ket_qua", "")
                km = so_khop("TLN", dap_an_nhap, {"dap_an_cuoi": bieu_thuc_chuan}, che_do)
                ket_qua = km.ket_qua
                ket_qua_dict = {"ket_qua": ket_qua.value, "la_chon_dap_an": False}
        else:
            km = so_khop(loai_cau, dap_an_nhap, problem.meta, che_do)
            ket_qua = km.ket_qua
            ket_qua_dict = {"ket_qua": ket_qua.value, "diem": km.diem}

    chi_thi, trang_thai_moi = _dispatch(
        trang_thai, ket_qua, noi_dung, yeu_cau_goi_y, dap_an_nhap, loai_cau, problem.meta
    )

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
    session.so_y_dung = trang_thai_moi.so_y_dung
    session.da_suy_luan = trang_thai_moi.da_suy_luan
    session.cap_nhat_luc = now

    if trang_thai_moi.da_xong:
        session.trang_thai = TrangThaiSession.hoan_thanh
        # Điểm cuối: TNDS theo bậc thang số ý đúng; TLN/TN4PA hoàn thành = 1.0
        if loai_cau == "TNDS":
            session.diem = diem_bac_thang(trang_thai_moi.so_y_dung)
        else:
            session.diem = 1.0
        # Thời gian làm bài = tổng thời gian HOẠT ĐỘNG (đã chặn nghỉ).
        session.thoi_gian_giay = int(session.thoi_gian_hoat_dong_giay or 0)

    van_ban_raw = llm.dien_dat(chi_thi.to_dict())

    # Chốt chặn: kiểm tra rò rỉ đáp án trước khi gửi HS
    gia_tri_chuan = (problem.meta or {}).get("dap_an_cuoi") or (problem.meta or {}).get("dap_an_dung")
    chot = kiem_tra_ro_ri(van_ban_raw, gia_tri_chuan, loai_cau)
    van_ban = chot.van_ban_thay_the if chot.muc_do == MucDoRoRi.ro_ri else van_ban_raw
    bi_chot = chot.muc_do == MucDoRoRi.ro_ri

    db.add(Turn(
        session_id=session.id,
        vai_tro=VaiTroTurn.gia_su,
        noi_dung=van_ban,
        ket_qua_so_khop=ket_qua_dict,
        cap_goi_y=trang_thai_moi.cap_goi_y_hien_tai,
        co_bi_chot_chan=bi_chot,
    ))

    if trang_thai_moi.da_xong:
        cap_nhat_tien_do(db, session.hoc_sinh_id, problem.chuyen_de)

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
    }
