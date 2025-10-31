# -----------------------------------
# 📁 keyboards.py — кнопки и клавиатуры
# -----------------------------------
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def main_menu():
    m = ReplyKeyboardMarkup(resize_keyboard=True)
    m.add(KeyboardButton("🎵 Выпуск песен"))
    m.add(KeyboardButton("🎁 Бесплатные семплы"), KeyboardButton("🧩 Бесплатные плагины"))
    m.add(KeyboardButton("💻 Заказать сборку ПК"))
    m.add(KeyboardButton("🎙 Наши студии по Москве"))
    m.add(KeyboardButton("📚 Бесплатный курс FL Studio"))
    return m

def back_button():
    m = ReplyKeyboardMarkup(resize_keyboard=True)
    m.add(KeyboardButton("⬅️ Назад"))
    return m

def studios_menu():
    m = ReplyKeyboardMarkup(resize_keyboard=True)
    m.add(KeyboardButton("PM RECORDS"), KeyboardButton("MARCUS MASTERS"))
    m.add(KeyboardButton("ГОРЬКИЙ РЕКОРДС"))
    m.add(KeyboardButton("⬅️ Назад"))
    return m
