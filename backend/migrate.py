#!/usr/bin/env python3
"""
migrate.py — Di chuyển toàn bộ dữ liệu từ SQLite (local) sang PostgreSQL (server).

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
HƯỚNG DẪN SỬ DỤNG
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Bước 1 — Chạy trên MÁY LOCAL để xuất dữ liệu:
    cd backend
    python migrate.py export

    → tạo ra file  backup_data.json  (~vài trăm KB)

Bước 2 — Upload file lên server:
    scp backup_data.json user@server:/duong/dan/backend/

Bước 3 — Chạy trên SERVER để nhập vào PostgreSQL:
    cd /duong/dan/backend
    python migrate.py import --db "postgresql://user:password@localhost:5432/ten_database"

    Ví dụ thực tế:
    python migrate.py import --db "postgresql://mathtutor:abc123@localhost/mathtutor_db"

Lưu ý:
  - Bước 3 yêu cầu đã cài requirements.txt trên server (pip install -r requirements.txt).
  - Database PostgreSQL phải tồn tại trước (createdb mathtutor_db).
  - Script tự tạo tất cả bảng, không cần chạy migration riêng.
  - Nếu database đã có dữ liệu, script sẽ hỏi xác nhận trước khi ghi đè.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import argparse
import io
import json
import sys
from pathlib import Path

# Đảm bảo stdout/stderr hỗ trợ UTF-8 (Windows terminal mặc định cp1252)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

BACKUP_FILE = Path(__file__).parent / "backup_data.json"

# Thứ tự import: cha trước con (xử lý riêng vòng users↔lop)
TABLES = [
    "cau_hinh",
    "chuyen_de",       # nguoi_tao_id → users (nullable, insert NULL trước)
    "users",           # lop_id → lop (nullable, insert NULL trước)
    "lop",             # gv_id → users (đã có)
    "dang",            # chuyen_de_id + nguoi_tao_id
    "problems",        # dang_id + nguoi_tao_id
    "solution_steps",  # problem_id
    "sessions",        # hoc_sinh_id + problem_id
    "turns",           # session_id
    "progress",        # hoc_sinh_id
    "flags",           # session_id (nullable) + turn_id (nullable)
    "phan_tich_hs",    # hoc_sinh_id
    "yeu_cau_dat_lai", # cột cũ, giữ lại để tương thích
]

# Cột JSON: SQLite lưu dạng chuỗi → cần parse thành dict/list khi import
JSON_COLS: dict[str, list[str]] = {
    "cau_hinh":      ["gia_tri"],
    "problems":      ["meta"],
    "sessions":      ["trang_thai_y", "thoi_gian_y"],
    "solution_steps": ["danh_sach_goi_y"],
    "turns":         ["ket_qua_so_khop"],
}


# ─────────────────────────────────────────────
# EXPORT
# ─────────────────────────────────────────────

def cmd_export(db_path: str) -> None:
    import sqlite3

    p = Path(db_path)
    if not p.exists():
        sys.exit(f"\n❌ Không tìm thấy file SQLite: {p.resolve()}")

    print(f"\n📦 Xuất dữ liệu từ {p.name} ...\n")

    conn = sqlite3.connect(p)
    conn.row_factory = sqlite3.Row
    data: dict[str, list] = {}
    total = 0

    for table in TABLES:
        try:
            rows = [dict(r) for r in conn.execute(f"SELECT * FROM {table}").fetchall()]
            data[table] = rows
            total += len(rows)
            print(f"  ✓  {table:<28} {len(rows):>6} bản ghi")
        except Exception:
            data[table] = []
            print(f"  –  {table:<28}  (bảng chưa tồn tại, bỏ qua)")

    conn.close()

    BACKUP_FILE.write_text(
        json.dumps(data, default=str, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    size_kb = BACKUP_FILE.stat().st_size / 1024
    print(f"\n✅ Xuất xong: {total} bản ghi → {BACKUP_FILE.name} ({size_kb:.1f} KB)")
    print("\n👉 Bước tiếp theo:")
    print(f"   1. Upload file  {BACKUP_FILE.name}  lên server")
    print('   2. Trên server chạy: python migrate.py import --db "postgresql://..."')


# ─────────────────────────────────────────────
# IMPORT
# ─────────────────────────────────────────────

def _parse_json_cols(rows: list[dict], table: str) -> list[dict]:
    """Parse cột JSON từ chuỗi SQLite thành dict/list."""
    cols = JSON_COLS.get(table, [])
    if not cols:
        return rows
    result = []
    for row in rows:
        r = dict(row)
        for col in cols:
            val = r.get(col)
            if isinstance(val, str):
                try:
                    r[col] = json.loads(val)
                except (json.JSONDecodeError, TypeError):
                    pass
        result.append(r)
    return result


def _insert_table(conn, table: str, rows: list[dict], skip_cols: set[str] | None = None) -> int:
    """Insert danh sách rows vào bảng, bỏ qua các cột trong skip_cols."""
    import sqlalchemy as sa

    if not rows:
        return 0

    rows = _parse_json_cols(rows, table)
    skip = skip_cols or set()

    ok = 0
    for row in rows:
        cols = {k: v for k, v in row.items() if k not in skip}
        if not cols:
            continue
        col_str = ", ".join(f'"{k}"' for k in cols)
        val_str = ", ".join(f":{k}" for k in cols)
        sql = sa.text(f'INSERT INTO {table} ({col_str}) VALUES ({val_str})')
        conn.execute(sql, cols)
        ok += 1
    return ok


def _reset_sequences(conn) -> None:
    """Đặt lại sequence ID sau khi insert để tránh conflict khi tạo bản ghi mới."""
    import sqlalchemy as sa

    for table in TABLES:
        try:
            conn.execute(sa.text(
                f"SELECT setval("
                f"  pg_get_serial_sequence('{table}', 'id'), "
                f"  COALESCE(MAX(id), 0) + 1, false"
                f") FROM {table}"
            ))
        except Exception:
            pass  # Bảng không tồn tại hoặc không có cột id


def cmd_import(db_url: str) -> None:
    import sqlalchemy as sa

    # Thêm thư mục backend vào path để import models
    sys.path.insert(0, str(Path(__file__).parent))

    # Import toàn bộ models để đăng ký với Base
    import app.models.cauhinh          # noqa: F401
    import app.models.danh_muc         # noqa: F401
    import app.models.flag             # noqa: F401
    import app.models.lop              # noqa: F401
    import app.models.phan_tich        # noqa: F401
    import app.models.problem          # noqa: F401
    import app.models.progress         # noqa: F401
    import app.models.session          # noqa: F401
    import app.models.solution_step    # noqa: F401
    import app.models.turn             # noqa: F401
    import app.models.user             # noqa: F401
    import app.models.yeu_cau_dat_lai  # noqa: F401
    from app.db.base import Base

    if not BACKUP_FILE.exists():
        sys.exit(
            f"\n❌ Không tìm thấy {BACKUP_FILE.name}\n"
            "   Chạy export trên máy local trước: python migrate.py export"
        )

    data: dict[str, list] = json.loads(BACKUP_FILE.read_text(encoding="utf-8"))
    total_records = sum(len(v) for v in data.values())

    print(f"\n📥 Chuẩn bị nhập {total_records} bản ghi vào PostgreSQL ...")
    print(f"   Database: {db_url.split('@')[-1]}\n")  # Ẩn password trong log

    engine = sa.create_engine(db_url)

    # Kiểm tra database đã có dữ liệu chưa
    try:
        with engine.connect() as conn:
            user_count = conn.execute(sa.text("SELECT COUNT(*) FROM users")).scalar()
        if user_count and user_count > 0:
            print(f"⚠️  Database đã có {user_count} tài khoản.")
            ans = input("   Tiếp tục sẽ ghi đè toàn bộ dữ liệu. Xác nhận? (yes/no): ").strip()
            if ans.lower() not in ("yes", "y"):
                sys.exit("Đã hủy.")
            # Xóa dữ liệu cũ theo thứ tự ngược (con trước cha)
            print("\n🗑️  Xóa dữ liệu cũ...")
            _truncate_all(engine)
    except Exception:
        pass  # Bảng chưa tồn tại → tạo mới bên dưới

    # Tạo cấu trúc bảng
    print("📐 Tạo cấu trúc bảng...")
    Base.metadata.create_all(engine)

    print("\n   Đang nhập...\n")
    total = 0

    with engine.begin() as conn:

        # 1. cau_hinh — không FK
        n = _insert_table(conn, "cau_hinh", data.get("cau_hinh", []))
        _log(n, "cau_hinh"); total += n

        # 2. chuyen_de — nguoi_tao_id nullable → insert NULL, cập nhật sau
        n = _insert_table(conn, "chuyen_de", data.get("chuyen_de", []),
                          skip_cols={"nguoi_tao_id"})
        _log(n, "chuyen_de"); total += n

        # 3. users — lop_id nullable → insert NULL, cập nhật sau
        user_rows = data.get("users", [])
        user_lop_map = {r["id"]: r.get("lop_id") for r in user_rows}
        n = _insert_table(conn, "users", user_rows, skip_cols={"lop_id"})
        _log(n, "users"); total += n

        # 4. lop — gv_id references users (đã có)
        n = _insert_table(conn, "lop", data.get("lop", []))
        _log(n, "lop"); total += n

        # 5. Cập nhật users.lop_id (giải quyết vòng users↔lop)
        updated = 0
        for uid, lop_id in user_lop_map.items():
            if lop_id is not None:
                conn.execute(
                    sa.text('UPDATE users SET lop_id = :lop_id WHERE id = :id'),
                    {"lop_id": lop_id, "id": uid},
                )
                updated += 1
        if updated:
            print(f"  ↺  users.lop_id cập nhật        {updated:>6} bản ghi")

        # 6. Cập nhật chuyen_de.nguoi_tao_id
        for row in data.get("chuyen_de", []):
            if row.get("nguoi_tao_id") is not None:
                conn.execute(
                    sa.text('UPDATE chuyen_de SET nguoi_tao_id = :tid WHERE id = :id'),
                    {"tid": row["nguoi_tao_id"], "id": row["id"]},
                )

        # 7. dang
        n = _insert_table(conn, "dang", data.get("dang", []))
        _log(n, "dang"); total += n

        # 8. problems
        n = _insert_table(conn, "problems", data.get("problems", []))
        _log(n, "problems"); total += n

        # 9. solution_steps
        n = _insert_table(conn, "solution_steps", data.get("solution_steps", []))
        _log(n, "solution_steps"); total += n

        # 10. sessions
        n = _insert_table(conn, "sessions", data.get("sessions", []))
        _log(n, "sessions"); total += n

        # 11. turns
        n = _insert_table(conn, "turns", data.get("turns", []))
        _log(n, "turns"); total += n

        # 12. progress
        n = _insert_table(conn, "progress", data.get("progress", []))
        _log(n, "progress"); total += n

        # 13. flags
        n = _insert_table(conn, "flags", data.get("flags", []))
        _log(n, "flags"); total += n

        # 14. phan_tich_hs
        n = _insert_table(conn, "phan_tich_hs", data.get("phan_tich_hs", []))
        _log(n, "phan_tich_hs"); total += n

        # 15. yeu_cau_dat_lai (bảng cũ, có thể rỗng)
        n = _insert_table(conn, "yeu_cau_dat_lai", data.get("yeu_cau_dat_lai", []))
        if n: _log(n, "yeu_cau_dat_lai"); total += n

        # Reset sequences để INSERT tiếp theo không bị lỗi duplicate ID
        print("\n  🔄 Reset sequences ID...")
        _reset_sequences(conn)

    print(f"\n✅ Hoàn thành! Đã nhập {total} bản ghi vào PostgreSQL.")
    print("   Hệ thống sẵn sàng sử dụng — không cần tạo lại dữ liệu.\n")


def _log(n: int, table: str) -> None:
    if n > 0:
        print(f"  ✓  {table:<28} {n:>6} bản ghi")
    else:
        print(f"  –  {table:<28}       (rỗng)")


def _truncate_all(engine) -> None:
    """Xóa toàn bộ dữ liệu theo thứ tự ngược để tránh FK violation."""
    import sqlalchemy as sa

    reverse = list(reversed(TABLES))
    with engine.begin() as conn:
        for table in reverse:
            try:
                conn.execute(sa.text(f"TRUNCATE TABLE {table} CASCADE"))
            except Exception:
                pass


# ─────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="MathTutor — Di chuyển dữ liệu SQLite → PostgreSQL",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_ex = sub.add_parser("export", help="Xuất SQLite → backup_data.json (chạy local)")
    p_ex.add_argument(
        "--db", default="dev.db",
        help="Đường dẫn file SQLite (mặc định: dev.db)",
    )

    p_im = sub.add_parser("import", help="Nhập backup_data.json → PostgreSQL (chạy server)")
    p_im.add_argument(
        "--db", required=True, metavar="URL",
        help='PostgreSQL URL, ví dụ: "postgresql://user:pass@localhost/dbname"',
    )

    args = parser.parse_args()

    if args.cmd == "export":
        cmd_export(args.db)
    else:
        cmd_import(args.db)


if __name__ == "__main__":
    main()
