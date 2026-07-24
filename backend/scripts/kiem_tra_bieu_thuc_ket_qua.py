"""Chẩn đoán CHỈ ĐỌC: quét toàn bộ "bieu_thuc_ket_qua" trong CSDL, báo bước nào KHÔNG parse
được bằng CAS — lỗi này khiến hệ thống chấm sai/luôn báo "không phân tích được" dù học sinh
nhập đúng tuyệt đối (xem PROGRESS.md v142). KHÔNG sửa/xóa gì, chỉ in ra để GV/Admin tự sửa
qua giao diện "Sửa câu hỏi".

Chạy từ thư mục backend/, trỏ vào DB muốn quét qua biến môi trường DATABASE_URL:

    # Local (dev.db mặc định, không cần set biến môi trường):
    .venv\\Scripts\\python.exe scripts\\kiem_tra_bieu_thuc_ket_qua.py

    # Production (copy đúng "External Database URL" từ Render dashboard):
    DATABASE_URL="postgresql://...External Database URL từ Render..." \\
        .venv\\Scripts\\python.exe scripts\\kiem_tra_bieu_thuc_ket_qua.py
"""

import app.main  # noqa: F401 — đăng ký đủ mọi model trước khi query (tránh lỗi mapper)
from app.core.matching.cas import buoc_co_bieu_thuc_khong_hop_le
from app.db.session import SessionLocal
from app.models.problem import Problem


def main() -> None:
    db = SessionLocal()
    try:
        problems = db.query(Problem).all()
        tong_loi = 0
        for p in problems:
            steps = [
                {
                    "thu_tu": s.thu_tu,
                    "pham_vi": s.pham_vi,
                    "bieu_thuc_ket_qua": s.bieu_thuc_ket_qua,
                }
                for s in p.solution_steps
            ]
            loi = buoc_co_bieu_thuc_khong_hop_le(steps)
            if loi:
                tong_loi += len(loi)
                print(f"\n=== Câu hỏi #{p.id} ({p.loai_cau.value}, {p.trang_thai_duyet.value}) ===")
                print(f"  Đề bài: {(p.de_bai or '')[:80]}")
                for dong in loi:
                    print(f"  - {dong}")

        print(f"\nTổng: {len(problems)} câu hỏi, {tong_loi} bước có bieu_thuc_ket_qua hỏng.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
