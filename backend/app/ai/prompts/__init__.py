"""Versioned prompt files (Principle IX). Each prompt is read from disk once and cached."""

from functools import lru_cache
from pathlib import Path

PROMPTS_DIR = Path(__file__).resolve().parent
CHAT_SYSTEM_FILE = "chat_system.md"


@lru_cache
def load_prompt(file_name: str) -> str:
    return (PROMPTS_DIR / file_name).read_text(encoding="utf-8").strip()


def chat_system_prompt() -> str:
    """Static on purpose (no dates) so the provider can cache it; today's date goes in the
    first user message instead."""
    return load_prompt(CHAT_SYSTEM_FILE)
