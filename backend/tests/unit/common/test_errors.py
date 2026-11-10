from app.common.errors import (
    PaymentDeclinedError,
    PayPalError,
    RateLimitedError,
    SyncInProgressError,
    error_body,
)


def test_error_codes_and_statuses() -> None:
    assert (SyncInProgressError("x").http_status, SyncInProgressError("x").code) == (
        409,
        "SYNC_IN_PROGRESS",
    )
    assert PaymentDeclinedError("x").http_status == 422
    assert PayPalError("x", code="PAYPAL_AUTH_FAILED").code == "PAYPAL_AUTH_FAILED"
    assert RateLimitedError("x", retry_after_s=5).retry_after_s == 5


def test_error_body_shape() -> None:
    assert error_body("CODE", "msg") == {"error": {"code": "CODE", "message": "msg"}}
