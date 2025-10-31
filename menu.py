# ------------------------------------
# handlers/menu.py — главное меню/навигация
# ------------------------------------
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext

from keyboards import main_menu, back_button, studios_menu
from config import LINK_PLUGINS, LINK_SAMPLES, LINK_FL_CLUB, TEXT_BUILD_PC
from .release import ReleaseStates

router = Router()
BACK = "⬅️ Назад"

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        f"Привет, {message.from_user.first_name}! Я PLOV BOT. Выбери действие:",
        reply_markup=main_menu()
    )
