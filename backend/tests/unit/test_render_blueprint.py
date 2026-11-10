"""render.yaml declares everything the apps read, keeps secrets out of the file (002 FR-050/051)."""

import re
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]  # PyYAML ships no stubs; stubs are not installed

from app.config import Settings

ROOT = Path(__file__).resolve().parents[3]
SECRETS = {"PAYPAL_CLIENT_ID", "PAYPAL_CLIENT_SECRET", "LLM_API_KEY", "DATABASE_URL"}
TEST_ONLY = {"RATE_LIMIT_ENABLED"}  # only allowed to change with APP_ENV=test


def blueprint() -> dict[str, Any]:
    data = yaml.safe_load((ROOT / "render.yaml").read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def env(service: str) -> dict[str, dict[str, Any]]:
    services = {s["name"]: s for s in blueprint()["services"]}
    return {item["key"]: item for item in services[service]["envVars"]}


def test_postgres_18_and_two_web_services() -> None:
    data = blueprint()
    assert data["databases"][0]["postgresMajorVersion"] == "18"
    services = {s["name"]: s for s in data["services"]}
    assert services["paylens-api"]["healthCheckPath"] == "/health"
    assert (services["paylens-api"]["rootDir"], services["paylens-web"]["rootDir"]) == (
        "backend",
        "frontend",
    )


def test_every_backend_setting_is_declared() -> None:
    declared = set(env("paylens-api"))
    expected = {name.upper() for name in Settings.model_fields} - TEST_ONLY
    assert expected <= declared


def test_secrets_are_never_written_in_the_file() -> None:
    api = env("paylens-api")
    for key in SECRETS:
        assert "value" not in api[key], key
    assert api["APP_ENV"]["value"] == "production"
    assert api["PAYPAL_BASE_URL"]["value"] == "https://api-m.sandbox.paypal.com"


def test_every_public_frontend_variable_is_declared() -> None:
    used: set[str] = set()
    for path in (ROOT / "frontend").rglob("*.ts*"):
        if "node_modules" in path.parts or ".next" in path.parts:
            continue
        used |= set(re.findall(r"process\.env\.(NEXT_PUBLIC_[A-Z_]+)", path.read_text("utf-8")))
    assert used and used <= set(env("paylens-web"))
