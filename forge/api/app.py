"""FastAPI application for FORGE REST API."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from forge.api.routes import api_router
from forge.api.routes.system import build_health_data, list_reference_cells
from forge.api.schemas.models import ErrorDetail, ErrorResponse, HealthResponse

logger = logging.getLogger(__name__)


def _build_error_response(
    status_code: int, code: str, message: str, details: list[str] | None = None
) -> JSONResponse:
    payload = ErrorResponse(
        error=ErrorDetail(code=code, message=message, details=details or [])
    ).model_dump()
    return JSONResponse(status_code=status_code, content=payload)


def create_app() -> FastAPI:
    """Create and configure the FORGE FastAPI app."""
    app = FastAPI(
        title="FORGE API",
        description="REST API for FORGE engine and AXIOM supervision workflows.",
        version="0.1.0",
        root_path=os.getenv("FORGE_API_ROOT_PATH", ""),
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    project_root = Path(__file__).resolve().parents[2]
    app.state.reference_data_dir = project_root / "data" / "reference"

    @app.exception_handler(RequestValidationError)
    async def request_validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        details = [
            f"{'.'.join(str(part) for part in err.get('loc', []))}: {err.get('msg', 'invalid value')}"
            for err in exc.errors()
        ]
        return _build_error_response(
            status_code=400,
            code="bad_request",
            message="Request validation failed.",
            details=details,
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        raw_detail: Any = exc.detail
        details: list[str] = []
        message = "Request failed."

        if isinstance(raw_detail, str):
            message = raw_detail
        elif isinstance(raw_detail, list):
            details = [str(item) for item in raw_detail]
            message = "Request failed."
        elif isinstance(raw_detail, dict):
            message = str(raw_detail.get("message", "Request failed."))
            raw_details = raw_detail.get("details")
            if isinstance(raw_details, list):
                details = [str(item) for item in raw_details]
        else:
            message = str(raw_detail)

        return _build_error_response(
            status_code=exc.status_code,
            code=f"http_{exc.status_code}",
            message=message,
            details=details,
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled API exception.", exc_info=exc)
        return _build_error_response(
            status_code=500,
            code="internal_error",
            message="Unexpected internal server error.",
        )

    @app.on_event("startup")
    async def startup_event() -> None:
        reference_dir = Path(app.state.reference_data_dir)
        reference_count = len(list_reference_cells(reference_dir))
        logger.info(
            "FORGE API startup complete. version=%s reference_cells=%d",
            build_health_data().version,
            reference_count,
        )

    @app.get("/health", response_model=HealthResponse, tags=["System"])
    def root_health_alias() -> HealthResponse:
        """Infrastructure-friendly alias for versioned health endpoint."""
        return HealthResponse(data=build_health_data())

    app.include_router(api_router)
    return app


app = create_app()

