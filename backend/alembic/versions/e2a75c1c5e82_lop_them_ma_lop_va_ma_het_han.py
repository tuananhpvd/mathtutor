"""lop them ma_lop va ma_het_han

Mã mời lớp để HS TỰ đăng ký vào đúng lớp (mức 1 lộ trình gỡ nút thắt triển khai).

Ghi chú khi review (đã sửa tay so với bản autogenerate):
- Autogenerate còn bắt thêm 2 thay đổi NGOÀI phạm vi, do model đã lệch dev.db từ trước:
  `tom_tat_ly_thuyet.noi_dung` JSON→Text và FK `yeu_cau_tro_giup.turn_id`. ĐÃ BỎ — không
  gộp drift lạ vào migration tính năng (sẽ rewrite bảng trên production một cách vô cớ, và
  `create_foreign_key(None, ...)` cũng không chạy được trên SQLite).
- Autogenerate sinh `app.db.types.UTCDateTime()` mà THIẾU import → đã thêm import.
- Dùng unique INDEX (không phải unique CONSTRAINT): SQLite không ALTER thêm constraint mà
  không rebuild bảng. Nhiều NULL vẫn hợp lệ trong unique index ở cả SQLite lẫn Postgres —
  đúng ý đồ "hầu hết lớp chưa có mã".

Revision ID: e2a75c1c5e82
Revises: 0e5e53d3e3b3
Create Date: 2026-07-20 18:20:03.915934

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

import app.db.types

# revision identifiers, used by Alembic.
revision: str = 'e2a75c1c5e82'
down_revision: Union[str, Sequence[str], None] = '0e5e53d3e3b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('lop', sa.Column('ma_lop', sa.String(length=16), nullable=True))
    op.add_column('lop', sa.Column('ma_het_han', app.db.types.UTCDateTime(), nullable=True))
    op.create_index(op.f('ix_lop_ma_lop'), 'lop', ['ma_lop'], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_lop_ma_lop'), table_name='lop')
    op.drop_column('lop', 'ma_het_han')
    op.drop_column('lop', 'ma_lop')
