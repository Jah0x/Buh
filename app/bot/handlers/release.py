from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from PIL import Image
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.database import crud
from app.logging import logger
from app.utils.files import ensure_parent, sanitize_filename
from app.bot.keyboards.main import BACK_BUTTON, back_keyboard, main_menu, release_services_keyboard
from app.bot.states import ReleaseStates

router = Router()

MAX_TRACK_SIZE = 100 * 1024 * 1024
ALLOWED_TRACK_EXT = {".wav", ".mp3"}
ALLOWED_COVER_EXT = {".jpg", ".jpeg", ".png"}
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@dataclass(frozen=True)
class ReleaseService:
    title: str
    price: str
    note: str


RELEASE_SERVICES = (
    ReleaseService("1 релиз", "555 ₽", "без питчинга"),
    ReleaseService("1 релиз + питчинг", "1111 ₽", "включает продвижение"),
    ReleaseService("ЕР + питчинг", "3333 ₽", "мини-альбом"),
    ReleaseService("Альбом (питчинг в подарок)", "5555 ₽", "полный релиз"),
    ReleaseService("Годовая подписка", "11111 ₽", "безлимитное количество релизов"),
    ReleaseService("Питчинг отдельно", "555 ₽", "по запросу"),
    ReleaseService("Отправка инвестору", "1111 ₽", "вручную или автоматически"),
    ReleaseService("Отправка на радио", "2222 ₽", "по списку радиостанций"),
    ReleaseService("Консультация с главой лейбла", "11111 ₽", "1 час онлайн"),
)

SERVICE_BY_TITLE = {item.title: item for item in RELEASE_SERVICES}
SERVICE_TITLES = [item.title for item in RELEASE_SERVICES]


def release_services_text() -> str:
    lines = ["Выбери услугу:"]
    for item in RELEASE_SERVICES:
        line = f"{item.title} — {item.price}"
        if item.note:
            line += f" ({item.note})"
        lines.append(line)
    lines.append("")
    lines.append("После загрузки материалов сформируем заявку, сохраним её в базе и подготовим черновик договора.")
    return "\n".join(lines)


def release_services_markup():
    return release_services_keyboard(SERVICE_TITLES)


async def prompt_release_services(message: Message, state: FSMContext) -> None:
    await state.set_state(ReleaseStates.service)
    await message.answer(release_services_text(), reply_markup=release_services_markup())


async def _download_file(message: Message, file_id: str, destination: Path) -> None:
    ensure_parent(destination)
    file = await message.bot.get_file(file_id)
    await message.bot.download_file(file.file_path, destination=str(destination))


def _validate_cover(path: Path) -> None:
    with Image.open(path) as img:
        img.verify()


def _service_from_state(data: dict) -> ReleaseService:
    title = data.get("service")
    return SERVICE_BY_TITLE.get(title, RELEASE_SERVICES[0])


def _build_description(data: dict) -> str:
    service = _service_from_state(data)
    first_line = f"Услуга: {service.title} — {service.price}"
    if service.note:
        first_line += f" ({service.note})"
    parts = [
        first_line,
        f"Жанр: {data.get('genre', '')}",
        f"Соцсети: {data.get('socials', '')}",
        f"Контактный email: {data.get('contact_email', '')}",
    ]
    original_track = data.get("track_original_name")
    if original_track:
        parts.append(f"Исходное имя файла: {original_track}")
    return "\n".join(parts)


