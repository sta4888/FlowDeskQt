from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import inspect

from activity_tracker.infrastructure.db.database import alembic_config, make_engine
from activity_tracker.infrastructure.db.orm import metadata


def test_upgrade_creates_tables_and_downgrade_removes_them(db_url):
    config = alembic_config(db_url)
    engine = make_engine(db_url)

    command.upgrade(config, "head")
    assert {"projects", "entries"} <= set(inspect(engine).get_table_names())

    command.downgrade(config, "base")
    assert not {"projects", "entries"} & set(inspect(engine).get_table_names())
    engine.dispose()


def test_migrations_are_in_sync_with_orm_models(db_url):
    """Если поменял модели и забыл создать миграцию, этот тест упадёт."""
    command.upgrade(alembic_config(db_url), "head")
    engine = make_engine(db_url)
    with engine.connect() as connection:
        diff = compare_metadata(MigrationContext.configure(connection), metadata)
    engine.dispose()

    assert diff == []
