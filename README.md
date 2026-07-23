# Aqllify — AI-помощник для изучения узбекского языка

Telegram Mini App для изучения узбекского языка с AI-проверкой ответов, spaced repetition и геймификацией.

**Bot:** [@Aqllify_bot](https://t.me/Aqllify_bot)
**Web:** [aqllify.com](https://aqllify.com) | [app.aqllify.com](https://app.aqllify.com)

---

## Возможности

- **50 уроков в 4 блоках** — полный курс A1: первые шаги, выживание в городе, повседневная жизнь, общение и культура
- **Узбекский латиница + кириллица + русский перевод** в каждом уроке
- **6 типов заданий:** перевод, обратный перевод, заполни пропуск, собери фразу, выбери ответ, ролевой диалог
- **AI-проверка ответов** (GPT-4o-mini) — понимает опечатки, транслит, кириллицу
- **Checkpoint** — ролевая игра с AI (знакомство с Aylin на узбекском)
- **SM-2 Spaced Repetition** — карточки для повторения слов
- **Геймификация** — XP, streak, титулы (Spark → Apex)
- **Последовательное прохождение** — следующий урок открывается после прохождения предыдущего
- **Работа над ошибками** — после квиза показываются неправильные ответы с правильными
- **Тёмная тема** — адаптируется под тему Telegram
- **Push-уведомления** — 3 напоминания в день (утро, день, вечер)

---

## Архитектура

```
┌─────────────────┐
│  Telegram User  │
└────────┬────────┘
         │
    ┌────┴─────┐
    ▼          ▼
┌────────┐  ┌──────────────┐
│  Bot   │  │   Mini App   │
│(aiogram)│  │ (React/Vite) │
│        │  │              │
│ • push │  │ • уроки      │
│ • SRS  │  │ • квизы      │
│  cron  │  │ • карточки   │
│ • streak│  │ • checkpoint │
│  notify│  │ • прогресс   │
└────┬───┘  └──────┬───────┘
     │             │
     └──────┬──────┘
            ▼
     ┌─────────────┐
     │  Backend    │
     │  (FastAPI)  │
     │             │
     │ • API       │
     │ • LLM proxy │
     │ • SRS engine│
     │ • Auth      │
     └──────┬──────┘
            │
     ┌──────┴──────┐
     ▼             ▼
┌──────────┐ ┌──────────┐
│ PostgreSQL│ │ OpenAI   │
│          │ │ GPT-4o-  │
│          │ │  mini    │
└──────────┘ └──────────┘
```

---

## Стек

### Backend
| Технология | Назначение |
|------------|-----------|
| Python 3.12 | Язык |
| FastAPI | API для Mini App |
| aiogram 3 | Telegram Bot |
| PostgreSQL 17 | База данных |
| SQLAlchemy 2 + asyncpg | ORM (async) |
| Alembic | Миграции |
| APScheduler | Push-уведомления (3/день) |
| OpenAI (GPT-4o-mini) | AI-проверка ответов + checkpoint диалоги |
| gTTS | Text-to-Speech (планируется) |
| structlog | Логирование |
| Pydantic Settings | Конфигурация |

### Frontend
| Технология | Назначение |
|------------|-----------|
| React 19 | UI фреймворк |
| TypeScript 5.7 | Типизация |
| Vite 6 | Сборка |
| @twa-dev/sdk | Telegram WebApp SDK |
| Zustand | State management |
| CSS Modules | Стили |
| axios | HTTP клиент |

### Инфраструктура
| Технология | Назначение |
|------------|-----------|
| Docker Compose | Оркестрация (4 сервиса) |
| Caddy | Reverse proxy + auto TLS |
| GitHub Actions | CI/CD (lint → test → deploy) |

---

## Структура проекта

```
aqllify/
├── backend/
│   ├── src/
│   │   ├── main.py              # FastAPI приложение
│   │   ├── config.py            # Pydantic Settings
│   │   ├── database.py          # SQLAlchemy async
│   │   ├── auth/                # Telegram initData HMAC валидация
│   │   ├── lessons/             # Загрузка уроков, check-answer, checkpoint
│   │   ├── progress/            # SM-2 SRS, XP, streak, титулы
│   │   ├── bot/                 # aiogram handlers, scheduler
│   │   └── services/
│   │       └── llm.py           # OpenAI integration
│   ├── alembic/                 # Миграции БД
│   ├── tests/                   # pytest (validation + unit)
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── App.tsx              # Router
│   │   ├── main.tsx             # Entry point, WebApp.ready()
│   │   ├── pages/
│   │   │   ├── HomePage.tsx     # Список уроков с прогрессом
│   │   │   ├── LessonPage.tsx   # Фразы → квиз → done
│   │   │   ├── CheckpointPage.tsx # AI ролевая игра
│   │   │   ├── ReviewPage.tsx   # SRS карточки
│   │   │   └── ProgressPage.tsx # XP, streak, титул
│   │   ├── components/
│   │   │   ├── TabBar.tsx
│   │   │   └── ErrorBoundary.tsx
│   │   └── shared/
│   │       └── api.ts           # axios + auth interceptor
│   ├── Dockerfile
│   └── package.json
│
├── courses/                     # Контент уроков (markdown + JSON)
│   └── uzlearn/
│       └── block-1/
│           ├── 01-salomlashish/
│           │   ├── lesson.md
│           │   └── exercises.json
│           ├── 02-tanishish/
│           ├── ...
│           └── 12-checkpoint/
│               ├── lesson.md
│               └── scenario.json
│
├── docker-compose.yml           # 4 сервиса: backend, bot, frontend, db
├── .github/workflows/ci.yml    # CI/CD pipeline
├── PRODUCT.md                   # Полная документация продукта
├── RESEARCH.md                  # Исследование рынка
├── CHANGELOG.md                 # История изменений и багфиксов
└── CLAUDE.md                    # Правила для AI при разработке
```

---

## API Endpoints

```
GET  /health                                    # Healthcheck
POST /api/v1/auth/login                         # Авторизация через Telegram initData
GET  /api/v1/lessons/{course}                   # Список уроков с прогрессом
GET  /api/v1/lessons/{course}/{block}/{lesson}  # Контент урока
POST /api/v1/lessons/check-answer               # AI-проверка ответа
POST /api/v1/lessons/checkpoint-dialog          # AI-диалог для checkpoint
GET  /api/v1/progress/stats                     # Статистика пользователя
GET  /api/v1/progress/review                    # SRS карточки для повторения
POST /api/v1/progress/review                    # Оценка карточки (SM-2)
POST /api/v1/progress/complete-lesson           # Завершение урока (XP + SRS)
```

---

## База данных

```
users                    # Telegram пользователи
├── telegram_id
├── first_name
├── daily_goal_minutes
└── created_at

user_stats               # XP, streak, титулы
├── total_xp
├── current_title        # spark → apex
├── streak_days
├── last_activity_date
└── streak_freeze_available

user_lesson_progress     # Прогресс по урокам
├── lesson_slug
├── completed
├── score
├── xp_earned
└── completed_at

srs_cards                # SM-2 карточки
├── word / translation
├── ease_factor
├── interval_days
├── next_review
├── correct_count
└── incorrect_count
```

---

## Запуск

### Требования
- Docker + Docker Compose
- Домен с DNS записями (A records)
- Telegram Bot Token (от @BotFather)
- OpenAI API Key

### Локально
```bash
git clone git@github.com:temrjan/aqllify.git
cd aqllify
cp .env.example .env
# Заполни .env: BOT_TOKEN, OPENAI_API_KEY
docker compose up -d
docker compose exec backend alembic upgrade head
```

### Production
```bash
# На сервере
git clone git@github.com:temrjan/aqllify.git /opt/aqllify
cp .env.example .env
# Заполни .env с production значениями
docker compose up -d
docker compose exec backend alembic upgrade head

# Caddy config (reverse proxy)
# app.aqllify.com → frontend + /api/* → backend
# api.aqllify.com → backend
```

### CI/CD
Push в `main` → GitHub Actions:
1. Lint (ruff)
2. Tests (pytest)
3. Deploy (SSH → git pull → docker compose build → up → alembic migrate)

---

## Тесты

```bash
# Все тесты
docker compose exec backend python -m pytest tests/ -v

# Только валидация контента (110 тестов)
docker compose exec backend python -m pytest tests/test_content_validation.py -v

# SM-2 алгоритм (15 тестов)
docker compose exec backend python -m pytest tests/test_srs.py -v
```

### Валидация контента проверяет:
- Все обязательные поля в lesson.md (title, block, lesson, xp_reward)
- Минимум 3 фразы с кириллицей в каждом уроке
- 10 заданий с правильными полями для каждого типа
- Микс типов заданий (не более 50% choice)
- Грамматика без markdown мусора
- XP > 0 для каждого задания

---

## Создание контента

Подробный гайд: см. Memory → `aqllify-block-creation-guide.md`

Краткий формат урока:
```
courses/uzlearn/block-N/XX-slug/
├── lesson.md         # Фразы (3 колонки: узб | кириллица | рус)
│                     # + грамматика + мини-диалог + домашка
└── exercises.json    # 10 заданий разных типов
```

---

## Расходы

| Компонент | Стоимость |
|-----------|----------|
| Сервер | ~$5-10/мес (VPS) |
| OpenAI API | ~$1-2/мес на 100 активных юзеров |
| Домен | ~$10/год |
| TLS, CI/CD, PostgreSQL | Бесплатно |

---

## Roadmap

- [x] Курс A1: 50 уроков в 4 блоках
- [ ] Аудио произношение (Google TTS)
- [ ] Семейный leaderboard
- [ ] A2 курс (уроки 51-100)
- [ ] TechLit курс (техническая грамотность)

---

## Лицензия

[GNU AGPL-3.0](LICENSE)
