from __future__ import annotations

from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from sqlalchemy.ext.asyncio import AsyncSession


class DatabaseSessionMiddleware(BaseMiddleware):
    def __init__(self, session_factory):
        super().__init__()
        self._session_factory = session_factory

    async def __call__(self, handler: Callable[[Any, Dict[str, Any]], Awaitable[Any]], event: Any, data: Dict[str, Any]) -> Any:
        async with self._session_factory() as session:                      
            data["session"] = session
            try:
                result = await handler(event, data)
                await session.commit()
                return result
            except Exception:
                await session.rollback()
                raise
