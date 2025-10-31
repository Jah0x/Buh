from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.contracts.generator import ContractGenerator
from app.database import models


@dataclass(slots=True)
class ContractContext:
    release: models.Release
    consent: models.Consent
    payment: models.Payment


class ContractService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.generator = ContractGenerator(settings.contract_template)

    def _build_output_path(self, release_id: int, timestamp: datetime) -> Path:
        relative = Path(str(release_id)) / f"{int(timestamp.timestamp())}.pdf"
        return self.settings.contracts_dir / relative

    def _relative_pdf_path(self, path: Path) -> str:
        try:
            return str(path.relative_to(self.settings.data_dir))
        except ValueError:
            return str(path)

    def _build_context(self, context: ContractContext, timestamp: datetime) -> Dict[str, object]:
        return {
            "release": context.release,
            "consent": context.consent,
            "payment": context.payment,
            "generated_at": timestamp,
        }

    async def create_contract(self, session: AsyncSession, context: ContractContext) -> models.Contract:
        timestamp = datetime.now(timezone.utc)
        output_path = self._build_output_path(context.release.id, timestamp)
        pdf_path = self.generator.generate(output_path, self._build_context(context, timestamp))
        contract = models.Contract(
            release_id=context.release.id,
            pdf_path=self._relative_pdf_path(pdf_path),
            status="drafted",
            sent_via="email",
            accept_token=uuid4().hex,
        )
        session.add(contract)
        await session.flush()
        return contract

    async def enqueue_email(
        self,
        session: AsyncSession,
        contract: models.Contract,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: str,
    ) -> models.MailOutbox:
        now = datetime.now(timezone.utc)
        message_key = contract.mail_message_key or uuid4().hex
        contract.mail_message_key = message_key
        attachments = [
            {
                "path": contract.pdf_path,
                "filename": Path(contract.pdf_path).name,
                "content_type": "application/pdf",
            }
        ]
        mail = models.MailOutbox(
            to_email=to_email,
            subject=subject,
            html=html_body,
            text=text_body,
            attachments=attachments,
            message_key=message_key,
            status="pending",
            attempts=0,
            scheduled_at=now,
        )
        session.add(mail)
        await session.flush()
        return mail

    def build_accept_link(self, contract: models.Contract) -> str:
        base = self.settings.public_base_url or "http://localhost"
        return f"{base.rstrip('/')}/contract/accept?token={contract.accept_token}"

    def resolve_pdf_path(self, contract: models.Contract) -> Path:
        return self.settings.data_dir / contract.pdf_path


__all__ = ["ContractService", "ContractContext"]
