from __future__ import annotations

import asyncio

from aiogram.exceptions import TelegramNetworkError

from app.bot import create_bot, create_dispatcher
from app.config import load_settings
from app.database.session import Database
from app.logging import configure_logging, logger


async def _main() -> None:
    settings = load_settings()
    configure_logging(settings.log_level)

    database = Database(settings)
    await database.init_models()

    bot = create_bot(settings)
    dispatcher = create_dispatcher(settings, database)

    logger.info("Starting bot polling")
    try:
        await dispatcher.start_polling(bot)
    except TelegramNetworkError as error:
        logger.error("Telegram network error: %s", error)
    finally:
        await bot.session.close()


def main() -> None:
    asyncio.run(_main())


if __name__ == "__main__":
    main()
