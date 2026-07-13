"""FastAPI dependency providers.

These pull the fully-wired :class:`Container` from application state and hand
use cases to routers, so routers never construct their own dependencies.
"""

from __future__ import annotations

from typing import Annotated

from config.containers import Container
from fastapi import Depends, Request

from bise.application.use_cases.companies.create_company import CreateCompany
from bise.application.use_cases.companies.get_company import GetCompany
from bise.application.use_cases.companies.list_companies import ListCompanies


def get_container(request: Request) -> Container:
    """Return the process-wide container stored on app state."""
    container: Container = request.app.state.container
    return container


ContainerDep = Annotated[Container, Depends(get_container)]


def get_create_company(container: ContainerDep) -> CreateCompany:
    return container.create_company()


def get_get_company(container: ContainerDep) -> GetCompany:
    return container.get_company()


def get_list_companies(container: ContainerDep) -> ListCompanies:
    return container.list_companies()
