# Tutor Agent

**Codex:** `~/Codex/standards/` — стандарты разработки
**Agentic loop:** `temrjan/devops-agent` — aiogram 3 + Anthropic

## Архитектура: Гибрид

```
Бот (aiogram) = триггер: push, SRS cron, streak, титулы
Mini App (React) = обучение: уроки, квизы, карточки, прогресс
Backend (FastAPI) = API: auth, SRS engine, LLM proxy, progress
```

## Стек
- **Backend:** Python 3.12, FastAPI, aiogram 3, PostgreSQL, APScheduler, anthropic/openai, gTTS
- **Frontend:** React 19, TypeScript, Vite, @twa-dev/sdk, Zustand, CSS Modules
- **Deploy:** Docker на 7demo

## Pipeline
```
Локально → git push → CI → CD → Production
```

## Ключевые документы
- `PRODUCT.md` — полная система обучения: SM-2, spiral, 3 сессии/день, типы заданий, титулы, MVP фазы
- `RESEARCH.md` — исследование: ТОП-5 платформ, источники узбекского контента, Aleem анализ

## Правила
- Backend: `~/Codex/standards/fastapi.md` + `python.md` + `postgresql.md`
- Frontend: `~/Codex/standards/react.md` + `typescript.md` + `telegram-miniapp.md`
- Архитектура: `~/Codex/standards/architecture.md`
- Контент уроков — markdown + json файлы, не хардкод
- LLM проверяет ответы (понимает смысл, не сравнивает строки)
