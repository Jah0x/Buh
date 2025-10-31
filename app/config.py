"""Application configuration loading."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


@dataclass(slots=True)
class Settings:
    """Runtime settings loaded from environment variables."""

    bot_token: str
    admin_username: str
    base_dir: Path
    db_url: str
    yookassa_shop_id: Optional[str]
    yookassa_secret: Optional[str]
    public_base_url: Optional[str]
    log_level: str = "INFO"
    consent_version: str = "v1"
    consent_text_path: Path = Path("app/resources/privacy_consent_v1.txt")
    contract_template: Path = Path("app/contracts/templates/contract.html")
    web_host: str = "0.0.0.0"
    web_port: int = 8080

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
    def contracts_dir(self) -> Path:
        return self.base_dir / "contracts"

    @property
    def consent_storage_path(self) -> Path:
        return self.base_dir / "consents"

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()
        base_dir = Path(os.getenv("BASE_DIR", "./data")).resolve()
        base_dir.mkdir(parents=True, exist_ok=True)
        for sub in ("tracks", "covers", "contracts", "consents"):
            (base_dir / sub).mkdir(parents=True, exist_ok=True)

        consent_text_path = Path(
            os.getenv("CONSENT_TEXT_PATH", "app/resources/privacy_consent_v1.txt")
        ).resolve()
        contract_template = Path(
            os.getenv("CONTRACT_TEMPLATE", "app/contracts/templates/contract.html")
        ).resolve()

        return cls(
            bot_token=_require_env("BOT_TOKEN"),
            admin_username=os.getenv("ADMIN_USERNAME", ""),
            base_dir=base_dir,
            db_url=os.getenv("DB_URL", "sqlite+aiosqlite:///./data/app.db"),
            yookassa_shop_id=os.getenv("YOOKASSA_SHOP_ID"),
            yookassa_secret=os.getenv("YOOKASSA_SECRET"),
            public_base_url=os.getenv("PUBLIC_BASE_URL"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            consent_version=os.getenv("CONSENT_VERSION", "v1"),
            consent_text_path=consent_text_path,
            contract_template=contract_template,
            web_host=os.getenv("WEB_HOST", "0.0.0.0"),
            web_port=int(os.getenv("WEB_PORT", "8080")),
        )


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Environment variable {name} is required")
    return value


def load_settings() -> Settings:
    """Load settings singleton."""

    return Settings.from_env()
