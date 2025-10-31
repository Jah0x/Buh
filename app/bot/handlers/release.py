from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from PIL import Image
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.database import crud
from app.logging import logger
from app.utils.files import ensure_parent, read_text, sanitize_filename
from app.bot.keyboards.main import back_keyboard, consent_keyboard, main_menu
from app.bot.states import ReleaseStates

router = Router()

BACK = "⬅️ Назад"
CONSENT_ACCEPT = "✅ Принимаю"
CONSENT_DECLINE = "❌ Не согласен"

ALLOWED_TRACK_EXT = {".wav", ".flac"}
ALLOWED_COVER_EXT = {".jpg", ".jpeg", ".png"}
ALLOWED_COVER_SIZES = {1500, 3000, 6000}
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


async def _download_file(message: Message, file_id: str, destination: Path) -> None:
    ensure_parent(destination)
    file = await message.bot.get_file(file_id)
    await message.bot.download_file(file.file_path, destination=str(destination))


def _validate_cover(path: Path) -> None:
    with Image.open(path) as img:
        width, height = img.size
        if width != height or width not in ALLOWED_COVER_SIZES:
            raise ValueError(f"Unsupported cover size: {width}x{height}")


async def _show_consent(message: Message, state: FSMContext, settings: Settings) -> None:
    consent_text = read_text(settings.consent_text_path)
    await state.update_data(consent_text=consent_text)
    await state.set_state(ReleaseStates.consent)
    await message.answer(
        f"{consent_text}\n\nЕсли согласен, нажми \"{CONSENT_ACCEPT}\".",
        reply_markup=consent_keyboard(),
    )


