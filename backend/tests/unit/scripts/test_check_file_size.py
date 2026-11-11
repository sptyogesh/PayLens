"""Tests for scripts/check_file_size.py (constitution Principle XIII limits)."""

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

SCRIPT = Path(__file__).resolve().parents[4] / "scripts" / "check_file_size.py"


def load_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("check_file_size", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


cfs = load_module()


def write_lines(path: Path, count: int) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("x\n" * count, encoding="utf-8")
    return path


@pytest.mark.parametrize(
    ("name", "limit"),
    [
        ("app/service.py", 200),
        ("lib/format.ts", 200),
        ("components/Card.tsx", 150),
        ("tests/test_service.py", 300),
        ("components/Card.test.tsx", 300),
        ("e2e/pay.spec.ts", 300),
    ],
)
def test_limit_boundaries(tmp_path: Path, name: str, limit: int) -> None:
    at_limit = write_lines(tmp_path / "ok" / name, limit)
    over_limit = write_lines(tmp_path / "bad" / name, limit + 1)
    assert cfs.find_offenders([at_limit]) == []
    assert cfs.find_offenders([over_limit]) == [(over_limit, limit + 1, limit)]


def test_generated_and_non_source_files_are_excluded(tmp_path: Path) -> None:
    generated = write_lines(tmp_path / "lib" / "api" / "api-types.ts", 5000)
    lockfile = write_lines(tmp_path / "package-lock.json", 5000)
    vendored = write_lines(tmp_path / "node_modules" / "pkg" / "index.ts", 5000)
    assert cfs.find_offenders([generated, lockfile, vendored]) == []


def test_main_returns_non_zero_and_lists_offenders(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    big = write_lines(tmp_path / "big.py", 201)
    assert cfs.main([str(big)]) == 1
    assert "big.py: 201 lines (limit 200)" in capsys.readouterr().out
    assert cfs.main([str(write_lines(tmp_path / "small.py", 10))]) == 0
