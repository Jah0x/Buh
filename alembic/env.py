from __future__ import annotations
import os
from logging.config import fileConfig
from alembic import context
from sqlalchemy import create_engine, pool
from app.database.base import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def _db_url() -> str:
    v = os.getenv("DATABASE_URL")
    if v:
        return v
    v = config.get_main_option("sqlalchemy.url")
    if v:
        return v
    return "sqlite+aiosqlite:///./data/buh.db"

def _sync_url(url: str) -> str:
    if url.startswith("sqlite+aiosqlite"):
        return url.replace("sqlite+aiosqlite", "sqlite")
    if url.startswith("postgresql+asyncpg"):
        return url.replace("postgresql+asyncpg", "postgresql")
    return url

def run_migrations_offline() -> None:
    url = _db_url()
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True, compare_type=True, dialect_opts={"paramstyle": "named"})
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    url = _db_url()
    engine = create_engine(_sync_url(url), poolclass=pool.NullPool)
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
