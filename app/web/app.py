from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Dict

from aiohttp import web
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.config import Settings
from app.contracts import ContractContext, ContractService
from app.database import models
from app.database.session import Database
from app.payments.robokassa_client import RobokassaClient


async def _collect_params(request: web.Request) -> Dict[str, str]:
    if request.can_read_body:
        data = await request.post()
        if data:
            return {k: v for k, v in data.items()}
    return {k: v for k, v in request.rel_url.query.items()}


def create_web_app(settings: Settings, database: Database, bot) -> web.Application:
    app = web.Application()
    app["settings"] = settings
    app["database"] = database
    app["bot"] = bot
    app["contract_service"] = ContractService(settings)
    app["robokassa_client"] = RobokassaClient(settings)

    async def healthcheck(_: web.Request) -> web.Response:
        return web.json_response({"status": "ok"})

    async def contract_accept(request: web.Request) -> web.Response:
        token = request.query.get("token")
        if not token:
            return web.Response(status=400, text="missing token")
        database: Database = request.app["database"]
        async with database.session() as session:
            stmt = select(models.Contract).where(models.Contract.accept_token == token)
            result = await session.execute(stmt)
            contract = result.scalar_one_or_none()
            if not contract:
                return web.Response(status=404, text="contract not found")
            if contract.accept_token_used_at:
                return web.Response(status=410, text="contract already signed")
            now = datetime.now(timezone.utc)
            contract.status = "signed"
            contract.signed_at = now
            contract.accept_token_used_at = now
            await session.flush()
            await session.commit()
        return web.Response(text="Договор подписан. Благодарим за подтверждение!")

    async def robokassa_result(request: web.Request) -> web.Response:
        params = await _collect_params(request)
        client: RobokassaClient = request.app["robokassa_client"]
        if not client.verify_result(params):
            return web.Response(status=400, text="invalid signature")
        inv_id_raw = params.get("InvId")
        if not inv_id_raw:
            return web.Response(status=400, text="missing InvId")
        try:
            inv_id = int(inv_id_raw)
        except ValueError:
            return web.Response(status=400, text="invalid InvId")
        database: Database = request.app["database"]
        async with database.session() as session:
            stmt = (
                select(models.Payment)
                .options(
                    selectinload(models.Payment.release).selectinload(models.Release.consent),
                    selectinload(models.Payment.contract),
                )
                .where(models.Payment.robokassa_inv_id == inv_id)
            )
            result = await session.execute(stmt)
            payment = result.scalar_one_or_none()
            if not payment:
                return web.Response(status=404, text="payment not found")
            if payment.status != "paid":
                payment.status = "paid"
                payment.paid_at = datetime.now(timezone.utc)
                payment.is_test = params.get("IsTest", "0") == "1"
                try:
                    payment.out_sum = Decimal(params.get("OutSum", "0"))
                except (InvalidOperation, TypeError):
                    pass
            meta = payment.metadata or {}
            robokassa_meta = meta.get("robokassa")
            if not isinstance(robokassa_meta, dict):
                robokassa_meta = {}
            robokassa_meta.update(params)
            meta["robokassa"] = robokassa_meta
            payment.metadata = meta
            if not payment.release or not payment.release.consent:
                await session.flush()
                await session.commit()
                return web.Response(status=422, text="consent not found")
            contract_service: ContractService = request.app["contract_service"]
            contract = payment.contract
            if not contract:
                context = ContractContext(
                    release=payment.release,
                    consent=payment.release.consent,
                    payment=payment,
                )
                contract = await contract_service.create_contract(session, context)
                payment.contract = contract
            if not contract.mail_message_key:
                accept_link = contract_service.build_accept_link(contract)
                subject = f"Договор по релизу {payment.release.track_name}"
                html_body = (
                    f"<p>Здравствуйте, {payment.release.consent.full_name}!</p>"
                    f"<p>К договору прикреплён файл, вы можете подписать его по ссылке: "
                    f"<a href=\"{accept_link}\">Подписать договор</a>.</p>"
                )
                text_body = (
                    f"Здравствуйте, {payment.release.consent.full_name}!\n"
                    f"Договор прикреплён к письму. Подписать: {accept_link}"
                )
                await contract_service.enqueue_email(
                    session,
                    contract,
                    payment.release.consent.email,
                    subject,
                    html_body,
                    text_body,
                )
            await session.flush()
            await session.commit()
        return web.Response(text=f"OK{inv_id}")

    async def robokassa_success(request: web.Request) -> web.Response:
        params = await _collect_params(request)
        client: RobokassaClient = request.app["robokassa_client"]
        if not client.verify_success(params):
            return web.Response(status=400, text="invalid signature")
        inv_id = params.get("InvId", "")
        return web.Response(text=f"Платёж {inv_id} принят. Мы направим договор на вашу почту.")

    async def robokassa_fail(request: web.Request) -> web.Response:
        params = await _collect_params(request)
        client: RobokassaClient = request.app["robokassa_client"]
        if not client.verify_success(params):
            return web.Response(status=400, text="invalid signature")
        inv_id = params.get("InvId", "")
        return web.Response(text=f"Платёж {inv_id} не был завершён. Попробуйте ещё раз или свяжитесь с поддержкой.")

    app.router.add_get("/health", healthcheck)
    app.router.add_get("/contract/accept", contract_accept)
    app.router.add_post("/payments/robokassa/result", robokassa_result)
    app.router.add_get("/payments/robokassa/result", robokassa_result)
    app.router.add_get("/payments/robokassa/success", robokassa_success)
    app.router.add_get("/payments/robokassa/fail", robokassa_fail)
    return app


__all__ = ["create_web_app"]
