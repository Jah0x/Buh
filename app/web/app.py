from __future__ import annotations

from aiohttp import web

from app.config import Settings
from app.database.session import Database


def create_web_app(settings: Settings, database: Database, bot) -> web.Application:
    del settings, database, bot
    app = web.Application()

    async def healthcheck(_: web.Request) -> web.Response:
        return web.json_response({"status": "ok"})

    app.router.add_get("/health", healthcheck)
    return app


__all__ = ["create_web_app"]
