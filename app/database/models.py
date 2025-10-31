from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(unique=True, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    releases: Mapped[List["Release"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    consents: Mapped[List["Consent"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Release(Base):
    __tablename__ = "releases"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    track_name: Mapped[str] = mapped_column(String(255))
    artist: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    authors: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    release_date: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    track_file: Mapped[str] = mapped_column(String(1024))
    cover_file: Mapped[str] = mapped_column(String(1024))
    status: Mapped[str] = mapped_column(String(32), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user: Mapped[User] = relationship(back_populates="releases")
    consent: Mapped[Optional["Consent"]] = relationship(back_populates="release", uselist=False)


class Consent(Base):
    __tablename__ = "consents"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    release_id: Mapped[int] = mapped_column(ForeignKey("releases.id", ondelete="CASCADE"))
    full_name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255))
    text_version: Mapped[str] = mapped_column(String(32))
    text_body: Mapped[str] = mapped_column(Text)
    method: Mapped[str] = mapped_column(String(64), default="telegram_button")
    accepted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user: Mapped[User] = relationship(back_populates="consents")
    release: Mapped[Release] = relationship(back_populates="consent")
