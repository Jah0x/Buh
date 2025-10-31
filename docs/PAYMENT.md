# Оплата через Robokassa

## Переменные окружения

| Имя | Описание |
| --- | --- |
| `ROBOKASSA_MERCHANT_LOGIN` | Логин магазина в Robokassa. |
| `ROBOKASSA_PASSWORD1` | Секрет для формирования подписи на редирект и Success/Fail. |
| `ROBOKASSA_PASSWORD2` | Секрет для проверки подписи на ResultURL. |
| `ROBOKASSA_IS_TEST` | `1` — тестовый режим, `0` — боевой. |
| `ROBOKASSA_CULTURE` | Язык формы (`ru` или `en`). |
| `ROBOKASSA_SIGNATURE_ALGO` | Алгоритм подписи (`md5`, `sha256`, `sha512`). |
| `PUBLIC_BASE_URL` | Базовый URL для ссылок подтверждения договора. |
| `SMTP_HOST`/`SMTP_PORT`/`SMTP_USER`/`SMTP_PASS`/`MAIL_FROM` | Параметры SMTP-отправки договора. |

## Формулы подписи

Все дополнительные параметры передаются как `Shp_*` и участвуют в подписи в алфавитном порядке (в формате `key=value`).

- **Redirect URL:** `SignatureValue = HASH(MerchantLogin:OutSum:InvId:Password1[:Shp_*=...])`
- **ResultURL:** `SignatureValue = HASH(OutSum:InvId:Password2[:Shp_*=...])`
- **Success/Fail:** `SignatureValue = HASH(OutSum:InvId:Password1[:Shp_*=...])`

`HASH` — выбранный алгоритм (`ROBOKASSA_SIGNATURE_ALGO`), результат передаётся в верхнем регистре.

## Последовательность событий

1. Пользователь перенаправляется на форму оплаты с параметрами Robokassa.
2. После оплаты Robokassa вызывает ResultURL (серверный колбэк). Подпись проверяется на `Password2`.
3. При валидной подписи система:
   - отмечает платёж как `paid`,
   - сохраняет параметры колбэка в `payments.metadata.robokassa`,
   - генерирует PDF-договор и создаёт запись в `contracts`,
   - ставит письмо в очередь `mail_outbox` с вложением и ссылкой на `/contract/accept?token=...`.
4. Ответ ResultURL — строго `OK<InvId>`. Повторные уведомления идемпотентны.
5. Страницы Success/Fail проверяют подпись на `Password1` и отображают результат пользователю, но не влияют на зачёт платежа.
6. Воркер `mailer` отправляет письмо с договором. После успешной отправки статус контракта меняется на `sent`.
7. Получатель переходит по ссылке подтверждения, что переводит договор в статус `signed`.

## Требования к сумме

Сумма передаётся с точностью до двух знаков после запятой (`OutSum`). Значение должно совпадать на всех этапах: при формировании URL и в ResultURL.

## Сетевые ограничения

Если используется whitelist IP Robokassa, добавьте адреса провайдера в правила фаервола для доступа к ResultURL. Актуальные диапазоны публикуются в кабинете Robokassa.
