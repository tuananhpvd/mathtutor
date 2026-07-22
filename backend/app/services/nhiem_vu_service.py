"""Dịch vụ giao bài/nhiệm vụ (A3).

GV giao thủ công từng HS / cả lớp, hoặc duyệt bộ bài hệ thống đề xuất theo điểm
yếu. HS có 'Nhiệm vụ của em' với tiến độ. Không phụ thuộc LLM/web.
"""

from datetime import datetime

from sqlalchemy.orm import Session

from app.models.nhiem_vu import NhiemVu, NhiemVuBai, NhiemVuHocSinh
from app.models.problem import Problem, TrangThaiDuyet
from app.models.session import Session as SessionModel
from app.models.session import TrangThaiSession
from app.models.thong_bao import LoaiThongBao
from app.models.user import User, VaiTro
from app.services import thong_bao_service
from app.services.gv_service import _so_huu_hs, _so_huu_lop


def _hoan_thanh_set(db: Session, hs_id: int, problem_ids: list[int]) -> set[int]:
    """Tập problem_id mà HS đã có phiên HOÀN THÀNH (không tính phiên bị ẩn)."""
    if not problem_ids:
        return set()
    rows = (
        db.query(SessionModel.problem_id)
        .filter(
            SessionModel.hoc_sinh_id == hs_id,
            SessionModel.problem_id.in_(problem_ids),
            SessionModel.trang_thai == TrangThaiSession.hoan_thanh,
            SessionModel.bi_an == False,  # noqa: E712
        )
        .distinct()
        .all()
    )
    return {r[0] for r in rows}


def dem_hoan_thanh(db: Session, gv_id: int, hoc_sinh_ids: list[int]) -> dict:
    """Với tập HS đang chọn, đếm mỗi bài có BAO NHIÊU em đã hoàn thành.

    Trả `{"so_hoc_sinh": N, "theo_bai": {problem_id: so_em_da_lam}}` — FE dùng để:
      - làm mờ & cấm tích bài mà CẢ NHÓM đã làm (giao lại là vô ích với mọi em),
      - gắn nhãn "3/5 em đã làm" cho bài mới một phần nhóm làm (GV tự quyết).
    Chỉ trả bài CÓ ít nhất 1 em đã làm (bảng thưa) để không tải cả ngân hàng câu hỏi.
    """
    hs_ids = list(dict.fromkeys(hoc_sinh_ids or []))
    for hid in hs_ids:
        if not _so_huu_hs(db, gv_id, hid):
            raise ValueError("Có học sinh không thuộc lớp của bạn")
    if not hs_ids:
        return {"so_hoc_sinh": 0, "theo_bai": {}}

    rows = (
        db.query(SessionModel.problem_id, SessionModel.hoc_sinh_id)
        .filter(
            SessionModel.hoc_sinh_id.in_(hs_ids),
            SessionModel.trang_thai == TrangThaiSession.hoan_thanh,
            SessionModel.bi_an == False,  # noqa: E712
        )
        .distinct()
        .all()
    )
    theo_bai: dict[int, int] = {}
    for pid, _hid in rows:
        theo_bai[pid] = theo_bai.get(pid, 0) + 1
    return {"so_hoc_sinh": len(hs_ids), "theo_bai": theo_bai}


