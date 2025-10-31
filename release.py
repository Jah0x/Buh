# ------------------------------------
# handlers/release.py — FSM релиза
# ------------------------------------
import os
import asyncio
from datetime import datetime
from typing import Optional

from aiogram import Router, F
from aiogram.types import Message, InputFile
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from PIL import Image

from config import BASE_DIR, ADMIN_USERNAME
from keyboards import main_menu, back_button
from db.database import add_release

router = Router()
BACK = "⬅️ Назад"

class ReleaseStates(StatesGroup):
    TRACK_UPLOAD = State()
    COVER_UPLOAD = State()
    TRACK_NAME = State()
    AUTHORS = State()
    DESCRIPTION = State()
    RELEASE_DATE = State()
    EMAIL = State()

async def download_from_telegram(bot, file_id: str, dst_path: str, retries: int = 3):
    last_exc: Optional[Exception] = None
    for i in range(retries):
        try:
            tg_file = await bot.get_file(file_id, request_timeout=600)
            os.makedirs(os.path.dirname(dst_path), exist_ok=True)
            await bot.download_file(tg_file.file_path, destination=dst_path, timeout=600)
            return
        except Exception as e:
            last_exc = e
            await asyncio.sleep(1.5 * (i + 1))
    if last_exc:
        raise last_exc

def probe_image(path: str):
    with Image.open(path) as img:
        return img.size, img.format

@router.message(ReleaseStates.TRACK_UPLOAD, F.text == BACK)
@router.message(ReleaseStates.COVER_UPLOAD, F.text == BACK)
@router.message(ReleaseStates.TRACK_NAME, F.text == BACK)
@router.message(ReleaseStates.AUTHORS, F.text == BACK)
@router.message(ReleaseStates.DESCRIPTION, F.text == BACK)
@router.message(ReleaseStates.RELEASE_DATE, F.text == BACK)
@router.message(ReleaseStates.EMAIL, F.text == BACK)
async def fsm_back(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Окей, вернулись в главное меню.", reply_markup=main_menu())

@router.message(ReleaseStates.TRACK_UPLOAD, F.document | F.audio)
async def handle_track_upload(message: Message, state: FSMContext):
    bot = message.bot
    file_obj = message.document or message.audio
    name = (file_obj.file_name or "").lower()
    if not (name.endswith(".wav") or name.endswith(".flac")):
        await message.answer("❌ Файл должен быть WAV или FLAC. Пришли заново **как файл (document)**.",
            reply_markup=back_button())
        return
    track_path = os.path.join(BASE_DIR, "tracks", file_obj.file_name)
    try:
        await download_from_telegram(bot, file_obj.file_id, track_path, retries=3)
    except Exception:
        await message.answer("⚠️ Не удалось скачать трек. Попробуй ещё раз.", reply_markup=back_button())
        return
    await state.update_data(track_file=track_path)
    await message.answer("✅ Трек получен! Теперь пришли **обложку** JPG/PNG.", reply_markup=back_button())
    await state.set_state(ReleaseStates.COVER_UPLOAD)
