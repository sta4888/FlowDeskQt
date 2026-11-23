"""Описание таблиц и императивный маппинг доменных классов.

Доменные классы остаются чистыми: SQLAlchemy "прикручивается" к ним здесь,
а не наоборот.
"""

from __future__ import annotations

from sqlalchemy import (
    Column, DateTime, Enum, ForeignKey, Index, Integer, MetaData, String, Table, Text,
    UniqueConstraint,
)
from sqlalchemy.orm import registry

from activity_tracker.domain.model import ActivityEntry, ActivityKind, Project

# Явные имена ограничений нужны Alembic (особенно для batch-режима в SQLite)
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=NAMING_CONVENTION)

projects_table = Table(
    "projects",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", String(100), nullable=False),
    Column("created_at", DateTime, nullable=False),
    UniqueConstraint("name"),
)

entries_table = Table(
    "entries",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("project_id", Integer, ForeignKey("projects.id"), nullable=True),
    Column(
        "kind",
        Enum(
            ActivityKind,
            native_enum=False,
            length=20,
            validate_strings=True,
            values_callable=lambda enum: [member.value for member in enum],
        ),
        nullable=False,
    ),
    Column("comment", Text, nullable=False),
    Column("started_at", DateTime, nullable=False),
    Column("ended_at", DateTime, nullable=False),
    Column("answered_at", DateTime, nullable=False),
    Index("ix_entries_project_id", "project_id"),
    Index("ix_entries_started_at", "started_at"),
)

mapper_registry = registry(metadata=metadata)
_mapped = False


def start_mappers() -> None:
    """Идемпотентно: можно вызывать из приложения и из тестов."""
    global _mapped
    if _mapped:
        return
    mapper_registry.map_imperatively(Project, projects_table)
    mapper_registry.map_imperatively(ActivityEntry, entries_table)
    _mapped = True
