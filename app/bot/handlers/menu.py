from __future__ import annotations

from dataclasses import dataclass

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.config import Settings
from app.bot.handlers.release import prompt_release_services
from app.bot.keyboards.main import (
    BACK_BUTTON,
    back_keyboard,
    courses_keyboard,
    main_menu,
    pc_modes_keyboard,
)
from app.bot.states import MenuStates, PCBuildStates

router = Router()

MENU_MUSIC = "🎵 Музыка и релизы"
MENU_PC = "💻 Собрать ПК"
MENU_STUDIOS = "🎙 Наши студии"
MENU_COURSES = "📚 Курсы и обучение"
MENU_LINKS = "🔗 Полезные ссылки"
MENU_CONTACTS = "📬 Связь с нами"

PC_READY = "Готовые сборки"
PC_CUSTOM = "Индивидуальная сборка"

READY_BUILDS = [
    ("Эконом", "XX ₽"),
    ("Мид", "XX ₽"),
    ("Про", "XX ₽"),
    ("Продюсер", "XX ₽"),
    ("Ultimate", "XX ₽"),
]

HELPFUL_LINKS = [
    ("Бесплатные плагины", "https://t.me/vstplov"),
    ("Бесплатные семплы", "https://t.me/plovsempl"),
    ("Бесплатный клуб", "https://t.me/plovsoundclub"),
]


@dataclass(frozen=True)
class CourseInfo:
    title: str
    price: str
    link: str


COURSES = [
    CourseInfo("Бесплатный курс FL Studio", "0 ₽", "https://t.me/plovsoundclub"),
    CourseInfo("Курс по звукорежиссуре", "15 510 ₽", "https://t.me/plovsoundclub?course=sound"),
    CourseInfo("Курс по битмейкингу", "22 550 ₽", "https://t.me/plovsoundclub?course=beat"),
    CourseInfo("Полный курс (битмейкинг + сведение)", "33 300 ₽", "https://t.me/plovsoundclub?course=full"),
]

COURSE_TITLES = [course.title for course in COURSES]
COURSE_BY_TITLE = {course.title: course for course in COURSES}


@dataclass(frozen=True)
class StudioInfo:
    title: str
    address: str
    description: str


STUDIOS = [
    StudioInfo(
        "PLOV Studio — Центр",
        "Москва, м. Курская",
        "Флагманская студия с просторной вокальной комнатой и контроллерной зоной.",
    ),
    StudioInfo(
        "PLOV Studio — Юг",
        "Москва, м. Тульская",
        "Уютное пространство для записи вокала, подкастов и создания битов.",
    ),
    StudioInfo(
        "PLOV Studio — Север",
        "Москва, м. Савёловская",
        "Компактная студия с акцентом на быстрый продакшн и комфортный коворкинг.",
    ),
]


def _pc_intro_text() -> str:
    lines = ["Выбери режим сборки ПК:"]
    lines.append("• Готовые сборки — для быстрого старта")
    lines.append("• Индивидуальная сборка — расскажи о задачах, и мы поможем")
    return "\n".join(lines)


def _ready_builds_text() -> str:
    lines = ["Доступные готовые сборки:"]
    for name, price in READY_BUILDS:
        lines.append(f"• {name} — {price}")
    lines.append("")
    lines.append("Для заказа напиши @BAXSNAKE.")
    return "\n".join(lines)


def _courses_intro_text() -> str:
    lines = ["Выбери курс:"]
    for course in COURSES:
        lines.append(f"• {course.title} — {course.price}")
    lines.append("")
    lines.append("После выбора откроется страница с оплатой или заявкой.")
    return "\n".join(lines)


def _studios_text() -> str:
    lines = ["🎙 Наши студии по Москве:"]
    for studio in STUDIOS:
        lines.append("")
        lines.append(studio.title)
        lines.append(f"Адрес: {studio.address}")
        lines.append(studio.description)
        lines.append("Услуги:")
        lines.append("• Запись голоса — 3000 ₽ / час")
        lines.append("• Сведение микса — от 40 000 ₽")
        lines.append("• Сведение (бит + голос) — от 10 000 ₽")
        lines.append("• Аранжировка / бит — от 55 555 до 222 222 ₽")
        lines.append("• Обложка PRO — 5555 ₽")
        lines.append("• Обложка LIGHT (ИИ) — 2222 ₽")
        lines.append("• Гострайтинг — индивидуально")
    lines.append("")
    lines.append("Связаться со студией → @BAXSNAKE")
    return "\n".join(lines)


def _links_text() -> str:
    lines = ["Полезные ссылки:"]
    for title, url in HELPFUL_LINKS:
        lines.append(f"• {title} → {url}")
    return "\n".join(lines)


def _course_selected_text(course: CourseInfo) -> str:
    lines = [course.title]
    lines.append(f"Стоимость: {course.price}")
    lines.append(f"Оформить и оплатить → {course.link}")
    lines.append("Оплата доступна через Робокассу и Telegram Stars.")
    return "\n".join(lines)


def _contact_text(settings: Settings) -> str:
    admin = settings.admin_username or "BAXSNAKE"
    lines = ["📬 Связь с нами:"]
    lines.append(f"Telegram: @{admin}")
    lines.append("Подписка и оплата — через Робокассу и Telegram Stars.")
    return "\n".join(lines)


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


