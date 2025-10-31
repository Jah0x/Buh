from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.config import Settings
from app.bot.keyboards.main import back_keyboard, main_menu
from app.bot.states import ReleaseStates

router = Router()

MENU_RELEASE = "🎵 Выпуск релиза"
MENU_DOCS = "📚 Документация"
MENU_CONTACTS = "📞 Контакты"
BACK = "⬅️ Назад"


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        f"Привет, {message.from_user.first_name or 'друг'}! Я PLOV BOT. Выбери действие:",
        reply_markup=main_menu(),
    )


@router.message(Command("menu"))
async def cmd_menu(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Главное меню:", reply_markup=main_menu())


@router.message(lambda m: m.text == MENU_RELEASE)
async def start_release_flow(message: Message, state: FSMContext) -> None:
    await state.set_state(ReleaseStates.track_upload)
    await message.answer(
        "Пришли трек в формате WAV или FLAC как файл (document).",
        reply_markup=back_keyboard(),
    )


@router.message(lambda m: m.text == MENU_DOCS)
async def show_docs(message: Message) -> None:
    await message.answer(
        "Документация доступна в репозитории /docs. Кратко: README, INSTALL, OPERATIONS, DB, PAYMENT, PRIVACY_CONSENT, CONTRACTS, SECURITY.",
        reply_markup=main_menu(),
    )


@router.message(lambda m: m.text == MENU_CONTACTS)
async def show_contacts(message: Message, settings: Settings) -> None:
    admin_username = settings.admin_username if settings and settings.admin_username else "admin"
    await message.answer(f"Связь с администратором: @{admin_username}", reply_markup=main_menu())
