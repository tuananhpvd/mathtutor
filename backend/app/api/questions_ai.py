"""API AI sinh câu hỏi + GV duyệt (Phase 5)."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.deps import CurrentUser, co_toan_quyen, require_role
from app.db.session import get_db
from app.llm.client import KhongHoTroDocAnhError, get_llm_client
from app.models.problem import Nguon, Problem, TrangThaiDuyet
from app.models.thong_bao import LoaiThongBao
from app.models.user import VaiTro
from app.schemas.question_gen import (
    CauHoiNhapResponse,
    DocDeTuAnhRequest,
    DocDeTuAnhResponse,
    DuyetRequest,
    LuuBuocGoiYRequest,
    SinhCauHoiRequest,
    TaoBuocGoiYRequest,
)
from app.services import thong_bao_service
from app.services.admin_service import lay_cau_hinh
from app.services.llm_quota_service import LOAI_SINH_CAU_HOI, LOI_HET_QUOTA, ap_quota_tac_vu
from app.services.question_gen_service import (
    doc_de_tu_anh,
    duyet_cau,
    luu_cau_nhap,
    sinh_va_luu,
    tao_nhap_buoc_goi_y,
)

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
    cau_hinh = lay_cau_hinh(db)
    llm = ap_quota_tac_vu(db, cau_hinh, current_user.id, get_llm_client(cau_hinh),
                          LOAI_SINH_CAU_HOI)
    if llm is None:
        raise HTTPException(status_code=429, detail=LOI_HET_QUOTA)
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


@router.post("/tao-buoc-goi-y", dependencies=[require_role(VaiTro.gv, VaiTro.admin)])
def tao_buoc_goi_y_api(
    body: TaoBuocGoiYRequest,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    """AI tạo bước và gợi ý: GV viết đề bài (+ phương án/ý) sẵn, AI CHỈ giải + chia bước
    + viết gợi ý theo đúng cấu trúc GV yêu cầu. Trả bản NHÁP — chưa lưu DB."""
    if body.loai_cau not in {"TN4PA", "TNDS", "TLN"}:
        raise HTTPException(status_code=400, detail="loai_cau không hợp lệ")
    cau_hinh = lay_cau_hinh(db)
    llm = ap_quota_tac_vu(db, cau_hinh, current_user.id, get_llm_client(cau_hinh),
                          LOAI_SINH_CAU_HOI)
    if llm is None:
        raise HTTPException(status_code=429, detail=LOI_HET_QUOTA)
    try:
        ket_qua = tao_nhap_buoc_goi_y(db, body.model_dump(), llm)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:  # KHÔNG để lộ 500 — báo lỗi rõ ràng để GV thử lại
        raise HTTPException(
            status_code=502,
            detail="AI không tạo được bước/gợi ý hợp lệ (mô hình lỗi hoặc trả dữ liệu "
                   "không đúng). Vui lòng thử lại. Chi tiết: " + str(e)[:200],
        )
    return ket_qua


@router.post("/doc-de-tu-anh", response_model=DocDeTuAnhResponse,
             dependencies=[require_role(VaiTro.gv, VaiTro.admin)])
def doc_de_tu_anh_api(
    body: DocDeTuAnhRequest,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    """AI đọc ảnh GV dán, nhận dạng loại câu + trích đề bài/phương án/ý để điền vào form —
    CHƯA giải, CHƯA lưu. GV xem chữ AI đọc được, sửa nếu cần, rồi mới bấm "Tạo" như luồng thủ
    công. Nếu ảnh không khớp loai_cau_ky_vong, trả khop_loai_cau=False kèm lý do (không lỗi)."""
    if body.loai_cau_ky_vong not in {"TN4PA", "TNDS", "TLN"}:
        raise HTTPException(status_code=400, detail="loai_cau_ky_vong không hợp lệ")
    cau_hinh = lay_cau_hinh(db)
    llm = ap_quota_tac_vu(db, cau_hinh, current_user.id, get_llm_client(cau_hinh),
                          LOAI_SINH_CAU_HOI)
    if llm is None:
        raise HTTPException(status_code=429, detail=LOI_HET_QUOTA)
    try:
        ket_qua = doc_de_tu_anh(llm, body.anh_base64, body.mime_type, body.loai_cau_ky_vong)
    except KhongHoTroDocAnhError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:  # KHÔNG để lộ 500 — báo lỗi rõ ràng để GV thử lại
        raise HTTPException(
            status_code=502,
            detail="AI không đọc được ảnh (mô hình lỗi hoặc trả dữ liệu không đúng). "
                   "Vui lòng thử lại. Chi tiết: " + str(e)[:200],
        )
    return ket_qua


@router.post("/tao-buoc-goi-y/luu", dependencies=[require_role(VaiTro.gv, VaiTro.admin)])
def luu_buoc_goi_y_api(
    body: LuuBuocGoiYRequest,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    """Lưu bản nháp (đã xem/sửa) vào ngân hàng câu hỏi ở trạng thái chờ duyệt."""
    try:
        problem = luu_cau_nhap(db, body.cau, current_user.id)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Không lưu được câu hỏi: {str(e)[:200]}")
    return {"id": problem.id, "trang_thai_duyet": problem.trang_thai_duyet.value}


@router.get("/cho-duyet", dependencies=[require_role(VaiTro.gv, VaiTro.admin)])
def danh_sach_cho_duyet(current_user: CurrentUser, db: Session = Depends(get_db)):
    q = db.query(Problem).filter(
        Problem.nguon == Nguon.ai_sinh,
        Problem.trang_thai_duyet == TrangThaiDuyet.cho_duyet,
    )
    # GV chỉ thấy câu AI của mình; Admin thấy tất cả
    if current_user.vai_tro == VaiTro.gv:
        q = q.filter(Problem.nguoi_tao_id == current_user.id)
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
    p = db.get(Problem, problem_id)
    if p is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy câu hỏi")
    if not co_toan_quyen(current_user) and p.nguoi_tao_id != current_user.id:
        raise HTTPException(status_code=403, detail="Bạn không có quyền duyệt câu hỏi này")
    owner_id, ten_bai = p.nguoi_tao_id, p.de_bai
    try:
        problem = duyet_cau(db, problem_id, body.hanh_dong)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    # Quản lý duyệt/loại câu của GV khác → thông báo cho chủ.
    if co_toan_quyen(current_user) and owner_id and owner_id != current_user.id:
        nhan = "đã duyệt câu hỏi" if body.hanh_dong == "duyet" else "đã loại câu hỏi"
        thong_bao_service.tao(
            db, nguoi_nhan_id=owner_id, noi_dung=f"{current_user.ho_ten} {nhan}: {ten_bai}",
            loai=LoaiThongBao.quan_ly, nguoi_gui_id=current_user.id,
            tieu_de="Quản lý cập nhật nội dung",
        )
    return {"id": problem.id, "trang_thai_duyet": problem.trang_thai_duyet.value}
