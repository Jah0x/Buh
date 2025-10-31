# Установка и запуск

## Предварительные требования

- Python 3.11+ и инструменты разработки (build-essential на Linux).
- Системные библиотеки Cairo/Pango/GDK-PixBuf для генерации PDF (WeasyPrint).
- SQLite для локального запуска; PostgreSQL рекомендуется для продакшена.

## Настройка окружения

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Скопируйте шаблон окружения и укажите значения переменных:

```bash
cp .env.example .env
```

Минимальный набор для запуска: `BOT_TOKEN`, `ADMIN_USERNAME`, `DB_URL`, `PUBLIC_BASE_URL`, `YOOKASSA_SHOP_ID`, `YOOKASSA_SECRET`, `LOG_LEVEL`.

## Инициализация базы данных

В активированном виртуальном окружении выполните миграции:

```bash
alembic upgrade head
```

Для PostgreSQL строка подключения имеет вид `postgresql+psycopg://user:password@host:5432/plovbot`.

## Локальный запуск

- **Polling-режим** (достаточен для разработки):
  ```bash
  python -m app.main
  ```
- **Webhook-режим** (продакшн): убедитесь, что настройки `WEB_HOST`/`WEB_PORT` соответствуют публичному адресу и настроены вебхуки в кабинете платежного провайдера.

При изменении зависимостей повторно выполните `pip install -r requirements.txt` внутри виртуального окружения.
