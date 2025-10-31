from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional

from yookassa import Configuration, Payment
from yookassa.domain.notification import WebhookNotification

from app.config import Settings

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class PaymentResponse:
    id: str
    status: str
    confirmation_url: Optional[str]
    amount: float
    currency: str
    raw: Dict[str, Any]


class YooKassaClient:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.enabled = bool(settings.yookassa_shop_id and settings.yookassa_secret)
        if self.enabled:
            Configuration.account_id = settings.yookassa_shop_id
            Configuration.secret_key = settings.yookassa_secret
        else:
            logger.warning("YooKassa credentials are not configured. Payments will operate in stub mode.")

    async def create_payment(
        self,
        amount: float,
        currency: str,
        description: str,
        return_url: Optional[str],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> PaymentResponse:
        if not self.enabled:
            fake_id = f"stub-{int(datetime.utcnow().timestamp())}"
            raw = {
                "id": fake_id,
                "status": "pending",
                "confirmation": {"confirmation_url": return_url},
                "amount": {"value": amount, "currency": currency},
            }
            return PaymentResponse(
                id=fake_id,
                status="pending",
                confirmation_url=return_url,
                amount=amount,
                currency=currency,
                raw=raw,
            )

        loop = asyncio.get_running_loop()

        def _create() -> Payment:
            payload = {
                "amount": {"value": f"{amount:.2f}", "currency": currency},
                "confirmation": {"type": "redirect", "return_url": return_url or self.settings.public_base_url},
                "capture": True,
                "description": description,
            }
            if metadata:
                payload["metadata"] = metadata
            return Payment.create(payload)

        payment: Payment = await loop.run_in_executor(None, _create)
        confirmation_url = None
        if payment.confirmation and payment.confirmation["type"] == "redirect":
            confirmation_url = payment.confirmation.get("confirmation_url")
        return PaymentResponse(
            id=payment.id,
            status=payment.status,
            confirmation_url=confirmation_url,
            amount=float(payment.amount["value"]),
            currency=payment.amount["currency"],
            raw=payment.to_dict(),
        )


def parse_webhook_event(body: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    try:
        notification = WebhookNotification(body)
    except Exception as exc:
        logger.error("Failed to parse YooKassa webhook: %s", exc)
        return None
    payload = notification.object
    return {
        "event": notification.event,
        "id": payload.get("id"),
        "status": payload.get("status"),
        "amount": float(payload.get("amount", {}).get("value", 0)),
        "currency": payload.get("amount", {}).get("currency", "RUB"),
        "metadata": payload.get("metadata"),
    }


__all__ = ["YooKassaClient", "PaymentResponse", "parse_webhook_event"]
