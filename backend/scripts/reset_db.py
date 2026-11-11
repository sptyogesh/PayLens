"""Drop and recreate all tables. Test databases only (used by Playwright global setup)."""

from app.config import get_settings
from app.db import get_engine
from app.models import Base


def main() -> None:
    if get_settings().app_env != "test":
        raise SystemExit("reset_db only runs with APP_ENV=test")
    engine = get_engine()
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    print("Database reset")


if __name__ == "__main__":
    main()
