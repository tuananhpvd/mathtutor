from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.admin import router as admin_api_router
from app.api.auth import admin_router, gv_router, hs_router
from app.api.auth import router as auth_router
from app.api.danh_muc import router as danh_muc_router
from app.api.dat_lai import gv_router as dat_lai_gv_router
from app.api.de_thi import router as de_thi_router
from app.api.gv import router as gv_api_router
from app.api.hs import router as hs_api_router
from app.api.monitor import router as monitor_router
from app.api.muc_tieu import router as muc_tieu_router
from app.api.nhiem_vu import router as nhiem_vu_router
from app.api.problems import router as problems_router
from app.api.progress import router as progress_router
from app.api.questions_ai import router as questions_ai_router
from app.api.sessions import router as sessions_router
from app.api.thong_bao import router as thong_bao_router
from app.api.tro_giup import router as tro_giup_router
from app.config import kiem_tra_an_toan_khoi_dong, settings
from app.core.uploads import UPLOADS_DIR
from app.db.session import get_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.db.init_db import init_db
    from app.services import lich_phan_tich

    kiem_tra_an_toan_khoi_dong()
    init_db()
    lich_phan_tich.khoi_dong()
    try:
        yield
    finally:
        await lich_phan_tich.dung()


app = FastAPI(title="MathTutor API", version="0.1.0", lifespan=lifespan)

_cors_origins = ["http://localhost:5173", "http://localhost:3000"]
_cors_origins += [o.strip() for o in settings.cors_extra_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Phục vụ ảnh minh họa câu hỏi đã upload (GV thêm ở form / import).
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")

app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(gv_router)
app.include_router(hs_router)
app.include_router(problems_router)
app.include_router(sessions_router)
app.include_router(monitor_router)
app.include_router(questions_ai_router)
app.include_router(progress_router)
app.include_router(admin_api_router)
app.include_router(danh_muc_router)
app.include_router(gv_api_router)
app.include_router(hs_api_router)
app.include_router(dat_lai_gv_router)
app.include_router(thong_bao_router)
app.include_router(tro_giup_router)
app.include_router(nhiem_vu_router)
app.include_router(muc_tieu_router)
app.include_router(de_thi_router)


@app.get("/api/health")
def health(db: Session = Depends(get_db)):
    """Uptime monitor cần phân biệt "app đứng" vs "app sống nhưng DB chết" — trước đây
    endpoint này lúc nào cũng trả 200 dù DB mất kết nối hoàn toàn."""
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False
    return JSONResponse(
        status_code=200 if db_ok else 503,
        content={"status": "ok" if db_ok else "db_loi", "service": "MathTutor", "db": db_ok},
    )


@app.get("/api/trang-thai-bao-tri")
def trang_thai_bao_tri(ma: str | None = None, db: Session = Depends(get_db)):
    """CÔNG KHAI (không cần đăng nhập) — frontend gọi lúc mở trang để biết có đang bật
    "sản phẩm đang hoàn thiện" hay không, và nếu có thì "ma" (query param) người dùng gửi
    có khớp mã xem trước (bao_tri_ma, đặt trong Cấu hình Admin) hay không.

    KHÔNG trả nguyên văn mã xem trước ra ngoài — chỉ trả true/false, tránh lộ mã qua việc
    đọc response."""
    from app.services.admin_service import lay_cau_hinh

    cau_hinh = lay_cau_hinh(db)
    bat = bool(cau_hinh.get("bao_tri_bat", False))
    hop_le = bat and bool(ma) and ma == str(cau_hinh.get("bao_tri_ma", ""))
    return {"bao_tri": bat, "hop_le": hop_le}
