# -----------------------------------
# 📁 keyboards.py — кнопки и клавиатуры (aiogram v3)
# -----------------------------------
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎵 Выпуск песен")],
            [KeyboardButton(text="🎁 Бесплатные семплы"), KeyboardButton(text="🧩 Бесплатные плагины")],
            [KeyboardButton(text="💻 Заказать сборку ПК")],
            [KeyboardButton(text="🎙 Наши студии по Москве")],
            [KeyboardButton(text="📚 Бесплатный курс FL Studio")],
        ],
        resize_keyboard=True
    )

def back_button():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⬅️ Назад")]
        ],
        resize_keyboard=True
    )

def studios_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="PM RECORDS"), KeyboardButton(text="MARCUS MASTERS")],
            [KeyboardButton(text="ГОРЬКИЙ РЕКОРДС")],
            [KeyboardButton(text="⬅️ Назад")],
        ],
        resize_keyboard=True
    )
