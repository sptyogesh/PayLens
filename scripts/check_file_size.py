"""Fail when a source file exceeds the constitution Principle XIII hard limits.

Usage:
    python scripts/check_file_size.py            # scan backend/ and frontend/
    python scripts/check_file_size.py FILE ...   # check only these files (lint-staged)
"""

from __future__ import annotations

import sys
from pathlib import Path

SOURCE_MAX_LINES = 200
COMPONENT_MAX_LINES = 150
TEST_MAX_LINES = 300
SOURCE_SUFFIXES = (".py", ".ts", ".tsx")
SCAN_ROOTS = ("backend", "frontend", "scripts")
EXCLUDED_NAMES = frozenset({"api-types.ts", "next-env.d.ts"})
EXCLUDED_DIRS = frozenset(
    {
        "node_modules",
        ".next",
        ".venv",
        "__pycache__",
        "coverage",
        "test-results",
        "playwright-report",
    }
)


def is_test_file(path: Path) -> bool:
    name = path.name
    return (
        name.startswith("test_")
        or name == "conftest.py"
        or ".test." in name
        or ".spec." in name
        or "e2e" in path.parts
        or "tests" in path.parts
    )


def limit_for(path: Path) -> int:
    if is_test_file(path):
        return TEST_MAX_LINES
    if path.suffix == ".tsx":
        return COMPONENT_MAX_LINES
    return SOURCE_MAX_LINES


def is_checked(path: Path) -> bool:
    if path.suffix not in SOURCE_SUFFIXES or path.name in EXCLUDED_NAMES:
        return False
    return not EXCLUDED_DIRS.intersection(path.parts)


def count_lines(path: Path) -> int:
    with path.open(encoding="utf-8") as handle:
        return sum(1 for _ in handle)


def find_offenders(paths: list[Path]) -> list[tuple[Path, int, int]]:
    offenders: list[tuple[Path, int, int]] = []
    for path in paths:
        if not path.is_file() or not is_checked(path):
            continue
        lines, limit = count_lines(path), limit_for(path)
        if lines > limit:
            offenders.append((path, lines, limit))
    return offenders


def collect(root: Path) -> list[Path]:
    files: list[Path] = []
    for name in SCAN_ROOTS:
        base = root / name
        if base.is_dir():
            files.extend(p for p in base.rglob("*") if is_checked(p.relative_to(root)))
    return files


def main(argv: list[str]) -> int:
    paths = [Path(arg) for arg in argv] if argv else collect(Path.cwd())
    offenders = find_offenders(paths)
    for path, lines, limit in offenders:
        sys.stdout.write(f"{path}: {lines} lines (limit {limit})\n")
    if offenders:
        sys.stdout.write("File size check failed: split the file (constitution Principle XIII).\n")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
