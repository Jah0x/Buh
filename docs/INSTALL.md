# Установка и запуск

## Требования

- Python 3.11+
- virtualenv / venv
- SQLite для разработки, PostgreSQL для продакшена
- Внешние зависимости: `libpango` и `libcairo` для WeasyPrint

## Шаги установки

1. Клонируйте репозиторий и создайте виртуальное окружение:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install --upgrade pip
   ```
2. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```
3. Скопируйте `.env.example` в `.env` и заполните значения:
   ```bash
   cp .env.example .env
   ```
4. Выполните миграции БД:
   ```bash
   alembic upgrade head
   ```
5. Запустите бота локально (режим polling):
   ```bash
   python -m app.main
   ```

## Переменные окружения

См. `.env.example` для полного списка. Критично задать `BOT_TOKEN`, `ADMIN_USERNAME`, `DB_URL`, `YOOKASSA_SHOP_ID`, `YOOKASSA_SECRET`, `PUBLIC_BASE_URL`.

## PostgreSQL

Для продакшена используйте строку подключения вида:
```
DB_URL=postgresql+psycopg://user:password@host:5432/plovbot
```

Перед запуском убедитесь, что выполнены миграции (`alembic upgrade head`).