def _chan_bai_ca_nhom_da_lam(db: Session, problem_ids: list[int], hs_ids: list[int]) -> None:
    """Chặn giao bài mà MỌI HS nhận nhiệm vụ đều đã hoàn thành.

    Vì sao là "mọi em" chứ không phải "bất kỳ em nào": nhiệm vụ giao cho cả lớp thì hầu như
    bài nào cũng có một em nào đó từng làm — chặn theo "bất kỳ" sẽ khiến GV không còn bài nào
    giao được. Chặn theo "mọi em" chỉ loại đúng những bài vô ích với toàn nhóm.

    Chốt chặn đặt ở SERVICE (không phải ở FE) để cả đường tạo mới lẫn đường sửa nhiệm vụ đều
    đi qua, và không phụ thuộc việc FE có lọc đúng hay không.
    """
    if not problem_ids or not hs_ids:
        return
    da_lam = {}
    for hid in hs_ids:
        for pid in _hoan_thanh_set(db, hid, problem_ids):
            da_lam[pid] = da_lam.get(pid, 0) + 1
    vi_pham = [pid for pid in problem_ids if da_lam.get(pid, 0) == len(hs_ids)]
    if vi_pham:
        ds = ", ".join(f"#{pid}" for pid in vi_pham[:5])
        them = f" và {len(vi_pham) - 5} bài khác" if len(vi_pham) > 5 else ""
        raise ValueError(
            f"Không giao được: bài {ds}{them} đã được TẤT CẢ học sinh nhận nhiệm vụ hoàn thành. "
            "Hãy bỏ chọn bài đó hoặc chọn thêm học sinh chưa làm."
        )


def _bai_dict(p: Problem) -> dict:
    return {
        "problem_id": p.id,
        "chuyen_de": p.chuyen_de,
        "dang_ten": p.dang.ten if p.dang else None,
        "loai_cau": p.loai_cau.value,
        "do_kho": p.do_kho.value,
        "de_bai": p.de_bai,
    }


def tao_nhiem_vu(
    db: Session,
    gv_id: int,
    tieu_de: str,
    mo_ta: str | None,
    han_chot: datetime | None,
    problem_ids: list[int],
    hoc_sinh_ids: list[int] | None = None,
    lop_ids: list[int] | None = None,
) -> dict:
    tieu_de = (tieu_de or "").strip()
    if not tieu_de:
        raise ValueError("Tiêu đề nhiệm vụ không được để trống")
    problem_ids = list(dict.fromkeys(problem_ids or []))
    if not problem_ids:
        raise ValueError("Cần chọn ít nhất 1 bài")

    # Gộp HS từ danh sách HS lẻ + các lớp.
    hs_set: set[int] = set(hoc_sinh_ids or [])
    for lid in (lop_ids or []):
        if not _so_huu_lop(db, gv_id, lid):
            raise ValueError("Không có quyền với lớp đã chọn")
        for u in db.query(User).filter(
            User.lop_id == lid, User.vai_tro == VaiTro.hs
        ).all():
            hs_set.add(u.id)
    if not hs_set:
        raise ValueError("Cần chọn ít nhất 1 học sinh hoặc 1 lớp")
    for hid in hs_set:
        if not _so_huu_hs(db, gv_id, hid):
            raise ValueError("Có học sinh không thuộc lớp của bạn")

    ps = db.query(Problem).filter(Problem.id.in_(problem_ids)).all()
    found = {p.id for p in ps}
    if found != set(problem_ids):
        raise ValueError("Có bài không tồn tại")
    for p in ps:
        if p.trang_thai_duyet != TrangThaiDuyet.da_duyet or p.bi_an:
            raise ValueError("Chỉ giao được bài đã duyệt")
        if p.nguoi_tao_id != gv_id:
            raise ValueError(f"Câu hỏi #{p.id} không thuộc bạn — chỉ được giao bài của mình")
    _chan_bai_ca_nhom_da_lam(db, problem_ids, list(hs_set))

    nv = NhiemVu(
        gv_id=gv_id, tieu_de=tieu_de,
        mo_ta=(mo_ta or "").strip() or None, han_chot=han_chot,
    )
    db.add(nv)
    db.flush()
    for pid in problem_ids:
        db.add(NhiemVuBai(nhiem_vu_id=nv.id, problem_id=pid))
    for hid in hs_set:
        db.add(NhiemVuHocSinh(nhiem_vu_id=nv.id, hoc_sinh_id=hid))
    db.commit()

    han_txt = f", hạn {han_chot.strftime('%d/%m/%Y')}" if han_chot else ""
    noi_dung = f"Thầy/cô giao nhiệm vụ: «{tieu_de}» ({len(problem_ids)} bài){han_txt}."
    for hid in hs_set:
        thong_bao_service.tao(
            db, nguoi_nhan_id=hid, noi_dung=noi_dung,
            loai=LoaiThongBao.nhiem_vu, nguoi_gui_id=gv_id,
            tieu_de="Nhiệm vụ mới", lien_ket_loai="nhiem_vu", lien_ket_id=nv.id,
        )
    return {"id": nv.id, "so_hs": len(hs_set), "so_bai": len(problem_ids)}


