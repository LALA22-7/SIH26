"""Alembic environment — uses synchronous psycopg2 connection for migrations."""
import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# Load all models so autogenerate can detect them
from app.models import Base  # noqa: F401 — side-effects matter

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# Override sqlalchemy.url from environment variable
database_sync_url = os.environ.get(
    "DATABASE_SYNC_URL",
    "postgresql+psycopg2://cyclone:cyclone_secret@localhost:5432/cyclonewatch",
)
config.set_main_option("sqlalchemy.url", database_sync_url)


def run_migrations_offline() -> None:
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
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
