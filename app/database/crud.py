from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import models


async def get_or_create_user(session: AsyncSession, telegram_id: int, username: Optional[str], first_name: Optional[str], last_name: Optional[str]) -> models.User:
    stmt = select(models.User).where(models.User.telegram_id == telegram_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    if user:
        return user
    user = models.User(
        telegram_id=telegram_id,
        username=username,
        first_name=first_name,
        last_name=last_name,
    )
    session.add(user)
    await session.flush()
    return user


async def create_release(
    session: AsyncSession,
    user: models.User,
    track_name: str,
    artist: Optional[str],
    authors: Optional[str],
    description: Optional[str],
    release_date: Optional[str],
    track_file: str,
    cover_file: str,
) -> models.Release:
    release = models.Release(
        user=user,
        track_name=track_name,
        artist=artist,
        authors=authors,
        description=description,
        release_date=release_date,
        track_file=track_file,
        cover_file=cover_file,
    )
    session.add(release)
    await session.flush()
    return release


async def create_consent(
    session: AsyncSession,
    user: models.User,
    release: models.Release,
    full_name: str,
    email: str,
    text_version: str,
    text_body: str,
    method: str,
    accepted_at: datetime,
) -> models.Consent:
    consent = models.Consent(
        user=user,
        release=release,
        full_name=full_name,
        email=email,
        text_version=text_version,
        text_body=text_body,
        method=method,
        accepted_at=accepted_at,
    )
    session.add(consent)
    await session.flush()
    return consent


async def get_latest_consent_for_user(session: AsyncSession, telegram_id: int) -> Optional[models.Consent]:
    stmt = (
        select(models.Consent)
        .join(models.User)
        .where(models.User.telegram_id == telegram_id)
        .order_by(models.Consent.accepted_at.desc())
    )
    result = await session.execute(stmt)
    return result.scalars().first()
