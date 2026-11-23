import pytest

from activity_tracker.infrastructure.db.database import (
    make_engine,
    make_session_factory,
    upgrade_to_head,
)
from activity_tracker.infrastructure.db.unit_of_work import SqlAlchemyUnitOfWork


@pytest.fixture
def db_url(tmp_path):
    return f"sqlite:///{tmp_path / 'test.db'}"


@pytest.fixture
def engine(db_url):
    upgrade_to_head(db_url)  # схема создаётся теми же миграциями, что и в проде
    engine = make_engine(db_url)
    yield engine
    engine.dispose()


@pytest.fixture
def session_factory(engine):
    return make_session_factory(engine)


@pytest.fixture
def uow_factory(session_factory):
    return lambda: SqlAlchemyUnitOfWork(session_factory)
