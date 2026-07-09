"""Service: GV/Admin sửa & xóa câu hỏi (Problem) + các bước lời giải."""

import re

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.danh_muc import Dang
from app.models.flag import Flag
from app.models.problem import (
    CheDoSoKhopEnum,
    DoKho,
    LoaiCau,
    Nguon,
    Problem,
    TrangThaiDuyet,
)
from app.models.session import Session as SessionModel
from app.models.solution_step import SolutionStep
from app.models.turn import Turn

LOAI_DAP_AN_THEO_LOAI = {
    "TN4PA": "chon_phuong_an",
    "TNDS": "dung_sai_4y",
    "TLN": "gia_tri",
}

_RE_SO_TLN = re.compile(r"^-?\d+([.,]\d+)?$")


def _kiem_tra_dap_an_tln(meta: dict) -> None:
    """Đáp án TLN phải là số nguyên/thập phân ≤ 4 ký tự (gồm -, ,)."""
    v = str(meta.get("dap_an_cuoi") or "").strip()
    if not v:
        raise ValueError("Đáp án cuối không được để trống")
    if len(v) > 4:
        raise ValueError("Đáp án cuối tối đa 4 ký tự (gồm dấu - và dấu ,)")
    if not _RE_SO_TLN.match(v):
        raise ValueError("Đáp án cuối phải là số nguyên hoặc số thập phân (ví dụ: 3, -2, 1,5)")


def tao_problem(db: Session, du_lieu: dict, nguoi_tao_id: int | None) -> Problem:
    """Tạo câu hỏi mới (GV/Admin nhập). Trạng thái khởi tạo: cho_duyet."""
    try:
        loai = LoaiCau(du_lieu.get("loai_cau"))
    except ValueError:
        raise ValueError("loai_cau phải là TN4PA | TNDS | TLN")
    try:
        do_kho = DoKho(du_lieu.get("do_kho", "tb"))
    except ValueError:
        raise ValueError("do_kho phải là de | tb | kho")

    de_bai = (du_lieu.get("de_bai") or "").strip()
    if not de_bai:
        raise ValueError("Đề bài không được rỗng")

    chuyen_de = du_lieu.get("chuyen_de")
    dang_id = du_lieu.get("dang_id")
    if dang_id is not None:
        dang = db.get(Dang, dang_id)
        if dang is None:
            raise ValueError("Không tìm thấy dạng")
        if dang.chuyen_de is not None:
            chuyen_de = dang.chuyen_de.ten
    if not chuyen_de:
        raise ValueError("Phải chọn dạng (chuyên đề)")

    try:
        che_do = CheDoSoKhopEnum(du_lieu.get("che_do_so_khop", "tuong_duong"))
    except ValueError:
        raise ValueError("che_do_so_khop không hợp lệ")

    meta = du_lieu.get("meta") or {}
    if loai == LoaiCau.TLN:
        _kiem_tra_dap_an_tln(meta)

    p = Problem(
        chuyen_de=chuyen_de,
        dang_id=dang_id,
        loai_cau=loai,
        do_kho=do_kho,
        de_bai=de_bai,
        loai_dap_an_nhap=LOAI_DAP_AN_THEO_LOAI[loai.value],
        che_do_so_khop=che_do,
        hinh_anh=du_lieu.get("hinh_anh"),
        # GV nhập thủ công → duyệt ngay. Câu hỏi luôn thuộc riêng người tạo.
        trang_thai_duyet=TrangThaiDuyet.da_duyet,
        nguon=Nguon.gv_nhap,
        nguoi_tao_id=nguoi_tao_id,
        meta=meta,
        loi_giai_chi_tiet=(du_lieu.get("loi_giai_chi_tiet") or "").strip(),
        hien_loi_giai_chi_tiet=bool(du_lieu.get("hien_loi_giai_chi_tiet", False)),
    )
    db.add(p)
    db.flush()
    for s in du_lieu.get("solution_steps") or []:
        db.add(SolutionStep(
            problem_id=p.id,
            thu_tu=s.get("thu_tu", 1),
            pham_vi=s.get("pham_vi", "ca_bai"),
            mo_ta=s.get("mo_ta", ""),
            bieu_thuc_ket_qua=s.get("bieu_thuc_ket_qua", ""),
            danh_sach_goi_y=s.get("danh_sach_goi_y", []),
        ))
    db.commit()
    db.refresh(p)
    return p


