from __future__ import annotations

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from ..config import Settings
from ..database.session import Database
from .handlers import menu, release
from .middlewares.db import DatabaseSessionMiddleware
from .middlewares.settings import SettingsMiddleware


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
