# Changelog

## [0.1.0] — 2026-03-15 / 2026-03-16

### Первый релиз: Deploy + Блок 1

#### Добавлено
- Deploy на сервер (Docker Compose: backend + bot + frontend + postgres)
- CI/CD pipeline (GitHub Actions → SSH deploy + Alembic migrate)
- SSH deploy key для GitHub + SSH config с Host aliases
- Caddy reverse proxy (aqllify.com, app.aqllify.com, api.aqllify.com)
- Same-origin API routing (app.aqllify.com/api/* → backend)
- 12 уроков Блока 1 с узбекской кириллицей
- Checkpoint урок 12 — ролевая игра с AI (Aylin)
- HomePage — список уроков с прогрессом и замками
- Последовательное прохождение (урок N+1 открывается после N)
- Done-экран: XP, счёт, работа над ошибками, кнопка "Попробовать ещё раз"
- build_sentence UI (Duolingo-style слова-кнопки)
- dialog_reply UI (контекст + реплика бота + "Ответь:")
- Тёмная тема (все CSS через Telegram theme vars)
- ProgressPage: имя и фото из Telegram, эмодзи
- Reply Keyboard с кнопкой "Обратная связь"
- /stats команда для админа (юзеры, XP, уроки, топ-5)
- Бот: описание, short description, menu button "Учить"
- Контент-валидация (110 тестов для всех уроков)
- ErrorBoundary — показывает ошибку вместо белого экрана
- Сохранение daily_goal в БД при выборе цели

#### Исправленные баги

| # | Баг | Причина | Решение |
|---|-----|---------|---------|
| 1 | Frontend не билдится в Docker | Нет `vite-env.d.ts` — TypeScript не знает CSS Modules и `import.meta.env` | Создан `src/vite-env.d.ts` с reference types и CSS module declarations |
| 2 | Bot крашится при старте | aiogram 3.26 убрал `parse_mode` из `Bot()` | Заменён на `DefaultBotProperties(parse_mode=ParseMode.HTML)` |
| 3 | Backend healthcheck fails | `curl` нет в python:3.12-slim | Заменён на `python -c "import urllib.request; ..."` |
| 4 | Courses не видны в контейнере | `courses/` в корне проекта, а Dockerfile копирует только `backend/` | Добавлен volume mount `./courses:/courses:ro` |
| 5 | API недоступен из Mini App | Cross-origin: frontend на app.aqllify.com, API на api.aqllify.com | Same-origin routing через Caddy: app.aqllify.com/api/* → backend |
| 6 | Белые плашки фраз в тёмной теме | CSS: `--bg-card: #F9FAFB` и `--border: #E5E7EB` захардкожены | Заменены на `var(--tg-secondary)` и `color-mix()` от `--tg-text` |
| 7 | TabBar белый фон в тёмной теме | `background: #ffffff` и `color: #9CA3AF` захардкожены | Заменены на `var(--tg-bg)` и `var(--tg-hint)` |
| 8 | Эмодзи отображаются как `&#11088;` | HTML entities в JSX рендерятся как текст, не как HTML | Заменены на Unicode escapes (`'\u2B50'`) или прямые эмодзи |
| 9 | dialog_reply показывает пустой промпт | Фронт показывал `ex.prompt` (пустой), игнорируя `context` и `bot_says` | Добавлен специальный рендер для dialog_reply с context + bot_says |
| 10 | SRS карточки с неправильным переводом | `create_cards_from_lesson` брал `cells[1]` (кириллица) вместо `cells[2]` (русский) | Исправлен парсер: 3-колоночная таблица → word=cells[0], translation=cells[2] |
| 11 | Дубликаты в user_lesson_progress | `add_xp` создавал новую запись при каждом прохождении | Добавлен upsert: проверка существующей записи, обновление score/xp |
| 12 | Белый экран после "Завершить" (3x) | `useEffect` для save-progress стоял ПОСЛЕ conditional returns — нарушение React Rules of Hooks | Все useEffect перемещены наверх; save вызывается из click handler напрямую |
| 13 | Кнопка "Завершить" скрыта за клавиатурой | На мобильном клавиатура закрывает footer с кнопкой | После check-answer: `blur()` закрывает клавиатуру, `scrollTo` скроллит вниз |
| 14 | Прогресс не сохраняется в БД | `useEffect` для save не срабатывал из-за React batching | `saveProgress()` вызывается напрямую в `handleNext` при клике |
| 15 | LLM иногда отмечает правильный ответ как неправильный | Промпт недостаточно строгий | Усилен промпт: "NEVER mark a correct answer as wrong", принимать любой регистр/пунктуацию |
| 16 | `Vaalaykum assalom` — ответ не изучен в уроке | Фраза в грамматике и диалоге, но не в таблице фраз | Добавлена в таблицу фраз + подсказка в dialog_reply задании |
| 17 | HTML injection через имя пользователя | `first_name` с символами `<>` ломает HTML parse в aiogram | `html.escape()` для всех пользовательских данных в сообщениях |
