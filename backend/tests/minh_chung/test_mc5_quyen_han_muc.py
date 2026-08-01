"""
MC-5 — Ma trận kiểm thử quyền/hạn mức (thuyết minh Bảng 13, dòng "Quản trị - quyền/hạn mức").

KHÔNG viết test mới: 30 ca này đã tồn tại và chạy trong bộ 663 test chính (test_monitor_idor.py
+ test_sessions_idor.py + test_llm_quota.py + test_config_safety.py). Bài này CHẠY LẠI đúng 4
file đó qua subprocess pytest thật (không suy đoán "chắc chúng vẫn xanh" từ lần chạy suite
chính) để lấy kết quả PASS/FAIL từng ca, rồi gom thành ma trận cho thuyết minh.
"""

import re
import subprocess
import sys
from pathlib import Path

THU_MUC_BAO_CAO = Path(__file__).resolve().parents[3] / "docs" / "minh_chung"
THU_MUC_TESTS = Path(__file__).resolve().parents[1]

CAC_FILE = [
    ("test_monitor_idor.py", "Chống truy cập chéo dữ liệu (IDOR) — cờ/hội thoại/nhật ký GV"),
    ("test_sessions_idor.py", "Chống truy cập chéo dữ liệu (IDOR) — phiên học của HS"),
    ("test_llm_quota.py", "Hạn mức sử dụng AI theo HS/hệ thống + suy giảm khi hết hạn mức"),
    ("test_config_safety.py", "An toàn cấu hình bí mật (JWT_SECRET, DATABASE_URL production)"),
]

_RE_KET_QUA = re.compile(r"^(tests/minh_chung/\.\./)?(\S+\.py)::(\S+)\s+(PASSED|FAILED)")


def _chay_va_gom(files: list[str]) -> list[dict]:
    duong_dan = [str(THU_MUC_TESTS / f) for f in files]
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", *duong_dan, "-v", "--tb=short", "--no-header"],
        capture_output=True, text=True, cwd=str(THU_MUC_TESTS.parent.parent),
    )
    ket_qua = []
    for dong in proc.stdout.splitlines():
        # Dạng dòng pytest -v: "tests/test_xxx.py::test_yyy PASSED"
        m = re.match(r"^(\S+\.py)::(\S+)\s+(PASSED|FAILED)", dong)
        if m:
            ket_qua.append({"file": m.group(1), "test": m.group(2), "ket_qua": m.group(3)})
    return ket_qua, proc.returncode, proc.stdout


def test_mc5_quyen_han_muc():
    ten_file = [f for f, _ in CAC_FILE]
    ket_qua, returncode, stdout_raw = _chay_va_gom(ten_file)

    assert ket_qua, f"Không parse được kết quả pytest — stdout:\n{stdout_raw[-3000:]}"

    so_pass = sum(1 for r in ket_qua if r["ket_qua"] == "PASSED")
    tong = len(ket_qua)

    THU_MUC_BAO_CAO.mkdir(parents=True, exist_ok=True)
    duong_dan_md = THU_MUC_BAO_CAO / "mc5_quyen_han_muc.md"
    with open(duong_dan_md, "w", encoding="utf-8") as f:
        f.write("# MC-5 — Ma trận kiểm thử quyền/hạn mức\n\n")
        f.write(f"**{so_pass}/{tong} ca đúng cấu hình** "
                f"(chạy lại thật qua subprocess pytest, không suy đoán).\n\n")
        for ten_f, mo_ta in CAC_FILE:
            cac_ca = [r for r in ket_qua if r["file"].endswith(ten_f)]
            so_pass_f = sum(1 for r in cac_ca if r["ket_qua"] == "PASSED")
            f.write(f"## `{ten_f}` — {mo_ta} ({so_pass_f}/{len(cac_ca)})\n\n")
            for r in cac_ca:
                bieu = "✅" if r["ket_qua"] == "PASSED" else "❌"
                f.write(f"- {bieu} `{r['test']}`\n")
            f.write("\n")

    assert so_pass == tong == 30, (
        f"MC-5 kỳ vọng đúng 30/30 ca (đây là test QUYỀN/BẢO MẬT đã có sẵn, không phải bộ đo "
        f"độ chính xác thống kê) — thực tế {so_pass}/{tong}, returncode={returncode}. "
        f"Xem {duong_dan_md}"
    )
