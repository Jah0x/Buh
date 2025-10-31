# Договоры

## Процесс

1. После успешного webhook ЮKassa формируется объект `ContractContext`.
2. `ContractService.render()` рендерит HTML-шаблон `app/contracts/templates/contract.html` и преобразует в PDF (WeasyPrint).
3. PDF сохраняется в `data/contracts/contract_release_<id>.pdf`.
4. Бот отправляет документ пользователю и обновляет статус контракта на `sent`.
5. После подписания статус можно обновить на `signed` (метод `update_contract_status`).

## Настройка

- Убедитесь, что установлены системные зависимости WeasyPrint (Cairo, Pango, GDK-PixBuf).
- Путь к шаблону можно переопределить через переменную `CONTRACT_TEMPLATE` в `.env`.
- Для кастомизации отредактируйте шаблон HTML/Jinja.

## Подпись

- Текущий процесс предполагает вручную подписанный договор (электронная подпись не интегрирована).
- После получения подписанного документа обновите статус контракта:
  ```python
  await update_contract_status(session, release_id, status="signed", signed_at=datetime.utcnow())
  ```
