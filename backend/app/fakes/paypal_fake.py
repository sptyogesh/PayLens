"""Deterministic fake PayPal for tests and E2E (APP_ENV=test only, enforced in Settings)."""


class FakePayPalGateway:
    """In-memory stand-in for HttpPayPalGateway. Stories add the methods they need."""
