from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.admin import router as admin_api_router
from app.api.auth import admin_router, gv_router, hs_router
from app.api.auth import router as auth_router
from app.api.danh_muc import router as danh_muc_router
from app.api.dat_lai import gv_router as dat_lai_gv_router
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
from app.core.uploads import UPLOADS_DIR


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.db.init_db import init_db
    from app.services import lich_phan_tich

    init_db()
    lich_phan_tich.khoi_dong()
    try:
        yield
    finally:
        await lich_phan_tich.dung()


app = FastAPI(title="MathTutor API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
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


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "MathTutor"}
