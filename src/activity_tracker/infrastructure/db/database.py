"""Подключение к БД и запуск миграций Alembic."""

from __future__ import annotations

import os
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker

MIGRATIONS_DIR = Path(__file__).parent / "migrations"
DB_URL_ENV = "ACTIVITY_TRACKER_DB_URL"


def default_db_url() -> str:
    """URL из переменной окружения или файл ~/.activity_tracker/tracker.db."""
    if url := os.environ.get(DB_URL_ENV):
        return url
    path = Path.home() / ".activity_tracker" / "tracker.db"
    path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{path}"


def make_engine(url: str) -> Engine:
    engine = create_engine(url)
    if engine.dialect.name == "sqlite":

        @event.listens_for(engine, "connect")
        def _enable_foreign_keys(dbapi_connection, _record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine


def make_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False)


def alembic_config(url: str) -> Config:
    config = Config()
    config.set_main_option("script_location", str(MIGRATIONS_DIR))
    config.set_main_option("sqlalchemy.url", url.replace("%", "%%"))
    return config


def upgrade_to_head(url: str) -> None:
    command.upgrade(alembic_config(url), "head")
