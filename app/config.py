from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


@dataclass(slots=True)
class Settings:

    bot_token: str
    admin_username: str
    base_dir: Path
    db_url: str
    public_base_url: Optional[str]
    environment: str = "dev"
    consent_version: str = "v1"
    consent_text_path: Path = Path("app/resources/privacy_consent_v1.txt")

    @property
    def data_dir(self) -> Path:
        return self.base_dir

    @property
    def tracks_dir(self) -> Path:
        return self.base_dir / "tracks"

    @property
    def covers_dir(self) -> Path:
        return self.base_dir / "covers"

    @property
    def log_level(self) -> str:
        return "INFO" if self.environment.lower() == "prod" else "DEBUG"

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()
        base_dir = Path(os.getenv("BASE_DIR", "./data")).resolve()
        base_dir.mkdir(parents=True, exist_ok=True)
        for sub in ("tracks", "covers"):
            (base_dir / sub).mkdir(parents=True, exist_ok=True)

        consent_text_path = Path(
            os.getenv("CONSENT_TEXT_PATH", "app/resources/privacy_consent_v1.txt")
        ).resolve()

        return cls(
            bot_token=_require_env("BOT_TOKEN"),
            admin_username=os.getenv("ADMIN_USERNAME", ""),
            base_dir=base_dir,
            db_url=os.getenv("DB_URL", "sqlite+aiosqlite:///./data/app.db"),
            public_base_url=os.getenv("PUBLIC_BASE_URL"),
            environment=os.getenv("APP_ENV", "dev"),
            consent_version=os.getenv("CONSENT_VERSION", "v1"),
            consent_text_path=consent_text_path,
        )


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Environment variable {name} is required")
    return value


def load_settings() -> Settings:

    return Settings.from_env()
