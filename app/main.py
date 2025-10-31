"""Application entry point."""
from __future__ import annotations

import asyncio

from aiohttp import web

from .bot import create_bot, create_dispatcher
from .config import load_settings
from .database.session import Database
from .logging import configure_logging, logger
from .payments import YooKassaClient
from .web.app import create_web_app


async def _run() -> None:
    settings = load_settings()
    configure_logging(settings.log_level)
    database = Database(settings)
    await database.init_models()

    bot = create_bot(settings)
    dispatcher = create_dispatcher(settings, database)

    payments = YooKassaClient(settings)
    bot["payments"] = payments

    web_app = create_web_app(settings, database, bot)
    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, settings.web_host, settings.web_port)
    await site.start()
    logger.info("Webhook server started on %s:%s", settings.web_host, settings.web_port)

    try:
        await dispatcher.start_polling(bot)
    finally:
        await runner.cleanup()
        await bot.session.close()


def run() -> None:
    asyncio.run(_run())


if __name__ == "__main__":
    run()
