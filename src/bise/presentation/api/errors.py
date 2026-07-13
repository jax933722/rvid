"""Maps domain/application exceptions to HTTP problem responses."""

from __future__ import annotations

from config.logging import get_logger
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from bise.application.errors import ApplicationError, ConflictError, NotFoundError
from bise.domain.errors import DomainError
from bise.presentation.api.schemas.common import ProblemDetail

logger = get_logger(__name__)


def _problem(status: int, title: str, detail: str, request: Request) -> JSONResponse:
    correlation_id = request.headers.get("X-Correlation-Id")
    body = ProblemDetail(title=title, status=status, detail=detail, correlation_id=correlation_id)
    return JSONResponse(status_code=status, content=body.model_dump())


def register_exception_handlers(app: FastAPI) -> None:
    """Register handlers that translate known exceptions into 4xx responses."""

    @app.exception_handler(NotFoundError)
    async def _handle_not_found(request: Request, exc: NotFoundError) -> JSONResponse:
        return _problem(404, "Not Found", str(exc), request)

    @app.exception_handler(ConflictError)
    async def _handle_conflict(request: Request, exc: ConflictError) -> JSONResponse:
        return _problem(409, "Conflict", str(exc), request)

    @app.exception_handler(ApplicationError)
    async def _handle_application_error(request: Request, exc: ApplicationError) -> JSONResponse:
        # e.g. an invalid search filter field/operator from compile_query.
        return _problem(422, "Unprocessable Entity", str(exc), request)

    @app.exception_handler(DomainError)
    async def _handle_domain_error(request: Request, exc: DomainError) -> JSONResponse:
        logger.warning("domain.error", error=str(exc))
        return _problem(422, "Unprocessable Entity", str(exc), request)
