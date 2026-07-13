"""Composition root — the single place that wires concrete infrastructure.

Everything else depends on abstractions; only this module (and it alone) knows
the concrete engine, session factory, and repository implementations. It builds
fully-wired use cases for the presentation layer to consume.
"""

from __future__ import annotations

from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker

from bise.application.use_cases.companies.create_company import CreateCompany
from bise.application.use_cases.companies.get_company import GetCompany
from bise.application.use_cases.companies.list_companies import ListCompanies
from bise.infrastructure.db.engine import create_db_engine, create_session_factory
from bise.infrastructure.db.unit_of_work import SqlAlchemyUnitOfWork
from config.settings import Settings, get_settings


class Container:
    """Owns process-wide singletons and builds use cases on demand."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings: Settings = settings or get_settings()
        self.engine: Engine = create_db_engine(self.settings)
        self.session_factory: sessionmaker[Session] = create_session_factory(self.engine)

    def unit_of_work(self) -> SqlAlchemyUnitOfWork:
        """Create a fresh Unit of Work (one transactional scope per use case call)."""
        return SqlAlchemyUnitOfWork(self.session_factory)

    # --- Use case factories (a new UoW per call keeps sessions request-scoped) ---
    def create_company(self) -> CreateCompany:
        return CreateCompany(self.unit_of_work())

    def get_company(self) -> GetCompany:
        return GetCompany(self.unit_of_work())

    def list_companies(self) -> ListCompanies:
        return ListCompanies(self.unit_of_work())