def de_xuat_theo_diem_yeu(db: Session, gv_id: int, hoc_sinh_id: int, gioi_han: int = 10) -> dict:
    """Đề xuất bài theo dạng yếu của HS (chưa hoàn thành) để GV duyệt rồi giao."""
    if not _so_huu_hs(db, gv_id, hoc_sinh_id):
        raise ValueError("Không có quyền với học sinh này")
    from app.services.phan_tich_service import ho_so_nang_luc

    ho_so = ho_so_nang_luc(db, hoc_sinh_id)
    diem_yeu = ho_so.get("diem_yeu") or []
    dang_ids = [r["dang_id"] for r in diem_yeu if r.get("dang_id")]
    if not dang_ids:
        return {"dang_yeu": [r["ten"] for r in diem_yeu], "bai": []}

    problems = (
        db.query(Problem)
        .filter(
            Problem.dang_id.in_(dang_ids),
            Problem.trang_thai_duyet == TrangThaiDuyet.da_duyet,
            Problem.bi_an == False,  # noqa: E712
        )
        .all()
    )
    done = _hoan_thanh_set(db, hoc_sinh_id, [p.id for p in problems])
    bai = [_bai_dict(p) for p in problems if p.id not in done][:gioi_han]
    return {"dang_yeu": [r["ten"] for r in diem_yeu], "bai": bai}


def de_xuat_theo_dang(
    db: Session, gv_id: int, hoc_sinh_id: int, dang_id: int, gioi_han: int = 10
) -> list[dict]:
    """Đề xuất bài CÙNG DẠNG (dang_id) mà HS chưa hoàn thành — dùng cho gợi ý "giao
    nhiệm vụ luyện lại" ngay tại câu sai cụ thể trong 1 bài thi (khác de_xuat_theo_diem_yeu
    vốn quét toàn bộ hồ sơ năng lực, hàm này chỉ khoanh đúng 1 dạng do GV chỉ định)."""
    if not _so_huu_hs(db, gv_id, hoc_sinh_id):
        raise ValueError("Không có quyền với học sinh này")
    problems = (
        db.query(Problem)
        .filter(
            Problem.dang_id == dang_id,
            Problem.trang_thai_duyet == TrangThaiDuyet.da_duyet,
            Problem.bi_an == False,  # noqa: E712
            Problem.nguoi_tao_id == gv_id,
        )
        .all()
    )
    done = _hoan_thanh_set(db, hoc_sinh_id, [p.id for p in problems])
    return [_bai_dict(p) for p in problems if p.id not in done][:gioi_han]


