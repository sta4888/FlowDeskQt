from __future__ import annotations

from sqlalchemy.orm import Session, sessionmaker

from activity_tracker.application.unit_of_work import UnitOfWork

from .repositories import SqlAlchemyEntryRepository, SqlAlchemyProjectRepository


class SqlAlchemyUnitOfWork(UnitOfWork):
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def __enter__(self) -> "SqlAlchemyUnitOfWork":
        self._session = self._session_factory()
        self.projects = SqlAlchemyProjectRepository(self._session)
        self.entries = SqlAlchemyEntryRepository(self._session)
        return self

    def __exit__(self, *exc_info) -> None:
        super().__exit__(*exc_info)  # rollback
        self._session.close()

    def commit(self) -> None:
        self._session.commit()

    def rollback(self) -> None:
        self._session.rollback()
