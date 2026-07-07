"""Di chuyển 1 lần: copy dữ liệu từ SQLite local (dev.db) sang PostgreSQL production.

Ghi đè (TRUNCATE rồi nạp lại) các bảng liệt kê bên dưới trên DB đích — chỉ chạy
khi production chưa có dữ liệu thật cần giữ (vd mới deploy, chỉ có seed mặc định).

Chạy từ thư mục backend/:
    PROD_DATABASE_URL="postgresql://...External Database URL từ Render..." \
        ../.venv/Scripts/python.exe scripts/migrate_local_to_prod.py
"""

import os
from pathlib import Path

from sqlalchemy import MetaData, Table, create_engine, insert, select, text

BACKEND_DIR = Path(__file__).resolve().parent.parent
SOURCE_URL = f"sqlite:///{BACKEND_DIR / 'dev.db'}"
TARGET_URL = os.environ["PROD_DATABASE_URL"]

# Thứ tự chèn theo phụ thuộc khóa ngoại. users<->lop có phụ thuộc vòng
# (users.lop_id -> lop.id, lop.gv_id -> users.id) nên users được chèn
# trước với lop_id=NULL, cập nhật lại sau khi đã có lop.
TABLES_IN_ORDER = ["users", "lop", "chuyen_de", "dang", "problems", "solution_steps", "thong_bao"]


def main() -> None:
    src_engine = create_engine(SOURCE_URL)
    tgt_engine = create_engine(TARGET_URL)
    src_meta = MetaData()
    tgt_meta = MetaData()

    # Đọc cấu trúc bảng TRƯỚC khi mở transaction TRUNCATE, để tránh 1 kết nối
    # khác (dùng cho reflect) phải chờ khóa ACCESS EXCLUSIVE của TRUNCATE.
    print("Dang doc cau truc bang...", flush=True)
    for name in TABLES_IN_ORDER:
        Table(name, src_meta, autoload_with=src_engine)
        Table(name, tgt_meta, autoload_with=tgt_engine)
    print("Da doc xong cau truc bang.", flush=True)

    with src_engine.connect() as src_conn, tgt_engine.begin() as tgt_conn:
        tgt_conn.execute(text("SET lock_timeout = '10s'"))
        print("Dang TRUNCATE...", flush=True)
        tgt_conn.execute(
            text(f"TRUNCATE TABLE {', '.join(TABLES_IN_ORDER)} RESTART IDENTITY CASCADE")
        )
        print("TRUNCATE xong.", flush=True)

        users_lop_id: dict[int, int | None] = {}

        for name in TABLES_IN_ORDER:
            src_table = src_meta.tables[name]
            tgt_table = tgt_meta.tables[name]
            rows = [dict(r._mapping) for r in src_conn.execute(select(src_table))]

            if name == "users":
                for r in rows:
                    users_lop_id[r["id"]] = r.get("lop_id")
                    r["lop_id"] = None

            if rows:
                tgt_conn.execute(insert(tgt_table), rows)
            print(f"{name}: {len(rows)} dong", flush=True)

        for user_id, lop_id in users_lop_id.items():
            if lop_id is not None:
                tgt_conn.execute(
                    text("UPDATE users SET lop_id = :lop_id WHERE id = :user_id"),
                    {"lop_id": lop_id, "user_id": user_id},
                )

        # BẮT BUỘC: chèn thẳng "id" có sẵn (không qua nextval()) khiến sequence tự tăng của
        # Postgres KHÔNG biết mà cập nhật theo — nếu bỏ qua bước này, lần đầu app tự thêm dòng
        # mới (qua ORM, không chỉ định id) sẽ dùng lại đúng id đã tồn tại → UniqueViolation.
        print("Dang dong bo lai sequence...", flush=True)
        for name in TABLES_IN_ORDER:
            tgt_conn.execute(text(
                f"SELECT setval(pg_get_serial_sequence('{name}', 'id'), "
                f"(SELECT GREATEST(MAX(id), 1) FROM \"{name}\"))"
            ))
        print("Da dong bo sequence.", flush=True)

    print("Xong.")


if __name__ == "__main__":
    main()
