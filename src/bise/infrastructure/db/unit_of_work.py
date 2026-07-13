"""SQLAlchemy Unit of Work implementing the application port."""

from __future__ import annotations

from types import TracebackType

from sqlalchemy.orm import Session, sessionmaker

from bise.application.ports.repositories import (
    CompanyRepository,
    CrawledPageRepository,
    CrawlJobRepository,
)
from bise.infrastructure.db.repositories.company_repository import SqlAlchemyCompanyRepository
from bise.infrastructure.db.repositories.crawl_repository import (
    SqlAlchemyCrawledPageRepository,
    SqlAlchemyCrawlJobRepository,
)


class SqlAlchemyUnitOfWork:
    """Opens a session/transaction and exposes repositories bound to it.

    Rolls back automatically on exit unless :meth:`commit` was called, so a use
    case that raises mid-way never leaves partial writes.
    """

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory
        self._session: Session | None = None
        # Typed as the ports so this UoW structurally satisfies the UnitOfWork protocol.
        self.companies: CompanyRepository
        self.crawl_jobs: CrawlJobRepository
        self.crawled_pages: CrawledPageRepository

    def __enter__(self) -> SqlAlchemyUnitOfWork:
        self._session = self._session_factory()
        self.companies = SqlAlchemyCompanyRepository(self._session)
        self.crawl_jobs = SqlAlchemyCrawlJobRepository(self._session)
        self.crawled_pages = SqlAlchemyCrawledPageRepository(self._session)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        assert self._session is not None
        try:
            if exc_type is not None:
                self._session.rollback()
        finally:
            self._session.close()
            self._session = None

    def commit(self) -> None:
        assert self._session is not None, "commit() called outside the UoW context"
        self._session.commit()

    def rollback(self) -> None:
        assert self._session is not None, "rollback() called outside the UoW context"
        self._session.rollback()