def danh_sach_gv(db: Session, gv_id: int) -> list[dict]:
    nhiem_vus = (
        db.query(NhiemVu).filter(NhiemVu.gv_id == gv_id)
        .order_by(NhiemVu.tao_luc.desc(), NhiemVu.id.desc()).all()
    )
    nv_ids = [nv.id for nv in nhiem_vus]
    if not nv_ids:
        return []
    bai_rows = db.query(NhiemVuBai).filter(NhiemVuBai.nhiem_vu_id.in_(nv_ids)).all()
    hs_rows = db.query(NhiemVuHocSinh).filter(NhiemVuHocSinh.nhiem_vu_id.in_(nv_ids)).all()

    bai_by_nv: dict[int, list[int]] = {}
    for b in bai_rows:
        bai_by_nv.setdefault(b.nhiem_vu_id, []).append(b.problem_id)
    hs_by_nv: dict[int, list[int]] = {}
    for h in hs_rows:
        hs_by_nv.setdefault(h.nhiem_vu_id, []).append(h.hoc_sinh_id)
    hs_ten = {
        u.id: u.ho_ten
        for u in db.query(User).filter(User.id.in_({h.hoc_sinh_id for h in hs_rows})).all()
    }

    # Batch-load tất cả Problem để trả chi tiết bài
    all_pids = {pid for pids in bai_by_nv.values() for pid in pids}
    problems_map = (
        {p.id: p for p in db.query(Problem).filter(Problem.id.in_(all_pids)).all()}
        if all_pids else {}
    )

    def _meta_safe(p: Problem) -> dict:
        if p.loai_cau.value == "TN4PA":
            return {"phuong_an": (p.meta or {}).get("phuong_an", {})}
        if p.loai_cau.value == "TNDS":
            return {"y": [{"ky_hieu": y.get("ky_hieu", ""), "noi_dung_y": y.get("noi_dung_y", "")}
                          for y in (p.meta or {}).get("y", [])]}
        return {}

    out = []
    for nv in nhiem_vus:
        pids = list(dict.fromkeys(bai_by_nv.get(nv.id, [])))
        hids = hs_by_nv.get(nv.id, [])
        hs_prog = []
        so_xong_het = 0
        for hid in hids:
            done = _hoan_thanh_set(db, hid, pids)
            n = len(done)
            if pids and n == len(pids):
                so_xong_het += 1
            hs_prog.append({"ho_ten": hs_ten.get(hid), "so_hoan_thanh": n, "tong_bai": len(pids)})
        bai_detail = []
        for pid in pids:
            p = problems_map.get(pid)
            if p:
                bai_detail.append({
                    "id": p.id, "chuyen_de": p.chuyen_de,
                    "dang_ten": p.dang.ten if p.dang else None,
                    "loai_cau": p.loai_cau.value, "do_kho": p.do_kho.value,
                    "de_bai": p.de_bai, "meta": _meta_safe(p),
                })
        out.append({
            "id": nv.id, "tieu_de": nv.tieu_de, "mo_ta": nv.mo_ta,
            "han_chot": nv.han_chot.isoformat() if nv.han_chot else None,
            "tao_luc": nv.tao_luc.isoformat() if nv.tao_luc else None,
            "so_bai": len(pids), "so_hs": len(hids),
            "so_hs_hoan_thanh": so_xong_het, "hoc_sinh": hs_prog,
            "bai": bai_detail,
        })
    return out


def danh_sach_hs(db: Session, hs_id: int) -> list[dict]:
    nv_hs = db.query(NhiemVuHocSinh).filter(NhiemVuHocSinh.hoc_sinh_id == hs_id).all()
    nv_ids = [x.nhiem_vu_id for x in nv_hs]
    if not nv_ids:
        return []
    nhiem_vus = {
        nv.id: nv for nv in db.query(NhiemVu).filter(NhiemVu.id.in_(nv_ids)).all()
    }
    bai_rows = db.query(NhiemVuBai).filter(NhiemVuBai.nhiem_vu_id.in_(nv_ids)).all()
    by_nv: dict[int, list[int]] = {}
    all_pids: set[int] = set()
    for b in bai_rows:
        by_nv.setdefault(b.nhiem_vu_id, []).append(b.problem_id)
        all_pids.add(b.problem_id)
    problems = (
        {p.id: p for p in db.query(Problem).filter(Problem.id.in_(all_pids)).all()}
        if all_pids else {}
    )
    done = _hoan_thanh_set(db, hs_id, list(all_pids))
    gv_ten = {
        u.id: u.ho_ten
        for u in db.query(User).filter(
            User.id.in_({nv.gv_id for nv in nhiem_vus.values()})
        ).all()
    }

    out = []
    for nv in nhiem_vus.values():
        pids = list(dict.fromkeys(by_nv.get(nv.id, [])))
        bai = []
        for pid in pids:
            p = problems.get(pid)
            if p is None:
                continue
            bai.append({
                "problem_id": pid, "chuyen_de": p.chuyen_de,
                "dang_ten": p.dang.ten if p.dang else None,
                "loai_cau": p.loai_cau.value, "do_kho": p.do_kho.value,
                "de_bai": p.de_bai,
                "da_hoan_thanh": pid in done,
            })
        so_ht = sum(1 for b in bai if b["da_hoan_thanh"])
        out.append({
            "id": nv.id, "tieu_de": nv.tieu_de, "mo_ta": nv.mo_ta,
            "han_chot": nv.han_chot.isoformat() if nv.han_chot else None,
            "tao_luc": nv.tao_luc.isoformat() if nv.tao_luc else None,
            "gv_ten": gv_ten.get(nv.gv_id),
            "bai": bai, "so_hoan_thanh": so_ht, "tong_bai": len(bai),
        })
    # Chưa hoàn thành lên trước, trong mỗi nhóm mới-trước (2 lần sort ổn định).
    out.sort(key=lambda x: x["tao_luc"] or "", reverse=True)
    out.sort(key=lambda x: x["tong_bai"] > 0 and x["so_hoan_thanh"] >= x["tong_bai"])
    return out


