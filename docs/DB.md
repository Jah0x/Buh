# База данных

## Технологии

- SQLAlchemy 2.0 (async engine)
- Alembic для миграций
- SQLite для разработки, PostgreSQL в продакшене

## Модели

### users
- `id` — PK
- `telegram_id` — уникальный идентификатор пользователя Telegram
- `username`, `first_name`, `last_name`
- `created_at`

### releases
- `id`
- `user_id` — FK → users
- `track_name`, `artist`, `authors`, `description`
- `release_date`
- `track_file`, `cover_file`
- `status` (pending/processing/ready)
- `created_at`

### consents
- `id`
- `user_id` — FK → users
- `release_id` — FK → releases
- `full_name`, `email`
- `text_version`, `text_body`
- `accepted_at`

### payments
- `id`
- `user_id` — FK → users
- `release_id` — FK → releases
- `provider` (yookassa)
- `provider_payment_id`
- `status`
- `amount`, `currency`
- `metadata`
- `created_at`, `confirmed_at`

### contracts
- `id`
- `user_id` — FK → users
- `release_id` — FK → releases
- `status` (drafted/sent/signed)
- `pdf_path`
- `sent_at`, `signed_at`
- `created_at`, `updated_at`

## Миграции

- Базовая ревизия: `202401010001_initial_schema.py`
- Новые ревизии создаются через `alembic revision --autogenerate`.

## Работа с сессиями

- Используйте `Database.session()` или middleware для получения `AsyncSession`.
- При ошибках происходит rollback, при успехе — commit.
