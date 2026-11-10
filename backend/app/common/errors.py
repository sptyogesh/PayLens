"""Application errors and their HTTP mapping (constitution Coding Standards).

Every error response has the shape {"error": {"code": "...", "message": "..."}}.
Stack traces never reach the client.
"""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

INTERNAL_ERROR_MESSAGE = "Something went wrong on our side. Please try again."
VALIDATION_ERROR_MESSAGE = "Some fields are missing or invalid."


class AppError(Exception):
    """Base error with a stable code, a safe message and an HTTP status."""

    http_status = 500
    code = "INTERNAL_ERROR"

    def __init__(self, message: str, code: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        if code is not None:
            self.code = code


class ValidationAppError(AppError):
    http_status = 422
    code = "VALIDATION_ERROR"


class InvalidPeriodError(AppError):
    http_status = 400
    code = "INVALID_PERIOD"


class NotFoundError(AppError):
    http_status = 404
    code = "NOT_FOUND"


class SyncInProgressError(AppError):
    http_status = 409
    code = "SYNC_IN_PROGRESS"


class PaymentDeclinedError(AppError):
    http_status = 422
    code = "PAYMENT_DECLINED"


class PayPalError(AppError):
    """Upstream PayPal failure. Codes: PAYPAL_UNAVAILABLE, PAYPAL_AUTH_FAILED, PAYPAL_REJECTED."""

    http_status = 502
    code = "PAYPAL_UNAVAILABLE"


class FxUnavailableError(AppError):
    """The FX rate source could not be reached. Leakage stays "rate unavailable" (FR-005)."""

    http_status = 502
    code = "FX_UNAVAILABLE"


class RateLimitedError(AppError):
    http_status = 429
    code = "RATE_LIMITED"

    def __init__(self, message: str, retry_after_s: int) -> None:
        super().__init__(message)
        self.retry_after_s = retry_after_s


def error_body(code: str, message: str) -> dict[str, dict[str, str]]:
    return {"error": {"code": code, "message": message}}


async def handle_app_error(_request: Request, error: Exception) -> JSONResponse:
    if not isinstance(error, AppError):  # pragma: no cover - registered for AppError only
        return await handle_unexpected_error(_request, error)
    headers: dict[str, str] = {}
    if isinstance(error, RateLimitedError):
        headers["Retry-After"] = str(error.retry_after_s)
    return JSONResponse(
        status_code=error.http_status,
        content=error_body(error.code, error.message),
        headers=headers,
    )


async def handle_validation_error(_request: Request, _error: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=422, content=error_body("VALIDATION_ERROR", VALIDATION_ERROR_MESSAGE)
    )


async def handle_unexpected_error(request: Request, error: Exception) -> JSONResponse:
    logger.error("Unhandled error on %s %s: %r", request.method, request.url.path, error)
    return JSONResponse(
        status_code=500, content=error_body("INTERNAL_ERROR", INTERNAL_ERROR_MESSAGE)
    )


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, handle_app_error)
    app.add_exception_handler(RequestValidationError, handle_validation_error)
    app.add_exception_handler(Exception, handle_unexpected_error)
