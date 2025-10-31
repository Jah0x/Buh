from __future__ import annotations

from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware

from ...config import Settings


class SettingsMiddleware(BaseMiddleware):
    def __init__(self, settings: Settings):
        super().__init__()
        self._settings = settings

    async def __call__(self, handler: Callable[[Any, Dict[str, Any]], Awaitable[Any]], event: Any, data: Dict[str, Any]) -> Any:
        data["settings"] = self._settings
        return await handler(event, data)
