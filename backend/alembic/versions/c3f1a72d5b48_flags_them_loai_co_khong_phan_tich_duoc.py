"""flags them loai co khong_phan_tich_duoc

Revision ID: c3f1a72d5b48
Revises: b931a26780f4
Create Date: 2026-07-28 10:05:00.000000

VÌ SAO PHẢI VIẾT TAY (không autogenerate được):
`flags.loai_co` khai báo bằng sa.Enum(..., name='loaico'). Trên PostgreSQL (production) đó
là một NATIVE ENUM TYPE — thêm giá trị mới bắt buộc `ALTER TYPE ... ADD VALUE`, Alembic
autogenerate KHÔNG sinh ra lệnh này. Trên SQLite (dev/test) cột chỉ là VARCHAR(22) không có
CHECK constraint (đã kiểm DDL thật trong dev.db), nên không cần làm gì — giá trị mới ghi
được ngay. Giá trị mới 'khong_phan_tich_duoc' dài 20 ký tự, vẫn vừa VARCHAR(22) sẵn có
(chuỗi dài nhất hiện tại là 'noi_dung_khong_phu_hop' = 22), KHÔNG phải nới cột.
"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'c3f1a72d5b48'
down_revision: Union[str, Sequence[str], None] = 'b931a26780f4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Thêm 'khong_phan_tich_duoc' vào enum loaico (chỉ PostgreSQL cần).

    PHẢI chạy NGOÀI transaction (autocommit_block): Alembic mặc định bọc migration trong
    BEGIN/COMMIT, mà PostgreSQL < 12 CẤM `ALTER TYPE ... ADD VALUE` bên trong transaction
    block (lỗi cứng → app không khởi động được vì tự `alembic upgrade head` lúc start).
    autocommit_block() làm migration này an toàn trên MỌI phiên bản PostgreSQL, không phải
    phụ thuộc vào việc đoán phiên bản của production.
    """
    if op.get_bind().dialect.name == "postgresql":
        with op.get_context().autocommit_block():
            # IF NOT EXISTS để chạy lại migration không vỡ (PostgreSQL >= 9.5).
            op.execute("ALTER TYPE loaico ADD VALUE IF NOT EXISTS 'khong_phan_tich_duoc'")
    # SQLite: cột là VARCHAR không CHECK → no-op, không cần đụng schema.


def downgrade() -> None:
    """KHÔNG ĐẢO ĐƯỢC — cố ý để trống, KHÔNG PHẢI thiếu sót.

    PostgreSQL không có lệnh xóa một giá trị khỏi enum type; cách duy nhất là tạo type mới,
    chuyển cột sang, xóa type cũ — thao tác nặng và rủi ro hơn hẳn cái nó đảo lại, trong khi
    một giá trị enum thừa hoàn toàn vô hại (không hàng nào dùng tới sau khi hạ cấp code).

    Đây là NGOẠI LỆ CÓ CHỦ ĐÍCH với quy ước "test upgrade head / downgrade -1" ở CLAUDE.md
    mục 6: downgrade migration này chạy sạch nhưng không khôi phục nguyên trạng enum. Nếu thật
    sự cần gỡ giá trị, phải viết migration riêng theo cách tạo type mới nói trên.
    """
    pass
