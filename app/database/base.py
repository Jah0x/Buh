from __future__ import annotations

import importlib
import subprocess
import sys


def _install_sqlalchemy() -> None:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "SQLAlchemy>=2.0"])
    importlib.invalidate_caches()


try:
    from sqlalchemy.orm import DeclarativeBase
except ModuleNotFoundError as exc:
    if exc.name != "sqlalchemy":
        raise
    try:
        _install_sqlalchemy()
    except Exception as install_error:
        raise ModuleNotFoundError(
            "SQLAlchemy is not installed. Install project dependencies to work with the database."
        ) from install_error
    from sqlalchemy.orm import DeclarativeBase
except ImportError:
    from sqlalchemy.orm import declarative_base

    Base = declarative_base()
else:

    class Base(DeclarativeBase):

        pass


__all__ = ["Base"]
