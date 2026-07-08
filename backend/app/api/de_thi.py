"""API đề ôn thi THPT (C1) — GV ghép/phát hành/xem kết quả; HS thi/nộp/xem kết quả.

Chốt chặn: lúc ĐANG THI, response tuyệt đối không mang trường đáp án (đề đi qua
`_strip_answers` như phòng học); đáp án đúng CHỈ có trong kết quả sau khi nộp.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.problems import _lay_dang_cd_map, _strip_answers
from app.auth.deps import CurrentUser, require_role
from app.db.session import get_db
from app.models.de_thi import DeThi, TrangThaiBaiThi
from app.models.problem import Problem
from app.models.user import User, VaiTro
from app.services import de_thi_service as svc

router = APIRouter(prefix="/api/de-thi", tags=["de-thi"])

_GV = [require_role(VaiTro.gv, VaiTro.admin)]
_HS = [require_role(VaiTro.hs)]


class TaoDeRequest(BaseModel):
    ten: str
    thoi_gian_phut: int = Field(90, ge=10, le=180)
    cau_theo_phan: dict[str, list[int]]  # {"I": [...], "II": [...], "III": [...]}


class PhatHanhRequest(BaseModel):
    phat_hanh: bool
    # None = giữ nguyên phạm vi đã cấu hình; chỉ cần khi phat_hanh=True và GV muốn đổi.
    pham_vi: str | None = None  # "tat_ca" | "tuy_chon"
    lop_ids: list[int] = Field(default_factory=list)
    hoc_sinh_ids: list[int] = Field(default_factory=list)


class TronDeRequest(BaseModel):
    so_cau: dict[str, int] = Field(default_factory=lambda: {"I": 12, "II": 4, "III": 6})
    chuyen_de: list[str] = Field(default_factory=list)  # [] = mọi chuyên đề
    ty_le_kho: dict[str, int] | None = None  # {"de": %, "tb": %, "kho": %}


class BaiLamRequest(BaseModel):
    bai_lam: dict


class NopBaiRequest(BaseModel):
    # None = nộp với bài làm đã autosave; có giá trị = cập nhật lần cuối rồi nộp.
    bai_lam: dict | None = None


# ---------- GV ----------

@router.post("", dependencies=_GV)
def tao_de(body: TaoDeRequest, current_user: CurrentUser, db: Session = Depends(get_db)):
    try:
        de = svc.tao_de(db, current_user.id, body.ten, body.thoi_gian_phut, body.cau_theo_phan)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"id": de.id, "ten": de.ten}


@router.get("", dependencies=[require_role(VaiTro.gv, VaiTro.admin, VaiTro.hs)])
def danh_sach_de(current_user: CurrentUser, db: Session = Depends(get_db)):
    if current_user.vai_tro == VaiTro.hs:
        hs = db.get(User, current_user.id)
        return svc.ds_de_hs(db, hs)
    return svc.ds_de_gv(db, current_user.id)


@router.post("/tron", dependencies=_GV)
def tron_de(body: TronDeRequest, current_user: CurrentUser, db: Session = Depends(get_db)):
    """GĐ2 — trộn đề tự động theo ma trận (số câu/phần + tỉ lệ Dễ-TB-Khó + chuyên đề).
    Chỉ trả ĐỀ XUẤT danh sách câu — GV xem/chỉnh trong form rồi mới tạo đề."""
    tong = sum(max(0, v) for v in body.so_cau.values())
    if tong == 0:
        raise HTTPException(status_code=400, detail="Số câu phải lớn hơn 0")
    if tong > 100:
        raise HTTPException(status_code=400, detail="Tối đa 100 câu mỗi đề")
    return svc.tron_de(db, current_user.id, body.so_cau, body.chuyen_de, body.ty_le_kho)


@router.get("/{de_id}/chi-tiet-gv", dependencies=_GV)
def chi_tiet_de_gv(de_id: int, current_user: CurrentUser, db: Session = Depends(get_db)):
    de = db.get(DeThi, de_id)
    if de is None or de.nguoi_tao_id != current_user.id:
        raise HTTPException(status_code=404, detail="Đề không tồn tại")
    problems = {p.id: p for p in db.query(Problem).filter(
        Problem.id.in_([c.problem_id for c in de.cau_list])).all()}
    return {
        "id": de.id, "ten": de.ten, "thoi_gian_phut": de.thoi_gian_phut,
        "phat_hanh": de.phat_hanh, "diem_toi_da": svc.diem_toi_da_cua(de),
        "cau_list": [{
            "de_thi_cau_id": c.id, "problem_id": c.problem_id, "phan": c.phan,
            "thu_tu": c.thu_tu,
            "de_bai": problems[c.problem_id].de_bai if c.problem_id in problems else "",
            "do_kho": problems[c.problem_id].do_kho.value if c.problem_id in problems else "",
        } for c in de.cau_list],
    }


@router.patch("/{de_id}/phat-hanh", dependencies=_GV)
def phat_hanh(de_id: int, body: PhatHanhRequest, current_user: CurrentUser,
              db: Session = Depends(get_db)):
    try:
        de = svc.dat_phat_hanh(
            db, current_user.id, de_id, body.phat_hanh,
            pham_vi=body.pham_vi, lop_ids=body.lop_ids, hoc_sinh_ids=body.hoc_sinh_ids,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"id": de.id, "phat_hanh": de.phat_hanh, "pham_vi": de.pham_vi}


@router.delete("/{de_id}", dependencies=_GV)
def xoa_de(de_id: int, current_user: CurrentUser, db: Session = Depends(get_db)):
    try:
        svc.xoa_de(db, current_user.id, de_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"da_xoa": True}


@router.get("/{de_id}/ket-qua-lop", dependencies=_GV)
def ket_qua_lop(de_id: int, current_user: CurrentUser, db: Session = Depends(get_db)):
    try:
        return svc.ket_qua_lop(db, current_user.id, de_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ---------- HS ----------

@router.post("/{de_id}/bat-dau", dependencies=_HS)
def bat_dau(de_id: int, current_user: CurrentUser, db: Session = Depends(get_db)):
    hs = db.get(User, current_user.id)
    try:
        bai = svc.bat_dau_thi(db, hs, de_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _trang_thai_bai(db, bai.id, current_user.id)


@router.get("/bai/{bai_id}", dependencies=_HS)
def xem_bai(bai_id: int, current_user: CurrentUser, db: Session = Depends(get_db)):
    return _trang_thai_bai(db, bai_id, current_user.id)


@router.patch("/bai/{bai_id}/luu", dependencies=_HS)
def luu_bai(bai_id: int, body: BaiLamRequest, current_user: CurrentUser,
            db: Session = Depends(get_db)):
    try:
        bai = svc.luu_bai_lam(db, current_user.id, bai_id, body.bai_lam)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"trang_thai": bai.trang_thai.value}


@router.post("/bai/{bai_id}/nop", dependencies=_HS)
def nop_bai(bai_id: int, current_user: CurrentUser,
            body: NopBaiRequest | None = None, db: Session = Depends(get_db)):
    try:
        bai = svc.nop_bai(db, current_user.id, bai_id,
                          body.bai_lam if body is not None else None)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _trang_thai_bai(db, bai.id, current_user.id)


def _trang_thai_bai(db: Session, bai_id: int, hs_id: int) -> dict:
    """Trạng thái bài thi cho HS — đang thi: đề đã lọc đáp án + giờ còn lại;
    đã nộp: kết quả đầy đủ kèm đáp án đúng từng câu."""
    try:
        bai, de = svc._bai_cua_hs(db, hs_id, bai_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    # Đang thi nhưng đã quá hạn → chốt luôn trước khi trả (đồng hồ server quyết định).
    if bai.trang_thai == TrangThaiBaiThi.dang_thi and svc._now() > svc._het_han_luc(bai, de):
        svc._cham_va_nop(db, bai, de)

    dang_cd = _lay_dang_cd_map(db)
    problems = {p.id: p for p in db.query(Problem).filter(
        Problem.id.in_([c.problem_id for c in de.cau_list])).all()}

    goc = {
        "bai_thi_id": bai.id, "de_thi_id": de.id, "ten_de": de.ten,
        "thoi_gian_phut": de.thoi_gian_phut, "trang_thai": bai.trang_thai.value,
        "diem_toi_da": svc.diem_toi_da_cua(de),
    }

    if bai.trang_thai == TrangThaiBaiThi.dang_thi:
        con_giay = int((svc._han_hien_thi(bai, de) - svc._now()).total_seconds())
        return {
            **goc,
            "con_lai_giay": max(0, con_giay),
            "bai_lam": bai.bai_lam or {},
            "cau_list": [{
                "de_thi_cau_id": c.id, "phan": c.phan, "thu_tu": c.thu_tu,
                "problem": _strip_answers(problems[c.problem_id], dang_cd),
            } for c in de.cau_list if c.problem_id in problems],
        }

    # Đã nộp: kết quả + đáp án đúng (cùng triết lý "xem lại sau hoàn thành").
    ct_map = {ct["de_thi_cau_id"]: ct for ct in (bai.chi_tiet or [])}
    cau_kq = []
    for c in de.cau_list:
        p = problems.get(c.problem_id)
        if p is None:
            continue
        meta = p.meta or {}
        if p.loai_cau.value == "TN4PA":
            dap_an = {"dap_an_dung": meta.get("dap_an_dung")}
        elif p.loai_cau.value == "TNDS":
            dap_an = {"dap_an_y": {y["ky_hieu"]: y["dap_an"] for y in meta.get("y", [])}}
        else:
            dap_an = {"dap_an_cuoi": str(meta.get("dap_an_cuoi", ""))}
        cau_kq.append({
            "de_thi_cau_id": c.id, "phan": c.phan, "thu_tu": c.thu_tu,
            "problem": _strip_answers(p, dang_cd),
            "dap_an_nhap": (bai.bai_lam or {}).get(str(c.id)),
            "dap_an_dung": dap_an,
            **{k: ct_map.get(c.id, {}).get(k) for k in ("dung", "diem", "diem_toi_da", "da_tra_loi")},
        })
    return {
        **goc,
        "diem": bai.diem,
        "nop_luc": bai.nop_luc.isoformat() if bai.nop_luc else None,
        "cau_list": cau_kq,
    }
