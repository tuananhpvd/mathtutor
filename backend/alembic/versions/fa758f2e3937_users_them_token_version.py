"""users them token_version

Revision ID: fa758f2e3937
Revises: 040595cbe601
Create Date: 2026-07-25 07:50:33.663412

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fa758f2e3937'
down_revision: Union[str, Sequence[str], None] = '040595cbe601'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # server_default='0' BẮT BUỘC (autogenerate bỏ sót): thêm cột NOT NULL vào bảng users đã
    # có sẵn dữ liệu (production) mà không có default sẽ lỗi ngay — mọi tài khoản cũ nhận
    # token_version=0, khớp đúng token đời trước (không mang claim 'tv' → coi như 0), nên KHÔNG
    # ai bị đá văng lúc deploy; chỉ hết hiệu lực khi thật sự đổi mật khẩu/khóa tài khoản sau này.
    op.add_column(
        'users',
        sa.Column('token_version', sa.Integer(), nullable=False, server_default='0'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'token_version')
