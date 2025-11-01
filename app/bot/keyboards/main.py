from typing import Iterable

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

BACK_BUTTON = "↩️ Назад"


def main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎵 Музыка и релизы")],
            [KeyboardButton(text="💻 Собрать ПК"), KeyboardButton(text="🎙 Наши студии")],
            [KeyboardButton(text="📚 Курсы и обучение"), KeyboardButton(text="🔗 Полезные ссылки")],
            [KeyboardButton(text="📬 Связь с нами")],
        ],
        resize_keyboard=True,
    )


def back_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=BACK_BUTTON)]],
        resize_keyboard=True,
    )


def release_services_keyboard(options: Iterable[str]) -> ReplyKeyboardMarkup:
    rows = [[KeyboardButton(text=option)] for option in options]
    rows.append([KeyboardButton(text=BACK_BUTTON)])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def pc_modes_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Готовые сборки")],
            [KeyboardButton(text="Индивидуальная сборка")],
            [KeyboardButton(text=BACK_BUTTON)],
        ],
        resize_keyboard=True,
    )


def courses_keyboard(options: Iterable[str]) -> ReplyKeyboardMarkup:
    rows = [[KeyboardButton(text=option)] for option in options]
    rows.append([KeyboardButton(text=BACK_BUTTON)])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)
