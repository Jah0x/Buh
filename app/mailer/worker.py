from __future__ import annotations

import asyncio
import logging
import smtplib
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from pathlib import Path
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.database import models
from app.database.session import Database

logger = logging.getLogger(__name__)


class MailerWorker:
    def __init__(self, settings: Settings, database: Database):
        self.settings = settings
        self.database = database
        self.retry_schedule = [60, 300, 900, 3600, 21600]

    async def run(self, interval: float = 5.0) -> None:
        while True:
            processed = await self.process_once()
            if not processed:
                await asyncio.sleep(interval)

    async def process_once(self) -> bool:
        async with self.database.session() as session:
            mail = await self._fetch_next(session)
            if not mail:
                return False
            mail.status = "sending"
            mail.attempts += 1
            await session.flush()
            try:
                message = self._build_message(mail)
                await self._send(message)
            except Exception as exc:
                logger.exception("Failed to send mail %s", mail.id)
                self._handle_failure(mail, exc)
                await session.flush()
                await session.commit()
                return True
            await self._handle_success(session, mail)
            await session.flush()
            await session.commit()
            return True

    async def _fetch_next(self, session: AsyncSession) -> Optional[models.MailOutbox]:
        now = datetime.now(timezone.utc)
        stmt = (
            select(models.MailOutbox)
            .where(
                models.MailOutbox.status == "pending",
                models.MailOutbox.scheduled_at <= now,
            )
            .order_by(models.MailOutbox.scheduled_at.asc(), models.MailOutbox.id.asc())
            .limit(1)
        )
        result = await session.execute(stmt)
        mail = result.scalar_one_or_none()
        return mail

    def _build_message(self, mail: models.MailOutbox) -> EmailMessage:
        if not self.settings.mail_from:
            raise RuntimeError("MAIL_FROM is not configured")
        if not self.settings.smtp_host:
            raise RuntimeError("SMTP_HOST is not configured")
        message = EmailMessage()
        message["Subject"] = mail.subject
        message["From"] = self.settings.mail_from
        message["To"] = mail.to_email
        if mail.text:
            message.set_content(mail.text)
        else:
            message.set_content(mail.html or "")
        if mail.html:
            message.add_alternative(mail.html, subtype="html")
        for attachment in mail.attachments or []:
            path = self._resolve_attachment_path(attachment.get("path"))
            if not path.exists():
                raise FileNotFoundError(str(path))
            content_type = attachment.get("content_type", "application/octet-stream")
            maintype, _, subtype = content_type.partition("/")
            with path.open("rb") as fh:
                data = fh.read()
            message.add_attachment(
                data,
                maintype=maintype or "application",
                subtype=subtype or "octet-stream",
                filename=attachment.get("filename", path.name),
            )
        return message

    def _resolve_attachment_path(self, relative: Optional[str]) -> Path:
        if not relative:
            raise RuntimeError("Attachment path is missing")
        return (self.settings.data_dir / relative).resolve()

    async def _send(self, message: EmailMessage) -> None:
        host = self.settings.smtp_host
        port = self.settings.smtp_port
        with smtplib.SMTP(host, port) as client:
            client.ehlo()
            if self.settings.smtp_use_tls:
                client.starttls()
                client.ehlo()
            if self.settings.smtp_user and self.settings.smtp_password:
                client.login(self.settings.smtp_user, self.settings.smtp_password)
            client.send_message(message)

    def _handle_failure(self, mail: models.MailOutbox, exc: Exception) -> None:
        mail.last_error = str(exc)
        delay = self._next_delay(mail.attempts)
        if delay is None:
            mail.status = "failed"
        else:
            mail.status = "pending"
            mail.scheduled_at = datetime.now(timezone.utc) + timedelta(seconds=delay)

    async def _handle_success(self, session: AsyncSession, mail: models.MailOutbox) -> None:
        now = datetime.now(timezone.utc)
        mail.status = "sent"
        mail.sent_at = now
        mail.last_error = None
        stmt = select(models.Contract).where(models.Contract.mail_message_key == mail.message_key)
        result = await session.execute(stmt)
        contract = result.scalar_one_or_none()
        if contract and contract.status != "signed":
            contract.status = "sent"
            contract.sent_via = "email"

    def _next_delay(self, attempts: int) -> Optional[int]:
        schedule = self.retry_schedule
        if attempts <= 0 or attempts > len(schedule):
            return None
        return schedule[attempts - 1]
