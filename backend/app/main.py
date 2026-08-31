from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    InvalidCursorError,
    NotFoundError,
    ValidationConflictError,
)
from app.db.session import engine
from app.schemas.base import ProblemDetail

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await engine.dispose()


def _problem_response(
    request: Request,
    *,
    status_code: int,
    title: str,
    detail: str,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    problem = ProblemDetail(title=title, status=status_code, detail=detail, instance=str(request.url))
    return JSONResponse(
        problem.model_dump(),
        status_code=status_code,
        media_type="application/problem+json",
        headers=headers,
    )


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        openapi_url="/openapi.json" if settings.debug else None,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix=settings.api_v1_prefix)

    @app.exception_handler(NotFoundError)
    async def handle_not_found(request: Request, exc: NotFoundError) -> JSONResponse:
        return _problem_response(
            request,
            status_code=404,
            title="Not found",
            detail=f"{exc.resource_type} {exc.resource_id} not found",
        )

    @app.exception_handler(InvalidCursorError)
    async def handle_invalid_cursor(request: Request, exc: InvalidCursorError) -> JSONResponse:
        return _problem_response(
            request, status_code=400, title="Invalid pagination cursor", detail=str(exc)
        )

    @app.exception_handler(ConflictError)
    async def handle_conflict(request: Request, exc: ConflictError) -> JSONResponse:
        return _problem_response(request, status_code=409, title="Conflict", detail=exc.message)

    @app.exception_handler(ValidationConflictError)
    async def handle_validation_conflict(
        request: Request, exc: ValidationConflictError
    ) -> JSONResponse:
        return _problem_response(
            request, status_code=422, title="Unprocessable request", detail=exc.message
        )

    @app.exception_handler(AuthenticationError)
    async def handle_authentication_error(
        request: Request, exc: AuthenticationError
    ) -> JSONResponse:
        return _problem_response(
            request,
            status_code=401,
            title="Not authenticated",
            detail=exc.message,
            headers={"WWW-Authenticate": "Bearer"},
        )

    @app.exception_handler(AuthorizationError)
    async def handle_authorization_error(request: Request, exc: AuthorizationError) -> JSONResponse:
        return _problem_response(
            request, status_code=403, title="Forbidden", detail=exc.message
        )

    @app.get("/health", tags=["health"])
    async def health_check() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
