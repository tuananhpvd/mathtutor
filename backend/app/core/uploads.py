"""Lưu ảnh minh họa câu hỏi. Kiểm tra bằng magic bytes (không phụ thuộc Pillow).

Chỉ chấp nhận PNG/JPG/WebP, tối đa 3MB. Ảnh lưu ở backend/uploads/ với tên ngẫu nhiên
(uuid) chống trùng/đoán, phục vụ qua StaticFiles mount /uploads.
"""

import uuid
from pathlib import Path

# app/core/uploads.py -> parents[2] = backend/
UPLOADS_DIR = Path(__file__).resolve().parents[2] / "uploads"
MAX_BYTES = 3 * 1024 * 1024  # 3MB


def _duoi_theo_magic(data: bytes) -> str | None:
    """Suy phần mở rộng từ magic bytes; None nếu không phải PNG/JPG/WebP."""
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return ".png"
    if data[:3] == b"\xff\xd8\xff":
        return ".jpg"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return ".webp"
    return None


def luu_hinh(data: bytes) -> str:
    """Kiểm tra + lưu ảnh, trả URL tương đối /uploads/<file>.

    Raise ValueError (message tiếng Việt) nếu rỗng, quá lớn, hoặc không phải ảnh hợp lệ.
    Xác thực bằng nội dung (magic bytes), KHÔNG tin content-type từ client.
    """
    if not data:
        raise ValueError("File ảnh rỗng")
    if len(data) > MAX_BYTES:
        raise ValueError("Ảnh vượt quá 3MB")
    duoi = _duoi_theo_magic(data)
    if duoi is None:
        raise ValueError("Chỉ chấp nhận ảnh PNG, JPG hoặc WebP")
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    ten = f"{uuid.uuid4().hex}{duoi}"
    (UPLOADS_DIR / ten).write_bytes(data)
    return f"/uploads/{ten}"
