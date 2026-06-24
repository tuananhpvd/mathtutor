from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.admin import router as admin_api_router
from app.api.auth import admin_router, gv_router, hs_router
from app.api.auth import router as auth_router
from app.api.danh_muc import router as danh_muc_router
from app.api.monitor import router as monitor_router
from app.api.problems import router as problems_router
from app.api.progress import router as progress_router
from app.api.questions_ai import router as questions_ai_router
from app.api.sessions import router as sessions_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.db.init_db import init_db

    init_db()
    yield


app = FastAPI(title="MathTutor API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "MathTutor"}
