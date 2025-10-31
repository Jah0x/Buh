from __future__ import annotations

import logging
from logging.config import dictConfig
from pathlib import Path

LOG_DIR = Path("logs")
LOG_FILE = LOG_DIR / "bot.log"


def configure_logging(level: str = "INFO") -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                    "level": level.upper(),
                },
                "file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "formatter": "default",
                    "filename": str(LOG_FILE),
                    "maxBytes": 5 * 1024 * 1024,
                    "backupCount": 5,
                    "encoding": "utf-8",
                    "level": level.upper(),
                },
            },
            "root": {
                "handlers": ["console", "file"],
                "level": level.upper(),
            },
        }
    )


logger = logging.getLogger("plovbot")