def import_batch(db: Session, items: list, nguoi_tao_id: int | None) -> dict:
    """Import hàng loạt câu hỏi từ file mẫu. Trạng thái khởi tạo: cho_duyet."""
    da_tao: list[int] = []
    loi: list[dict] = []

    for i, item in enumerate(items):
        try:
            loai = LoaiCau(item.loai_cau)
            do_kho = DoKho(item.do_kho)
            de_bai = (item.de_bai or "").strip()
            if not de_bai:
                raise ValueError("Đề bài không được rỗng")
            chuyen_de = (item.chuyen_de or "").strip()
            if not chuyen_de:
                raise ValueError("Chuyên đề không được rỗng")

            meta = item.meta or {}
            if loai == LoaiCau.TLN:
                _kiem_tra_dap_an_tln(meta)

            dang_id: int | None = None
            if item.dang_ten:
                dang = db.query(Dang).filter(
                    func.lower(Dang.ten) == item.dang_ten.strip().lower()
                ).first()
                if dang is not None:
                    dang_id = dang.id
                    if dang.chuyen_de is not None:
                        chuyen_de = dang.chuyen_de.ten

            sp = db.begin_nested()
            try:
                p = Problem(
                    chuyen_de=chuyen_de,
                    dang_id=dang_id,
                    loai_cau=loai,
                    do_kho=do_kho,
                    de_bai=de_bai,
                    hinh_anh=item.hinh_anh,
                    loai_dap_an_nhap=LOAI_DAP_AN_THEO_LOAI[loai.value],
                    trang_thai_duyet=TrangThaiDuyet.cho_duyet,
                    nguon=Nguon.gv_nhap,
                    nguoi_tao_id=nguoi_tao_id,
                    meta=meta,
                    loi_giai_chi_tiet=(item.loi_giai_chi_tiet or "").strip(),
                )
                db.add(p)
                db.flush()
                sp.commit()
                da_tao.append(p.id)
            except Exception as e:
                sp.rollback()
                raise e
        except Exception as e:
            loi.append({"dong": i + 1, "ly_do": str(e)})

    db.commit()
    return {"da_tao": len(da_tao), "ids": da_tao, "loi": loi}


def sua_problem(db: Session, problem_id: int, du_lieu: dict) -> Problem:
    """Cập nhật từng phần. du_lieu là dict đã exclude_unset (chỉ trường được gửi).

    - dang_id: nếu đổi, đồng bộ luôn `chuyen_de` (denormalized) theo chuyên đề của dạng.
    - solution_steps: nếu gửi, thay thế toàn bộ các bước cũ.
    """
    p = db.get(Problem, problem_id)
    if p is None:
        raise ValueError("Không tìm thấy câu hỏi")

    if "dang_id" in du_lieu:
        dang_id = du_lieu["dang_id"]
        if dang_id is not None:
            dang = db.get(Dang, dang_id)
            if dang is None:
                raise ValueError("Không tìm thấy dạng")
            p.dang_id = dang.id
            # Đồng bộ tên chuyên đề trừ khi caller gửi chuyen_de tường minh.
            if "chuyen_de" not in du_lieu and dang.chuyen_de is not None:
                p.chuyen_de = dang.chuyen_de.ten
        else:
            p.dang_id = None

    if "chuyen_de" in du_lieu and du_lieu["chuyen_de"]:
        p.chuyen_de = du_lieu["chuyen_de"]
    if "de_bai" in du_lieu and du_lieu["de_bai"]:
        p.de_bai = du_lieu["de_bai"]
    if "hinh_anh" in du_lieu:  # gửi None = gỡ ảnh; chuỗi = đặt ảnh mới
        p.hinh_anh = du_lieu["hinh_anh"]
    if "do_kho" in du_lieu and du_lieu["do_kho"]:
        try:
            p.do_kho = DoKho(du_lieu["do_kho"])
        except ValueError:
            raise ValueError("do_kho phải là de | tb | kho")
    if "meta" in du_lieu and du_lieu["meta"] is not None:
        if p.loai_cau == LoaiCau.TLN:
            _kiem_tra_dap_an_tln(du_lieu["meta"])
        p.meta = du_lieu["meta"]
    if "trang_thai_duyet" in du_lieu and du_lieu["trang_thai_duyet"]:
        try:
            p.trang_thai_duyet = TrangThaiDuyet(du_lieu["trang_thai_duyet"])
        except ValueError:
            raise ValueError("trang_thai_duyet không hợp lệ")
    if "loi_giai_chi_tiet" in du_lieu and du_lieu["loi_giai_chi_tiet"] is not None:
        p.loi_giai_chi_tiet = du_lieu["loi_giai_chi_tiet"].strip()
    if "hien_loi_giai_chi_tiet" in du_lieu and du_lieu["hien_loi_giai_chi_tiet"] is not None:
        p.hien_loi_giai_chi_tiet = bool(du_lieu["hien_loi_giai_chi_tiet"])

    if "solution_steps" in du_lieu and du_lieu["solution_steps"] is not None:
        # Xóa các bước cũ rồi tạo lại từ danh sách mới.
        for s in list(p.solution_steps):
            db.delete(s)
        db.flush()
        for s in du_lieu["solution_steps"]:
            db.add(SolutionStep(
                problem_id=p.id,
                thu_tu=s.get("thu_tu", 1),
                pham_vi=s.get("pham_vi", "ca_bai"),
                mo_ta=s.get("mo_ta", ""),
                bieu_thuc_ket_qua=s.get("bieu_thuc_ket_qua", ""),
                danh_sach_goi_y=s.get("danh_sach_goi_y", []),
            ))

    db.commit()
    db.refresh(p)
    return p