def cap_nhat_nhiem_vu(db: Session, gv_id: int, nv_id: int, data: dict) -> dict:
    nv = db.get(NhiemVu, nv_id)
    if nv is None or nv.gv_id != gv_id:
        raise ValueError("Nhiệm vụ không tồn tại hoặc không thuộc quyền của bạn")
    if "tieu_de" in data:
        tieu_de = (data["tieu_de"] or "").strip()
        if not tieu_de:
            raise ValueError("Tiêu đề không được để trống")
        nv.tieu_de = tieu_de
    if "mo_ta" in data:
        nv.mo_ta = (data["mo_ta"] or "").strip() or None
    if "han_chot" in data:
        from datetime import datetime
        v = data["han_chot"]
        nv.han_chot = datetime.fromisoformat(v) if v else None
    if "problem_ids" in data:
        new_pids = list(dict.fromkeys(data["problem_ids"] or []))
        if not new_pids:
            raise ValueError("Cần chọn ít nhất 1 bài")
        ps = db.query(Problem).filter(Problem.id.in_(new_pids)).all()
        if len(ps) != len(new_pids):
            raise ValueError("Có bài không tồn tại")
        for p in ps:
            if p.trang_thai_duyet != TrangThaiDuyet.da_duyet or p.bi_an:
                raise ValueError("Chỉ giao được bài đã duyệt")
            if p.nguoi_tao_id != gv_id:
                raise ValueError(f"Câu hỏi #{p.id} không thuộc bạn — chỉ được giao bài của mình")
        # Đường SỬA nhiệm vụ cũng phải chặn — trước đây chỉ tạo mới mới kiểm, nên GV vẫn thêm
        # được bài đã hoàn thành bằng cách tạo rồi sửa.
        hs_ids_nv = [
            r[0] for r in db.query(NhiemVuHocSinh.hoc_sinh_id)
            .filter(NhiemVuHocSinh.nhiem_vu_id == nv_id).all()
        ]
        _chan_bai_ca_nhom_da_lam(db, new_pids, hs_ids_nv)
        db.query(NhiemVuBai).filter(NhiemVuBai.nhiem_vu_id == nv_id).delete()
        for pid in new_pids:
            db.add(NhiemVuBai(nhiem_vu_id=nv_id, problem_id=pid))
    db.commit()
    return {"id": nv.id, "tieu_de": nv.tieu_de, "mo_ta": nv.mo_ta,
            "han_chot": nv.han_chot.isoformat() if nv.han_chot else None}


def xoa_nhiem_vu(db: Session, gv_id: int, nv_id: int) -> None:
    nv = db.get(NhiemVu, nv_id)
    if nv is None or nv.gv_id != gv_id:
        raise ValueError("Nhiệm vụ không tồn tại hoặc không thuộc quyền của bạn")
    db.query(NhiemVuBai).filter(NhiemVuBai.nhiem_vu_id == nv_id).delete()
    db.query(NhiemVuHocSinh).filter(NhiemVuHocSinh.nhiem_vu_id == nv_id).delete()
    db.delete(nv)
    db.commit()
