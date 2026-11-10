"""Write the FastAPI OpenAPI schema to frontend/lib/api/openapi.json (input for api-types.ts)."""

import json
import os
from pathlib import Path

OUTPUT = Path(__file__).resolve().parents[2] / "frontend" / "lib" / "api" / "openapi.json"


def main() -> None:
    # The schema does not depend on real settings; use safe test values to build the app.
    os.environ.setdefault("APP_ENV", "test")
    os.environ.setdefault("PAYPAL_MODE", "fake")
    os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://localhost/unused")
    from app.main import create_app  # noqa: PLC0415 - import after env is set

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(create_app().openapi(), indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