@router.message(ReleaseStates.track_upload, F.text == BACK)
@router.message(ReleaseStates.cover_upload, F.text == BACK)
@router.message(ReleaseStates.track_name, F.text == BACK)
@router.message(ReleaseStates.artist, F.text == BACK)
@router.message(ReleaseStates.authors, F.text == BACK)
@router.message(ReleaseStates.description, F.text == BACK)
@router.message(ReleaseStates.release_date, F.text == BACK)
@router.message(ReleaseStates.full_name, F.text == BACK)
@router.message(ReleaseStates.email, F.text == BACK)
@router.message(ReleaseStates.consent, F.text == BACK)
async def cancel_flow(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Процесс сбора релиза отменён.", reply_markup=main_menu())


@router.message(ReleaseStates.track_upload, F.document | F.audio)
async def handle_track_upload(message: Message, state: FSMContext, settings: Settings) -> None:
    file = message.document or message.audio
    if not file:
        await message.answer("Отправь трек как файл WAV/FLAC.", reply_markup=back_keyboard())
        return
    filename = (file.file_name or "track.wav").lower()
    ext = Path(filename).suffix
    if ext not in ALLOWED_TRACK_EXT:
        await message.answer("Файл должен быть в формате WAV или FLAC.", reply_markup=back_keyboard())
        return
    sanitized_name = sanitize_filename(filename)
    destination = settings.tracks_dir / sanitized_name
    try:
        await _download_file(message, file.file_id, destination)
    except Exception as exc:
        logger.error("Track download failed: %s", exc)
        await message.answer("Не удалось скачать файл. Попробуй ещё раз.", reply_markup=back_keyboard())
        return
    await state.update_data(track_file=str(destination), track_original_name=filename)
    await state.set_state(ReleaseStates.cover_upload)
    await message.answer(
        "Теперь пришли обложку JPG/PNG 1500x1500, 3000x3000 или 6000x6000.",
        reply_markup=back_keyboard(),
    )


@router.message(ReleaseStates.track_upload)
async def handle_track_upload_invalid(message: Message) -> None:
    await message.answer("Пришли трек в формате WAV/FLAC как файл (document).", reply_markup=back_keyboard())


@router.message(ReleaseStates.cover_upload, F.photo | F.document)
async def handle_cover_upload(
    message: Message,
    state: FSMContext,
    settings: Settings,
    session: AsyncSession,
) -> None:
    if message.photo:
        photo_size = message.photo[-1]
        filename = f"cover_{message.from_user.id}_{photo_size.file_unique_id}.jpg"
        sanitized_name = sanitize_filename(filename)
        destination = settings.covers_dir / sanitized_name
        file_id = photo_size.file_id
    else:
        document = message.document
        if not document:
            await message.answer("Отправь обложку картинкой или файлом JPG/PNG.")
            return
        filename = (document.file_name or f"cover_{document.file_unique_id}.jpg").lower()
        ext = Path(filename).suffix.lower()
        if ext not in ALLOWED_COVER_EXT:
            await message.answer("Обложка должна быть JPG или PNG.", reply_markup=back_keyboard())
            return
        sanitized_name = sanitize_filename(filename)
        destination = settings.covers_dir / sanitized_name
        file_id = document.file_id
    try:
        await _download_file(message, file_id, destination)
        _validate_cover(destination)
    except Exception as exc:
        logger.error("Cover validation failed: %s", exc)
        await message.answer("Не удалось обработать обложку. Проверь формат и размер.", reply_markup=back_keyboard())
        return
    await state.update_data(cover_file=str(destination))

    existing_consent = await crud.get_latest_consent_for_user(session, message.from_user.id)
    if existing_consent:
        await state.update_data(full_name=existing_consent.full_name, email=existing_consent.email)
        await _show_consent(message, state, settings)
        return

    await state.set_state(ReleaseStates.full_name)
    await message.answer("Укажи ФИО для договора.", reply_markup=back_keyboard())


@router.message(ReleaseStates.cover_upload)
async def handle_cover_invalid(message: Message) -> None:
    await message.answer(
        "Нужно отправить обложку JPG/PNG 1500/3000/6000.", reply_markup=back_keyboard()
    )


@router.message(ReleaseStates.full_name)
async def handle_full_name(message: Message, state: FSMContext) -> None:
    if not message.text:
        await message.answer("Нужно указать ФИО.", reply_markup=back_keyboard())
        return
    await state.update_data(full_name=message.text.strip())
    await state.set_state(ReleaseStates.email)
    await message.answer("Укажи email для связи и отправки документов.", reply_markup=back_keyboard())


@router.message(ReleaseStates.email)
async def handle_email(message: Message, state: FSMContext, settings: Settings) -> None:
    email = (message.text or "").strip()
    if not EMAIL_RE.match(email):
        await message.answer("Похоже на некорректный email. Попробуй снова.", reply_markup=back_keyboard())
        return
    await state.update_data(email=email)
    await _show_consent(message, state, settings)


@router.message(ReleaseStates.track_name)
async def handle_track_name(message: Message, state: FSMContext) -> None:
    if not message.text:
        await message.answer("Нужно указать название трека текстом.", reply_markup=back_keyboard())
        return
    await state.update_data(track_name=message.text.strip())
    await state.set_state(ReleaseStates.artist)
    await message.answer("Укажи исполнителя (можно несколько).", reply_markup=back_keyboard())


@router.message(ReleaseStates.artist)
async def handle_artist(message: Message, state: FSMContext) -> None:
    if not message.text:
        await message.answer("Нужно указать исполнителя текстом.", reply_markup=back_keyboard())
        return
    await state.update_data(artist=message.text.strip())
    await state.set_state(ReleaseStates.authors)
    await message.answer("Укажи авторов и правообладателей.", reply_markup=back_keyboard())


@router.message(ReleaseStates.authors)
async def handle_authors(message: Message, state: FSMContext) -> None:
    if not message.text:
        await message.answer("Нужно указать авторов текстом.", reply_markup=back_keyboard())
        return
    await state.update_data(authors=message.text.strip())
    await state.set_state(ReleaseStates.description)
    await message.answer("Добавь описание релиза (по желанию).", reply_markup=back_keyboard())


@router.message(ReleaseStates.description)
async def handle_description(message: Message, state: FSMContext) -> None:
    await state.update_data(description=(message.text or "").strip())
    await state.set_state(ReleaseStates.release_date)
    await message.answer("Планируемая дата релиза (формат YYYY-MM-DD или текст).", reply_markup=back_keyboard())


@router.message(ReleaseStates.release_date)
async def handle_release_date(
    message: Message,
    state: FSMContext,
    settings: Settings,
    session: AsyncSession,
) -> None:
    await state.update_data(release_date=(message.text or "").strip())
    await finalize_release(message, state, settings, session)


@router.message(ReleaseStates.consent, F.text == CONSENT_DECLINE)
async def handle_consent_decline(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Без согласия мы не можем продолжить. Напиши, когда будешь готов.", reply_markup=main_menu())


@router.message(ReleaseStates.consent, F.text == CONSENT_ACCEPT)
async def handle_consent_accept(message: Message, state: FSMContext) -> None:
    await state.update_data(consent_accepted_at=datetime.now(timezone.utc).isoformat())
    await state.set_state(ReleaseStates.track_name)
    await message.answer("Спасибо! Теперь расскажи о релизе. Как называется трек?", reply_markup=back_keyboard())


@router.message(ReleaseStates.consent)
async def handle_consent_unknown(message: Message) -> None:
    await message.answer("Подтверди согласие кнопкой или нажми назад.", reply_markup=consent_keyboard())
    

async def finalize_release(
    message: Message,
    state: FSMContext,
    settings: Settings,
    session: AsyncSession,
) -> None:
    data = await state.get_data()
    if not data.get("consent_accepted_at"):
        await message.answer("Сначала подтвердите согласие.", reply_markup=consent_keyboard())
        return

    full_name = data.get("full_name")
    email = data.get("email")
    if not full_name or not email:
        await message.answer("Не хватает данных для оформления. Заполни ФИО и email.", reply_markup=back_keyboard())
        await state.set_state(ReleaseStates.full_name)
        return

    user = await crud.get_or_create_user(
        session,
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
    )

    release = await crud.create_release(
        session,
        user=user,
        track_name=data.get("track_name", "Без названия"),
        artist=data.get("artist"),
        authors=data.get("authors"),
        description=data.get("description"),
        release_date=data.get("release_date"),
        track_file=data.get("track_file"),
        cover_file=data.get("cover_file"),
    )

    accepted_at_raw = data.get("consent_accepted_at")
    accepted_at = datetime.fromisoformat(accepted_at_raw) if accepted_at_raw else datetime.now(timezone.utc)

    await crud.create_consent(
        session,
        user=user,
        release=release,
        full_name=full_name,
        email=email,
        text_version=settings.consent_version,
        text_body=data.get("consent_text", ""),
        method="telegram_button",
        accepted_at=accepted_at,
    )

    await state.clear()
    await message.answer(
        "Спасибо! Мы получили данные релиза и свяжемся с тобой после проверки.",
        reply_markup=main_menu(),
    )
