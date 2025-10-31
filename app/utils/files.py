from __future__ import annotations

import re
from pathlib import Path
from uuid import uuid4

ALLOWED_FILENAME_RE = re.compile(r"[^a-zA-Z0-9._-]")


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def read_text(path: Path) -> str:
    return Path(path).read_text(encoding="utf-8")


def sanitize_filename(name: str) -> str:
    base = ALLOWED_FILENAME_RE.sub("_", name)
    base = base.strip("._") or "file"
    suffix = uuid4().hex
    if "." in base:
        stem, ext = base.rsplit(".", 1)
        return f"{stem}_{suffix}.{ext}"
    return f"{base}_{suffix}"
