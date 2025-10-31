"""File related helper utilities."""
from __future__ import annotations

from pathlib import Path


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def read_text(path: Path) -> str:
    return Path(path).read_text(encoding="utf-8")
