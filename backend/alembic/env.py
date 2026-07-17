from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

# Đăng ký TẤT CẢ model với Base.metadata trước khi autogenerate so sánh — danh sách import
# này phải khớp app/db/init_db.py (nguồn import model duy nhất khác của dự án).
import app.models.cauhinh  # noqa: F401,E402
import app.models.cot_moc  # noqa: F401,E402
import app.models.danh_muc  # noqa: F401,E402
import app.models.de_thi  # noqa: F401,E402
import app.models.flag  # noqa: F401,E402
import app.models.llm_su_dung  # noqa: F401,E402
import app.models.lop  # noqa: F401,E402
import app.models.muc_tieu  # noqa: F401,E402
import app.models.nhiem_vu  # noqa: F401,E402
import app.models.phan_tich  # noqa: F401,E402
import app.models.problem  # noqa: F401,E402
import app.models.progress  # noqa: F401,E402
import app.models.session  # noqa: F401,E402
import app.models.solution_step  # noqa: F401,E402
import app.models.thong_bao  # noqa: F401,E402
import app.models.tom_tat_ly_thuyet  # noqa: F401,E402
import app.models.turn  # noqa: F401,E402
import app.models.user  # noqa: F401,E402
import app.models.yeu_cau_tro_giup  # noqa: F401,E402
from alembic import context
from app.config import settings
from app.db.base import Base

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# DATABASE_URL luôn đọc từ env (app.config.settings) — KHÔNG hard-code/duplicate trong
# alembic.ini, để chỉ có 1 nguồn sự thật giống mọi nơi khác trong dự án.
config.set_main_option("sqlalchemy.url", settings.database_url)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
# disable_existing_loggers=False: mặc định fileConfig() XÓA SẠCH mọi logging handler đã có
# (kể cả pytest caplog) — vỡ test chạy SAU trong cùng tiến trình vì chay_migration() gọi
# hàm này mỗi lần Alembic chạy (không chỉ lúc gõ lệnh CLI).
if config.config_file_name is not None:
    fileConfig(config.config_file_name, disable_existing_loggers=False)

target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
