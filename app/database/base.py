from __future__ import annotations

try:
    from sqlalchemy.orm import DeclarativeBase
except ModuleNotFoundError as exc:
    raise ModuleNotFoundError(
        "SQLAlchemy is not installed. Install project dependencies to work with the database."
    ) from exc
except ImportError:
    from sqlalchemy.orm import declarative_base

    Base = declarative_base()
else:

    class Base(DeclarativeBase):

        pass


__all__ = ["Base"]
