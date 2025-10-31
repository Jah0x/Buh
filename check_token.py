# C:\Bot\check_token.py
import asyncio
from aiogram import Bot
from config import API_TOKEN

async def main():
    try:
        bot = Bot(API_TOKEN)
        me = await bot.get_me()
        print("OK ✅ Бот найден:", me.username, me.id)
    except Exception as e:
        print("❌ Ошибка токена / сети:", repr(e))

asyncio.run(main())
