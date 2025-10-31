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
    contract_template_path: Path = Path("app/contracts/templates/contract.html.j2")
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_use_tls: bool = True
    mail_from: Optional[str] = None
    robokassa_merchant_login: Optional[str] = None
    robokassa_password1: Optional[str] = None
    robokassa_password2: Optional[str] = None
    robokassa_is_test: bool = True
    robokassa_culture: str = "ru"
    robokassa_signature_algo: str = "sha256"

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
        path = self.base_dir / "contracts"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def contract_template(self) -> Path:
        return self.contract_template_path.resolve()

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

        contract_template_path = Path(
            os.getenv("CONTRACT_TEMPLATE_PATH", "app/contracts/templates/contract.html.j2")
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
            contract_template_path=contract_template_path,
            smtp_host=os.getenv("SMTP_HOST"),
            smtp_port=int(os.getenv("SMTP_PORT", "587")),
            smtp_user=os.getenv("SMTP_USER"),
            smtp_password=os.getenv("SMTP_PASS"),
            smtp_use_tls=os.getenv("SMTP_USE_TLS", "1") != "0",
            mail_from=os.getenv("MAIL_FROM"),
            robokassa_merchant_login=os.getenv("ROBOKASSA_MERCHANT_LOGIN"),
            robokassa_password1=os.getenv("ROBOKASSA_PASSWORD1"),
            robokassa_password2=os.getenv("ROBOKASSA_PASSWORD2"),
            robokassa_is_test=os.getenv("ROBOKASSA_IS_TEST", "1") == "1",
            robokassa_culture=os.getenv("ROBOKASSA_CULTURE", "ru"),
            robokassa_signature_algo=os.getenv("ROBOKASSA_SIGNATURE_ALGO", "sha256"),
        )


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Environment variable {name} is required")
    return value


def load_settings() -> Settings:

    return Settings.from_env()
