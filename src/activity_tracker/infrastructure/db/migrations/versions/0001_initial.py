"""projects and entries

Revision ID: 0001
Revises:
Create Date: 2026-11-23
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_projects"),
        sa.UniqueConstraint("name", name="uq_projects_name"),
    )
    op.create_table(
        "entries",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=True),
        sa.Column("kind", sa.String(length=20), nullable=False),
        sa.Column("comment", sa.Text(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("ended_at", sa.DateTime(), nullable=False),
        sa.Column("answered_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["project_id"], ["projects.id"], name="fk_entries_project_id_projects"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_entries"),
    )
    op.create_index("ix_entries_project_id", "entries", ["project_id"])
    op.create_index("ix_entries_started_at", "entries", ["started_at"])


def downgrade() -> None:
    op.drop_index("ix_entries_started_at", table_name="entries")
    op.drop_index("ix_entries_project_id", table_name="entries")
    op.drop_table("entries")
    op.drop_table("projects")
