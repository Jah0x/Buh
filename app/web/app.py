from __future__ import annotations

from datetime import datetime
from aiohttp import web
from aiogram.types import FSInputFile

from ..config import Settings
from ..contracts.service import ContractContext, ContractService
from ..database.crud import get_payment_with_relations, update_contract_status, update_payment_status
from ..database.session import Database
from ..logging import logger
from ..payments import parse_webhook_event


def create_web_app(settings: Settings, database: Database, bot) -> web.Application:
    app = web.Application()
    contract_service = ContractService(settings)

    async def healthcheck(_: web.Request) -> web.Response:
        return web.json_response({"status": "ok"})

    async def yookassa_webhook(request: web.Request) -> web.Response:
        body = await request.json()
        payload = parse_webhook_event(body)
        if not payload:
            raise web.HTTPBadRequest()
        payment_id = payload["id"]
        status = payload["status"]
        async with database.session() as session:
            payment = await update_payment_status(
                session,
                provider_payment_id=payment_id,
                status=status,
                confirmed_at=datetime.utcnow() if status == "succeeded" else None,
                metadata=payload.get("metadata"),
            )
            if not payment:
                logger.warning("Payment %s not found", payment_id)
                return web.json_response({"ok": True})
            payment = await get_payment_with_relations(session, payment.provider_payment_id)
            if not payment or not payment.release:
                return web.json_response({"ok": True})
            release = payment.release
            consent = release.consent
            if status == "succeeded" and consent:
                context = ContractContext(release=release, consent=consent, payment=payment)
                pdf_path = contract_service.render(context)
                await update_contract_status(
                    session,
                    release_id=release.id,
                    status="sent",
                    pdf_path=str(pdf_path),
                    sent_at=datetime.utcnow(),
                )
                await session.commit()
                try:
                    document = FSInputFile(path=pdf_path, filename="contract.pdf")
                    await bot.send_document(
                        chat_id=release.user.telegram_id,
                        document=document,
                        caption="Ваш договор сформирован. Пожалуйста, подпишите и верните.",
                    )
                except Exception as exc:                                         
                    logger.error("Failed to send contract PDF: %s", exc)
        return web.json_response({"ok": True})

    app.router.add_get("/health", healthcheck)
    app.router.add_post("/payments/yookassa/webhook", yookassa_webhook)
    return app


__all__ = ["create_web_app"]
