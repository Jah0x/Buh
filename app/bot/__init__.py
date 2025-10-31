from __future__ import annotations

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from app.config import Settings
from app.database.session import Database
from app.bot.handlers import menu, release
from app.bot.middlewares.db import DatabaseSessionMiddleware
from app.bot.middlewares.settings import SettingsMiddleware


def create_dispatcher(settings: Settings, database: Database) -> Dispatcher:
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    dp.include_router(menu.router)
    dp.include_router(release.router)
    dp.update.outer_middleware(SettingsMiddleware(settings))
    dp.update.outer_middleware(DatabaseSessionMiddleware(database.session_factory))
    return dp


def create_bot(settings: Settings) -> Bot:
    bot = Bot(token=settings.bot_token, parse_mode=ParseMode.HTML)
    bot["settings"] = settings
    return bot


__all__ = ["create_dispatcher", "create_bot"]
