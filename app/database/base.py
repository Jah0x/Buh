from __future__ import annotations

try:
    from sqlalchemy.orm import DeclarativeBase
except ImportError:
    from sqlalchemy.orm import declarative_base

    Base = declarative_base()
else:

    class Base(DeclarativeBase):

        pass


__all__ = ["Base"]