def xoa_problem(db: Session, problem_id: int) -> dict:
    """Xóa cứng nếu chưa có phiên học; ẩn (soft delete) nếu đã có dữ liệu HS."""
    p = db.get(Problem, problem_id)
    if p is None:
        raise ValueError("Không tìm thấy câu hỏi")
    co_phien = db.query(SessionModel).filter(SessionModel.problem_id == problem_id).count() > 0
    if co_phien:
        p.bi_an = True
        db.commit()
        return {"ok": True, "an": True}
    for s in list(p.solution_steps):
        db.delete(s)
    db.delete(p)
    db.commit()
    return {"ok": True, "an": False}


def khoi_phuc_problem(db: Session, problem_id: int) -> None:
    p = db.get(Problem, problem_id)
    if p is None:
        raise ValueError("Không tìm thấy câu hỏi")
    p.bi_an = False
    db.commit()


def anh_huong_xoa_vinh_vien(db: Session, problem_id: int) -> dict:
    """Thống kê dữ liệu sẽ bị xóa vĩnh viễn — để hiện cảnh báo trước khi xóa."""
    p = db.get(Problem, problem_id)
    if p is None:
        raise ValueError("Không tìm thấy câu hỏi")
    if not p.bi_an:
        raise ValueError("Câu hỏi phải được ẩn trước khi xóa vĩnh viễn")

    sessions = db.query(SessionModel).filter(SessionModel.problem_id == problem_id).all()
    session_ids = [s.id for s in sessions]
    so_hoc_sinh = len({s.hoc_sinh_id for s in sessions})

    so_luot = 0
    so_co = 0
    if session_ids:
        turn_ids = [
            t.id for t in db.query(Turn.id).filter(Turn.session_id.in_(session_ids)).all()
        ]
        so_luot = len(turn_ids)
        so_co = db.query(Flag).filter(
            Flag.session_id.in_(session_ids)
        ).count()
        if turn_ids:
            so_co += db.query(Flag).filter(Flag.turn_id.in_(turn_ids)).count()

    return {
        "so_phien": len(session_ids),
        "so_hoc_sinh": so_hoc_sinh,
        "so_luot": so_luot,
        "so_co": so_co,
    }


def xoa_vinh_vien_problem(db: Session, problem_id: int) -> dict:
    """Xóa cứng câu hỏi đã ẩn + toàn bộ dữ liệu liên quan (không thể hoàn tác)."""
    p = db.get(Problem, problem_id)
    if p is None:
        raise ValueError("Không tìm thấy câu hỏi")
    if not p.bi_an:
        raise ValueError("Câu hỏi phải được ẩn trước khi xóa vĩnh viễn")

    sessions = db.query(SessionModel).filter(SessionModel.problem_id == problem_id).all()
    session_ids = [s.id for s in sessions]

    if session_ids:
        turn_ids = [
            t.id for t in db.query(Turn.id).filter(Turn.session_id.in_(session_ids)).all()
        ]
        if turn_ids:
            db.query(Flag).filter(Flag.turn_id.in_(turn_ids)).delete(synchronize_session=False)
        db.query(Flag).filter(Flag.session_id.in_(session_ids)).delete(synchronize_session=False)
        db.query(Turn).filter(Turn.session_id.in_(session_ids)).delete(synchronize_session=False)
        db.query(SessionModel).filter(
            SessionModel.problem_id == problem_id
        ).delete(synchronize_session=False)

    for step in list(p.solution_steps):
        db.delete(step)
    db.delete(p)
    db.commit()
    return {"ok": True, "so_phien_da_xoa": len(session_ids)}
