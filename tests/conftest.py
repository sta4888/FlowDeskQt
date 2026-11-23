import pytest

from activity_tracker.infrastructure.db.orm import start_mappers


@pytest.fixture(scope="session", autouse=True)
def _mappers():
    start_mappers()