@router.message(F.text == MENU_MUSIC)
async def menu_music(message: Message, state: FSMContext) -> None:
    await state.clear()
    await prompt_release_services(message, state)


@router.message(F.text == MENU_PC)
async def menu_pc(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(MenuStates.pc)
    await message.answer(_pc_intro_text(), reply_markup=pc_modes_keyboard())


@router.message(MenuStates.pc, F.text == BACK_BUTTON)
async def menu_pc_back(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Главное меню:", reply_markup=main_menu())


@router.message(MenuStates.pc, F.text == PC_READY)
async def menu_pc_ready(message: Message) -> None:
    await message.answer(_ready_builds_text(), reply_markup=pc_modes_keyboard())


@router.message(MenuStates.pc, F.text == PC_CUSTOM)
async def menu_pc_custom(message: Message, state: FSMContext) -> None:
    await state.set_state(PCBuildStates.budget)
    await message.answer("Укажи бюджет для сборки.", reply_markup=back_keyboard())


@router.message(PCBuildStates.budget, F.text == BACK_BUTTON)
async def pc_budget_back(message: Message, state: FSMContext) -> None:
    await state.set_state(MenuStates.pc)
    await message.answer(_pc_intro_text(), reply_markup=pc_modes_keyboard())


@router.message(PCBuildStates.budget)
async def pc_budget(message: Message, state: FSMContext) -> None:
    if not message.text:
        await message.answer("Нужно указать бюджет текстом.", reply_markup=back_keyboard())
        return
    await state.update_data(pc_budget=message.text.strip())
    await state.set_state(PCBuildStates.goals)
    await message.answer("Для чего нужен ПК? Укажи основные задачи (музыка, видео, игры, продакшн).", reply_markup=back_keyboard())


@router.message(PCBuildStates.goals, F.text == BACK_BUTTON)
async def pc_goals_back(message: Message, state: FSMContext) -> None:
    await state.set_state(PCBuildStates.budget)
    await message.answer("Укажи бюджет для сборки.", reply_markup=back_keyboard())


@router.message(PCBuildStates.goals)
async def pc_goals(message: Message, state: FSMContext) -> None:
    if not message.text:
        await message.answer("Опиши задачи для ПК.", reply_markup=back_keyboard())
        return
    await state.update_data(pc_goals=message.text.strip())
    await state.set_state(PCBuildStates.wishes)
    await message.answer("Есть пожелания по комплектующим или брендам?", reply_markup=back_keyboard())


@router.message(PCBuildStates.wishes, F.text == BACK_BUTTON)
async def pc_wishes_back(message: Message, state: FSMContext) -> None:
    await state.set_state(PCBuildStates.goals)
    await message.answer("Для чего нужен ПК? Укажи задачи.", reply_markup=back_keyboard())


@router.message(PCBuildStates.wishes)
async def pc_wishes(message: Message, state: FSMContext) -> None:
    if not message.text:
        await message.answer("Добавь пожелания или напиши 'нет'.", reply_markup=back_keyboard())
        return
    await state.update_data(pc_wishes=message.text.strip())
    data = await state.get_data()
    summary = [
        "💻 Индивидуальная сборка",
        f"Бюджет: {data.get('pc_budget', '')}",
        f"Задачи: {data.get('pc_goals', '')}",
        f"Пожелания: {data.get('pc_wishes', '')}",
        "Индивидуальную сборку поможет оформить @BAXSNAKE.",
    ]
    await state.set_state(MenuStates.pc)
    await message.answer("\n".join(summary), reply_markup=pc_modes_keyboard())


@router.message(F.text == MENU_COURSES)
async def menu_courses(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(MenuStates.courses)
    await message.answer(_courses_intro_text(), reply_markup=courses_keyboard(COURSE_TITLES))


@router.message(MenuStates.courses, F.text == BACK_BUTTON)
async def menu_courses_back(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Главное меню:", reply_markup=main_menu())


@router.message(MenuStates.courses)
async def menu_course_select(message: Message) -> None:
    course = COURSE_BY_TITLE.get(message.text or "")
    if not course:
        await message.answer("Выбери курс из списка.", reply_markup=courses_keyboard(COURSE_TITLES))
        return
    await message.answer(_course_selected_text(course), reply_markup=courses_keyboard(COURSE_TITLES))


@router.message(F.text == MENU_STUDIOS)
async def menu_studios(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(MenuStates.studios)
    await message.answer(_studios_text(), reply_markup=back_keyboard())


@router.message(MenuStates.studios, F.text == BACK_BUTTON)
async def menu_studios_back(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Главное меню:", reply_markup=main_menu())


@router.message(F.text == MENU_LINKS)
async def menu_links(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(MenuStates.links)
    await message.answer(_links_text(), reply_markup=back_keyboard())


@router.message(MenuStates.links, F.text == BACK_BUTTON)
async def menu_links_back(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Главное меню:", reply_markup=main_menu())


@router.message(F.text == MENU_CONTACTS)
async def menu_contacts(message: Message, state: FSMContext, settings: Settings) -> None:
    await state.clear()
    await message.answer(_contact_text(settings), reply_markup=main_menu())


__all__ = [
    "MENU_MUSIC",
    "MENU_PC",
    "MENU_STUDIOS",
    "MENU_COURSES",
    "MENU_LINKS",
    "MENU_CONTACTS",
]
