from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from . import models


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
) -> models.Consent:
    consent = models.Consent(
        user=user,
        release=release,
        full_name=full_name,
        email=email,
        text_version=text_version,
        text_body=text_body,
    )
    session.add(consent)
    await session.flush()
    return consent


async def create_payment(
    session: AsyncSession,
    user: models.User,
    release: models.Release,
    provider_payment_id: str,
    status: str,
    amount: float,
    currency: str,
    metadata: Optional[dict] = None,
) -> models.Payment:
    payment = models.Payment(
        user=user,
        release=release,
        provider_payment_id=provider_payment_id,
        status=status,
        amount=amount,
        currency=currency,
        metadata=metadata,
    )
    session.add(payment)
    await session.flush()
    return payment


async def update_payment_status(session: AsyncSession, provider_payment_id: str, status: str, confirmed_at: Optional[datetime] = None, metadata: Optional[dict] = None) -> Optional[models.Payment]:
    stmt = select(models.Payment).where(models.Payment.provider_payment_id == provider_payment_id)
    result = await session.execute(stmt)
    payment = result.scalar_one_or_none()
    if not payment:
        return None
    payment.status = status
    if confirmed_at:
        payment.confirmed_at = confirmed_at
    if metadata is not None:
        payment.metadata = metadata
    await session.flush()
    return payment


async def create_contract(
    session: AsyncSession,
    user: models.User,
    release: models.Release,
    status: str = "drafted",
    pdf_path: Optional[str] = None,
) -> models.Contract:
    contract = models.Contract(user=user, release=release, status=status, pdf_path=pdf_path)
    session.add(contract)
    await session.flush()
    return contract


async def update_contract_status(
    session: AsyncSession,
    release_id: int,
    status: str,
    pdf_path: Optional[str] = None,
    sent_at: Optional[datetime] = None,
    signed_at: Optional[datetime] = None,
) -> Optional[models.Contract]:
    stmt = select(models.Contract).where(models.Contract.release_id == release_id)
    result = await session.execute(stmt)
    contract = result.scalar_one_or_none()
    if not contract:
        return None
    contract.status = status
    if pdf_path:
        contract.pdf_path = pdf_path
    if sent_at:
        contract.sent_at = sent_at
    if signed_at:
        contract.signed_at = signed_at
    contract.updated_at = datetime.utcnow()
    await session.flush()
    return contract


async def get_payment_with_relations(session: AsyncSession, provider_payment_id: str) -> Optional[models.Payment]:
    stmt = (
        select(models.Payment)
        .where(models.Payment.provider_payment_id == provider_payment_id)
        .options(
            selectinload(models.Payment.release).selectinload(models.Release.consent),
            selectinload(models.Payment.release).selectinload(models.Release.contract),
            selectinload(models.Payment.release).selectinload(models.Release.user),
        )
    )
    result = await session.execute(stmt)
    payment = result.scalar_one_or_none()
    if payment:
        await session.refresh(payment, attribute_names=["release"])
        if payment.release:
            await session.refresh(payment.release, attribute_names=["consent", "contract", "user"])
    return payment