@router.message(ReleaseStates.service, F.text == BACK_BUTTON)
async def release_back_to_menu(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Главное меню:", reply_markup=main_menu())


@router.message(ReleaseStates.service)
async def select_release_service(message: Message, state: FSMContext) -> None:
    service = SERVICE_BY_TITLE.get(message.text or "")
    if not service:
        await message.answer("Выбери услугу из списка ниже.", reply_markup=release_services_markup())
        return
    await state.update_data(service=service.title)
    await state.set_state(ReleaseStates.track_upload)
    await message.answer(
        "Загрузи трек файлом WAV или MP3 (до 100 МБ).",
        reply_markup=back_keyboard(),
    )


@router.message(ReleaseStates.track_upload, F.text == BACK_BUTTON)
async def release_track_back(message: Message, state: FSMContext) -> None:
    await prompt_release_services(message, state)


@router.message(ReleaseStates.track_upload, F.document | F.audio)
async def handle_track_upload(message: Message, state: FSMContext, settings: Settings) -> None:
    file = message.document or message.audio
    if not file:
        await message.answer("Отправь трек как файл WAV или MP3.", reply_markup=back_keyboard())
        return
    filename = (file.file_name or "track").lower()
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_TRACK_EXT:
        await message.answer("Допустимы только WAV или MP3.", reply_markup=back_keyboard())
        return
    size = getattr(file, "file_size", None) or 0
    if size > MAX_TRACK_SIZE:
        await message.answer("Файл должен быть не более 100 МБ.", reply_markup=back_keyboard())
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
    await message.answer("Теперь пришли обложку JPG или PNG.", reply_markup=back_keyboard())


@router.message(ReleaseStates.track_upload)
async def handle_track_invalid(message: Message) -> None:
    await message.answer("Отправь трек файлом WAV или MP3.", reply_markup=back_keyboard())


@router.message(ReleaseStates.cover_upload, F.text == BACK_BUTTON)
async def release_cover_back(message: Message, state: FSMContext) -> None:
    await state.set_state(ReleaseStates.track_upload)
    await message.answer("Снова отправь трек WAV или MP3.", reply_markup=back_keyboard())


@router.message(ReleaseStates.cover_upload, F.photo | F.document)
async def handle_cover_upload(message: Message, state: FSMContext, settings: Settings) -> None:
    if message.photo:
        photo = message.photo[-1]
        filename = f"cover_{message.from_user.id}_{photo.file_unique_id}.jpg"
        destination = settings.covers_dir / sanitize_filename(filename)
        file_id = photo.file_id
    else:
        document = message.document
        if not document:
            await message.answer("Отправь обложку картинкой или файлом JPG/PNG.", reply_markup=back_keyboard())
            return
        filename = (document.file_name or f"cover_{document.file_unique_id}.jpg").lower()
        ext = Path(filename).suffix.lower()
        if ext not in ALLOWED_COVER_EXT:
            await message.answer("Допустимы только JPG или PNG.", reply_markup=back_keyboard())
            return
        destination = settings.covers_dir / sanitize_filename(filename)
        file_id = document.file_id
    try:
        await _download_file(message, file_id, destination)
        _validate_cover(destination)
    except Exception as exc:
        logger.error("Cover processing failed: %s", exc)
        await message.answer("Не удалось обработать обложку. Проверь файл и попробуй снова.", reply_markup=back_keyboard())
        return
    await state.update_data(cover_file=str(destination))
    await state.set_state(ReleaseStates.artist_name)
    await message.answer("Укажи имя артиста.", reply_markup=back_keyboard())


@router.message(ReleaseStates.cover_upload)
async def handle_cover_invalid(message: Message) -> None:
    await message.answer("Нужна обложка JPG или PNG.", reply_markup=back_keyboard())


@router.message(ReleaseStates.artist_name, F.text == BACK_BUTTON)
async def release_artist_back(message: Message, state: FSMContext) -> None:
    await state.set_state(ReleaseStates.cover_upload)
    await message.answer("Вернёмся к обложке. Пришли файл ещё раз.", reply_markup=back_keyboard())


@router.message(ReleaseStates.artist_name)
async def handle_artist(message: Message, state: FSMContext) -> None:
    if not message.text:
        await message.answer("Нужно указать имя артиста текстом.", reply_markup=back_keyboard())
        return
    await state.update_data(artist_name=message.text.strip())
    await state.set_state(ReleaseStates.release_title)
    await message.answer("Укажи название релиза.", reply_markup=back_keyboard())


@router.message(ReleaseStates.release_title, F.text == BACK_BUTTON)
async def release_title_back(message: Message, state: FSMContext) -> None:
    await state.set_state(ReleaseStates.artist_name)
    await message.answer("Снова укажи имя артиста.", reply_markup=back_keyboard())


@router.message(ReleaseStates.release_title)
async def handle_release_title(message: Message, state: FSMContext) -> None:
    if not message.text:
        await message.answer("Нужно указать название релиза.", reply_markup=back_keyboard())
        return
    await state.update_data(release_title=message.text.strip())
    await state.set_state(ReleaseStates.genre)
    await message.answer("Какой жанр релиза?", reply_markup=back_keyboard())


@router.message(ReleaseStates.genre, F.text == BACK_BUTTON)
async def release_genre_back(message: Message, state: FSMContext) -> None:
    await state.set_state(ReleaseStates.release_title)
    await message.answer("Укажи название релиза ещё раз.", reply_markup=back_keyboard())


@router.message(ReleaseStates.genre)
async def handle_genre(message: Message, state: FSMContext) -> None:
    if not message.text:
        await message.answer("Нужно указать жанр.", reply_markup=back_keyboard())
        return
    await state.update_data(genre=message.text.strip())
    await state.set_state(ReleaseStates.socials)
    await message.answer("Поделись ссылками на соцсети и площадки.", reply_markup=back_keyboard())


@router.message(ReleaseStates.socials, F.text == BACK_BUTTON)
async def release_socials_back(message: Message, state: FSMContext) -> None:
    await state.set_state(ReleaseStates.genre)
    await message.answer("Нужно указать жанр.", reply_markup=back_keyboard())


@router.message(ReleaseStates.socials)
async def handle_socials(message: Message, state: FSMContext) -> None:
    if not message.text:
        await message.answer("Добавь ссылки на соцсети.", reply_markup=back_keyboard())
        return
    await state.update_data(socials=message.text.strip())
    await state.set_state(ReleaseStates.contact_email)
    await message.answer("Укажи e-mail для договора.", reply_markup=back_keyboard())


@router.message(ReleaseStates.contact_email, F.text == BACK_BUTTON)
async def release_email_back(message: Message, state: FSMContext) -> None:
    await state.set_state(ReleaseStates.socials)
    await message.answer("Добавь ссылки на соцсети.", reply_markup=back_keyboard())


@router.message(ReleaseStates.contact_email)
async def handle_contact_email(message: Message, state: FSMContext, settings: Settings, session: AsyncSession) -> None:
    email = (message.text or "").strip()
    if not EMAIL_RE.match(email):
        await message.answer("Похоже на неверный e-mail. Попробуй снова.", reply_markup=back_keyboard())
        return
    await state.update_data(contact_email=email)
    await finalize_release(message, state, settings, session)


async def finalize_release(message: Message, state: FSMContext, settings: Settings, session: AsyncSession) -> None:
    data = await state.get_data()
    track_path = data.get("track_file")
    cover_path = data.get("cover_file")
    if not track_path or not cover_path:
        await message.answer("Не хватает файлов для заявки. Начнём заново.", reply_markup=back_keyboard())
        await prompt_release_services(message, state)
        return
    user = await crud.get_or_create_user(
        session,
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
    )
    service = _service_from_state(data)
    release = await crud.create_release(
        session,
        user=user,
        track_name=data.get("release_title", "Без названия"),
        artist=data.get("artist_name"),
        authors=data.get("genre"),
        description=_build_description(data),
        release_date=service.title,
        track_file=track_path,
        cover_file=cover_path,
    )
    await state.clear()
    summary_lines = [
        "Заявка отправлена!",
        f"Услуга: {service.title} — {service.price}",
        f"Артист: {release.artist or '—'}",
        f"Релиз: {release.track_name}",
        f"Контактный e-mail: {data.get('contact_email', '')}",
        "Черновик договора отправим на почту после проверки материалов.",
    ]
    await message.answer("\n".join(summary_lines), reply_markup=main_menu())


__all__ = [
    "prompt_release_services",
    "release_services_text",
    "release_services_markup",
]
