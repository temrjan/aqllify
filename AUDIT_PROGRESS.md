# Audit progress — REVIEW 2026-05-07

> Трекер выполнения работ по аудиту от 2026-05-07. Источник находок: `REVIEW_2026-05-07.md` (60+ пунктов после дедупликации) + `.review/postgres-review.json` (20) + `frontend/.review-typescript-findings.json` (25).
>
> **База аудита:** commit `77e074d`. Все статусы проверяются от этой точки.
>
> **Статусы:** `⬜ open` · `🟡 partial` · `✅ done` (с указанием коммита) · `⏭️ won't fix` (с обоснованием)
>
> **Обновлять при каждом фиксе:** менять статус, ставить дату и хеш коммита, кратко описывать что сделано.

---

## 📊 Сводка

| Категория | Всего | ✅ | 🟡 | ⬜ | ⏭️ |
|-----------|-------|-----|-----|-----|-----|
| 🔴 BLOCKING | 16 | 3 | 0 | 13 | 0 |
| 🟠 IMPORTANT — Backend Python | 12 | 1 | 0 | 11 | 0 |
| 🟠 IMPORTANT — Frontend TS | 14 | 0 | 0 | 14 | 0 |
| 🟠 IMPORTANT — Postgres | 8 | 0 | 0 | 8 | 0 |
| 🟠 IMPORTANT — Tests | 6 | 0 | 0 | 6 | 0 |
| 🟠 IMPORTANT — Docker | 11 | 1 | 0 | 10 | 0 |
| 🟡 SUGGESTION | 12 | 0 | 0 | 12 | 0 |
| ⚪ NIT | 5 | 0 | 0 | 5 | 0 |
| Postgres deep (доп.) | 20 | 0 | 0 | 20 | 0 |
| TypeScript deep (доп.) | 25 | 0 | 0 | 25 | 0 |
| **Итого уникальных** | **~80** | **5** | **0** | **~75** | **0** |

**Закрыто после аудита (commit `260cff3` от 2026-05-07 17:04, единственный post-audit коммит):**
- IMPORTANT Backend: `HTTPException(...) from e` (B904) — `auth/router.py`
- IMPORTANT Docker: `logging` driver options — caps json-file логов 10m × 5 файлов

**Готовится / в работе:** —

---

## 🔴 BLOCKING (фиксить до следующего деплоя)

### Безопасность

- ✅ **B1** — Path traversal в `create_cards_from_lesson` — `backend/src/progress/service.py`. Закрыто 2026-05-08. `safe_path` guard + Pydantic regex на `lesson_slug` + Query regex на `course` + структурный лог `path_traversal_blocked`. 5 unit-тестов в `test_security_paths.py`.
- ✅ **B2** — `_safe_path` prefix-check без разделителя — `backend/src/lessons/service.py`. Закрыто 2026-05-08. `str.startswith` → `is_relative_to`. Функция переименована `_safe_path` → `safe_path` (cross-module API). Регрессионный тест `test_blocks_sibling_prefix` точно reproduces оригинальный баг.
- ✅ **B3** — LLM fallback утекает золотой ответ — `backend/src/services/llm.py`. Закрыто 2026-05-08. Удалён string-comparison fallback. На любую ошибку — лог `llm_check_failed` (только `type(e).__name__`, без `str(e)` чтобы не echo'ить request body) + bare `raise`. Роут `check_student_answer` ловит исключение и переводит в `HTTPException(503)` через `from e` (HTTPException re-raise'ится без обёртки). 3 unit-теста с sentinel `SECRET_ANSWER` + `structlog.testing.capture_logs()` (ассертит факт записи + отсутствие утечки в логе/исключении/return).
- 🟡 **B4** — Telegram InitData HMAC — `backend/src/auth/service.py`. **Подтверждено:** `hmac.compare_digest` уже используется. **Открыто:** TTL=86400s (24h), Telegram советует 5–15 мин; нужно сократить до 3600s. _Skill-chain: `/workflow → /check → /python → /security-review → /python-review → /verify`._
- ⬜ **B5** — `complete_lesson` не проверяет существование урока — `backend/src/progress/router.py:70+`. **Подтверждено:** в текущем коде нет вызова `get_lesson(course, req.lesson_slug)` до `add_xp`. Любой `lesson_slug` начисляет XP. _Skill-chain: `/workflow fast → /python → /python-review → /verify`._

### Корректность

- ⬜ **B6** — Silent `.catch(() => {})` в CheckpointPage — `frontend/src/pages/CheckpointPage.tsx:108`. Минимум логировать. _Skill-chain: `/workflow fast → /typescript → gstack → /verify`._
- ⬜ **B7** — Синхронный `read_text` в async-пути — `backend/src/progress/service.py:158`, `backend/src/lessons/service.py:105,118`. Блокирует event loop. `asyncio.to_thread` или in-memory cache. _Skill-chain: `/workflow → /check → /python → /python-review → /verify`._
- ⬜ **B8** — Безусловный `+20 XP` стрик-бонус — `backend/src/progress/service.py:264`. На каждый `add_xp`, включая каждую SRS-карточку. 10-карточный review = +200 XP вместо +20. `xp_earned` в ответе врёт. _Skill-chain: `/workflow → /check → /python + тесты на ветки → /python-review → /verify`._

### Postgres

- ⬜ **B9** — Нет UNIQUE `(user_id, lesson_slug)` — `backend/src/progress/models.py:53`. SELECT-then-INSERT гонка. Нужна Alembic-миграция + `INSERT ... ON CONFLICT`. _Skill-chain: `/workflow → /check → /python (Alembic) → /python-review → /verify (staging→prod)`._
- ⬜ **B10** — Нет UNIQUE `(user_id, word)` в `srs_cards` — `backend/src/progress/models.py:72`. N+1 + race. UNIQUE + bulk `INSERT ... ON CONFLICT DO NOTHING`. _Skill-chain: `/workflow → /check → /python → simplify (дедуп с B9) → /python-review → /verify`._

### Tests

- ⬜ **B11** — Нулевое покрытие `/complete-lesson` end-to-end — `backend/tests/`. Параметризованный тест с реальным lesson + score `[0.0, 0.5, 1.0, 1.05]`. _Зависит от **B13**._
- ⬜ **B12** — Нет тестов на InitData HMAC — `backend/src/auth/service.py`. Tampered hash, expired auth_date, missing fields. _Зависит от **B13**._
- ⬜ **B13** — Нет `conftest.py` — `backend/tests/`. Нет async session fixture, нет TestClient, нет override `get_db`. **Корневая причина** дыр в покрытии. aiosqlite in-memory + TestClient + bypass для InitData. _Skill-chain: `/workflow → /check (aiosqlite vs testcontainers) → /python → /python-review`._

### Docker / Deploy

- ⬜ **B14** — Гонка Alembic в деплой-скрипте — `.github/workflows/ci.yml`. `up -d → sleep 5 → alembic upgrade head` нестабильно. Запускать миграцию через `docker compose run --rm backend alembic upgrade head` ДО `up -d --wait`. _Skill-chain: `/codex → /check → правка yml → /verify (staging)`._
- ⬜ **B15** — Нет rollback в деплое — `.github/workflows/ci.yml`. `git pull && build && up -d` мутирует прод in-place. Push образов в GHCR с тегом по SHA. _Skill-chain: `/codex → /check → правка ci.yml + compose → /verify (staging)`._
- ⬜ **B16** — Нет `.dockerignore` (root, backend, frontend). `.git`, `.env`, `node_modules`, `tests/`, `dist/` копируются в образы. **Не путать с docker-review B16** про unbounded logs — тот закрыт коммитом `260cff3`. _Skill-chain: `/codex → создать файлы → /verify (пересборка)`._

---

## 🟠 IMPORTANT (на этой неделе)

### Backend / Python

- ⬜ `__import__("datetime").timedelta(...)` — `progress/service.py:121,246`. Заменить на нормальный import.
- ⬜ Timezone drift: `date.today()` повсеместно (UTC) при пользователях UTC+5 (Tashkent). Streak/SRS off-by-one с 19:00–23:59 UTC. Helper `today_local()`.
- ⬜ Race в `add_xp`: нет `SELECT ... FOR UPDATE` на UserStats → двойной стрик при concurrent.
- ⬜ Latent bug в upsert: `progress/service.py:282` UPDATE-ветка не выставляет `completed=True`.
- ⬜ `get_or_create_user` без try/except IntegrityError → concurrent first-login = 500.
- ⬜ Markdown-парсер дублирован между `lessons/service.py` (`_extract_phrases`) и `progress/service.py` (`create_cards_from_lesson`) — уже разъехались (только один поддерживает `O'zbek`). Кандидат на `simplify`.
- ⬜ `COURSES_DIR` дублирован с `.parent.parent.parent.parent` в двух модулях — fragile.
- ⬜ Rate limiter — in-memory dict, под multi-worker не работает (20×N), нет eviction → memory leak.
- ⬜ `get_current_user` живёт в `auth/router.py` — должен быть в `auth/dependencies.py`.
- ⬜ `AsyncOpenAI` создан на module-import — тесты падают без `OPENAI_API_KEY`, клиент не закрывается на shutdown. Lifespan pattern.
- ✅ `raise HTTPException(...)` без `from e` (Ruff B904) — закрыто `260cff3` (`auth/router.py: chain with from e`). 2026-05-07.
- ⬜ `auth_date` max 24h — слишком широкое окно реплея (см. **B4**).
- ⬜ Startup health-check на `OPENAI_API_KEY` — после закрытия B3 пустой/невалидный ключ даёт 503 на каждый `/check-answer` без ранней диагностики. Известный долг, появился из-за фикса B3.

### Frontend / TypeScript

- ⬜ `tsconfig.json` под-strict: нет `exactOptionalPropertyTypes`, `noImplicitOverride`, `verbatimModuleSyntax`, `noUnusedLocals/Parameters`, `forceConsistentCasingInFileNames`.
- ⬜ `Exercise.type: string` вместо discriminated union (бэк имеет 8 точных типов).
- ⬜ Дублирование типов между всеми 5 страницами: `Phrase`, `Exercise`, `Lesson`, `LessonListItem`. Бэк публикует `openapi.json` — генерировать через `openapi-typescript`.
- ⬜ `saveProgress` double-fire risk: `if (saved || saving)` — render-tearing guard, не in-flight. Нужен `useRef(false)`.
- ⬜ `HapticFeedback` без try/catch в `LessonPage:213,215,266,268,283`. Помощник `safeHaptic`.
- ⬜ `HomePage.tsx:78` — O(N²) через `lessons.indexOf(lesson)` внутри `map`. `Map<slug, index>`.
- ⬜ Нет `AbortController` на fetch'и в `useEffect` — race при быстрой навигации.
- ⬜ Axios без типизации: `api.get(...)` вместо `api.get<LessonContent>(...)`. Блокировано до openapi-codegen.
- ⬜ Inconsistent error handling: 6 разных стилей `.catch` в 5 файлах. Кандидат на `simplify`.
- ⬜ `HomePage` `{lesson.score} XP` показывает 0–1 фракцию как XP — рендерит «0.5 XP», должно «50%».
- ⬜ `LessonPage` обработка 503 от `/check-answer` — после закрытия B3 LLM ошибки приходят как 503; UI должен показать retry/error, не silent fail. Известный долг от B3.
- ⬜ `ErrorBoundary` использует `window.location.href` reload — не сбрасывается при смене роута.
- ⬜ `TabBar` использует `===` вместо `NavLink` — `/lesson/*` ломает подсветку.
- ⬜ Eager-импорт всех роутов — нет `lazy()`/Suspense, big initial bundle.
- ⬜ `sourcemap: false` в prod — нечем дебажить инциденты.

### Postgres

- ⬜ Composite индекс `srs_cards(user_id, next_review)` — горячий запрос `get_due_cards`. Сейчас только single-column.
- ⬜ `last_activity_date: Date` TZ-naive vs `TIMESTAMPTZ` — дрейф со streak.
- ⬜ CHECK constraints отсутствуют: `score BETWEEN 0 AND 1`, `quality BETWEEN 0 AND 5`, `ease_factor >= 1.3`, `total_xp >= 0`, `streak_days >= 0`.
- ⬜ ENUM для `current_title` (10 фиксированных) — сейчас `String(20)`, нет защиты от опечаток.
- ⬜ `server_default=func.now()` вместо Python lambda для `created_at`.
- ⬜ Пул: `pool_pre_ping`, `statement_timeout`, `idle_in_transaction_session_timeout` не выставлены.
- ⬜ Нет backup strategy — только Docker volume, без `pg_dump` cron / WAL archiving.
- ⬜ Две commit-транзакции на SRS review (`review_card.commit()` + `add_xp.commit()`) — не атомарно.

### Tests

- ⬜ SM-2 quality boundaries не покрыты: q=2 (last incorrect), q=0, q=3 c correct_count=0/1.
- ⬜ Streak edge cases в `add_xp` — нулевое покрытие 5 веток (same day, +1 day, None, freeze, reset).
- ⬜ Title boundaries — нет тестов на exact threshold values.
- ⬜ Path traversal `_safe_path` — нет тестов на `../../etc/passwd`.
- ⬜ `check_answer` без тестов — fallback path определяет поведение во время outage.
- ⬜ CI без `--strict-markers`, без coverage gate, без `-x`. Frontend job без тестов вообще.

### Docker

- ⬜ Backend Dockerfile single-stage, бежит как root до `USER appuser` switch (если он есть).
- ⬜ `env_file: .env` инжектит секреты в env — видно через `docker inspect`. Migrate в Docker secrets.
- ⬜ Нет `cap_drop: [ALL]`, `read_only: true`, `tmpfs` для `/tmp`.
- ⬜ Лимиты тесные: 256M backend, 128M bot. CPU не ограничен нигде.
- ⬜ Frontend и bot без healthcheck — aiogram polling может silent die.
- ⬜ `npm install` вместо `npm ci` — недетерминированно.
- ⬜ `nginx:alpine` как root — switch на `nginxinc/nginx-unprivileged`.
- ⬜ `VITE_API_URL` baked at build time — образ не портируется между env.
- ✅ Logging driver options (caps json-file logs) — закрыто `260cff3` (10m × 5 файлов per container). 2026-05-07.
- ⬜ Нет Trivy/Grype scanning в CI.
- ⬜ `POSTGRES_PASSWORD` дефолтит на `tutor_password` — должен быть `${POSTGRES_PASSWORD:?required}`.

---

## 🟡 SUGGESTION (когда будет время)

- ⬜ `lessons/models.py` содержит Pydantic, не ORM — нарушает конвенцию (`models.py` = SQLAlchemy, `schemas.py` = Pydantic). Перенести в `lessons/schemas.py`.
- ⬜ `UserStatsResponse` определён, но не используется — обернуть `/progress/stats` либо удалить.
- ⬜ `course: str = "uzlearn"` как query-параметр в `/progress/complete-lesson` — несогласовано с `/lessons/{course}` (path).
- ⬜ Hardcoded `TITLES` — не сортируется гарантированно, можно через `bisect`.
- ⬜ `_extract_section` regex не терминирует на `### ` (level-3 headers).
- ⬜ `parse_qs` для InitData → должен быть `parse_qsl(init_data, keep_blank_values=True)` (стандарт Telegram).
- ⬜ Bot scheduler: `add_job` без `replace_existing=True` → `ConflictingIdError` на restart.
- ⬜ Bot scheduler: `from src.progress.models import` — bot достаёт ORM напрямую, должен через service.
- ⬜ Compose: build-only services без `image:` тега — нет rollback artifact (закроется вместе с **B15**).
- ⬜ `nginx.conf` без security headers (CSP, X-Frame-Options), без gzip, `server_tokens off`.
- ⬜ LLM markdown-stripping crash на одной строке без `\n` → `IndexError`.
- ⬜ `feedback_forward_failed` в `bot/handlers.py` — ошибка отправки админу проглатывается без лога.

---

## ⚪ NIT

- ⬜ `_check_rate_limit` — функция бросает исключение, должна быть `_assert_under_rate_limit` или возвращать bool.
- ⬜ `assert interval == round(3 * 2.5)` в `test_srs.py` — пересчитывает алгоритм под тестом, заменить на литерал `8`.
- ⬜ `parseMessage match[1] !== undefined` — мёртвая защита.
- ⬜ Биased shuffle `[...words].sort(() => Math.random() - 0.5)` в `LessonPage:84` — Fisher-Yates вместо.
- ⬜ `document.getElementById('root')!` — non-null assertion вместо проверки.

---

## 🗄️ Postgres deep review (доп. находки из `.review/postgres-review.json`)

Многие пересекаются с BLOCKING/IMPORTANT выше; здесь — оригинальный список со ссылками на строки. Нумерация P1–P20.

- ⬜ **P1** — UNIQUE на `user_lesson_progress(user_id, lesson_slug)` — high (= **B9**).
- ⬜ **P2** — UNIQUE на `srs_cards(user_id, word)` + `INSERT ON CONFLICT DO NOTHING` — high (= **B10**).
- ⬜ **P3** — Composite index `srs_cards(user_id, next_review)` — high (горячий путь `get_due_cards`).

> Note: P1=B9, P2=B10 (UNIQUE constraints) — пока ⬜. Path-traversal (B1/B2) к Postgres deep напрямую не относится.
- ⬜ **P4** — `last_activity_date` TZ-naive → drift со streak в окне 19:00–23:59 UTC — high.
- ⬜ **P5** — CHECK на `current_title IN (...)`, `total_xp >= 0`, `streak_days >= 0` — medium.
- ⬜ **P6** — CHECK на `ease_factor >= 1.3`, `correct/incorrect_count >= 0`, `interval_days >= 0` — medium.
- ⬜ **P7** — CHECK на `score BETWEEN 0 AND 1`, `xp_earned >= 0` — medium.
- ⬜ **P8** — Transaction discipline: убрать commit'ы из `review_card`/`add_xp`/`create_cards_from_lesson`, перенести в `get_db` — high.
- ⬜ **P9** — Engine config: `pool_pre_ping=True`, `pool_recycle=1800`, `statement_timeout`, `idle_in_transaction_session_timeout`, `application_name` — high.
- ⬜ **P10** — `get_active_users` + `send_evening_reminder`: N+1 + удержание DB-сессии через Telegram I/O. Сначала загрузить всё, потом отпустить сессию, потом цикл — high.
- ⬜ **P11** — Mismatch Python `default=10` vs `server_default='10'`; `default=lambda: datetime.now(...)` vs `func.now()` — medium.
- ⬜ **P12** — `completed` Boolean redundant с `completed_at IS NOT NULL`; либо drop, либо partial index `WHERE completed = true` — low.
- ⬜ **P13** — Alembic env.py: импортируется только `progress.models`. Будущие модули → autogenerate `op.drop_table`. Также не включены `compare_type`/`compare_server_default` — medium.
- ⬜ **P14** — Constraints без явных имён → `op.drop_constraint` будет guesswork. `naming_convention` в `MetaData` — low.
- ⬜ **P15** — `db` service: одно named volume, без `pg_dump` cron/WAL archiving, без `shm_size`, без `shared_buffers`, лимит 256M — high.
- ⬜ **P16** — `__import__("datetime").timedelta(...)` (= IMPORTANT) — low.
- ⬜ **P17** — `add_xp` lesson upsert: SELECT-then-branch; PG-native `ON CONFLICT DO UPDATE` правильнее (требует **P1**) — medium.
- ⬜ **P18** — `get_db` не commit/rollback на success/exception → если route забыл `commit()`, ROLLBACK при close — medium.
- ⬜ **P19** — `UserStats` 1:1 с `users` через PK/FK + `users` создаются отдельно от `user_stats` → window где `add_xp` ловит `ValueError` — low. Триггер `ensure_user_stats` или `INSERT` в одной транзакции.
- ⬜ **P20** — `word String(500)` / `translation String(500)` / `lesson_slug String(100)` — необоснованные размеры; либо TEXT + валидация на API, либо реалистичные ограничения с CHECK — low.

---

## 🎨 TypeScript deep review (доп. находки из `frontend/.review-typescript-findings.json`)

Многие пересекаются с IMPORTANT Frontend выше. Нумерация TS1–TS25.

- ⬜ **TS1** — Под-strict tsconfig (= IMPORTANT FE) — high.
- ⬜ **TS2** — `Exercise.type: string` → discriminated union 8 вариантов (= IMPORTANT FE) — high.
- ⬜ **TS3** — `saveProgress` deps + render-tearing guard → `useRef(false)` (= IMPORTANT FE) — high.
- ⬜ **TS4** — `lesson.meta?.xp_reward ?? 50` — мёртвый optional chain — medium.
- ⬜ **TS5** — `(ex.xp ?? 10)` остался после score-calc fix; backend default уже = 10, fallback dead — medium.
- ⬜ **TS6** — `HapticFeedback` без try/catch (= IMPORTANT FE) — medium.
- ⬜ **TS7** — Duplicate types между всеми 5 страницами → `openapi-typescript` codegen (= IMPORTANT FE) — medium.
- ⬜ **TS8** — Axios `api.get` без generic type, `.catch` без narrowing (`isAxiosError`) — medium.
- ⬜ **TS9** — `document.getElementById('root')!` (= NIT) — medium.
- ⬜ **TS10** — `WebApp.ready()/expand()` без try/catch и без проверки `platform` — medium.
- ⬜ **TS11** — Eager import всех роутов + нет `manualChunks` (= IMPORTANT FE) — medium.
- ⬜ **TS12** — `sourcemap: false` (= IMPORTANT FE) — low.
- ⬜ **TS13** — `noUncheckedIndexedAccess`: `lesson.exercises[i]` не нарrow в дочерних handler — medium.
- ⬜ **TS14** — `key={i}` в `build_sentence` → stable key — low.
- ⬜ **TS15** — Biased shuffle (= NIT) — low.
- ⬜ **TS16** — `setTimeout(() => scrollTo(...), 100)` magic number; нет cleanup → scroll фaerится на следующей странице — low.
- ⬜ **TS17** — `ErrorBoundary` reload через `window.location.href` (= IMPORTANT FE) — medium.
- ⬜ **TS18** — `ErrorBoundary.State.error: string` теряет stack/componentStack — low.
- ⬜ **TS19** — `TabBar` `===` vs `NavLink` (= IMPORTANT FE) — low.
- ⬜ **TS20** — `<button>` без `aria-label`; нет i18n (рус-only) — low.
- ⬜ **TS21** — `HomePage` lessons-by-block может индексироваться без guard — low.
- ⬜ **TS22** — `WebApp.initDataUnsafe.user` без narrowing — low.
- ⬜ **TS23** — Импорты типов как values (`import { Exercise }` вместо `import type`); ломается при `verbatimModuleSyntax` — low.
- ⬜ **TS24** — Нет `AbortController` в `useEffect` фетчах (= IMPORTANT FE) — medium.
- ⬜ **TS25** — `import.meta.env.VITE_API_URL` типизирован как `string | undefined`; `vite-env.d.ts` не объявляет required — low.

---

## 🛣️ Рекомендуемая последовательность (из `REVIEW_2026-05-07.md`)

1. **Этап 1 — security hot-patch:** B1, B2, B3, B4
2. **Этап 2 — корректность:** B6, B7, B8, B5
3. **Этап 3 — БД миграция:** B9, B10
4. **Этап 4 — тесты-инфра:** B13 → B11, B12
5. **Этап 5 — деплой:** B14, B15, B16
6. **Этап 6 — IMPORTANT batched по слоям:** Backend → Frontend → Postgres

---

## 🧾 Хронология изменений

| Дата | Коммит | Что закрыто |
|------|--------|-------------|
| 2026-05-08 | (этот коммит) | **BLOCKING B3** закрыт. Удалён leaky fallback в `services/llm.py` (возвращал `answer_context` через `feedback`/`corrected`). Логирование сужено до `type(e).__name__`. Роутер транслирует исключение в `HTTPException(503)` с узким re-raise для `HTTPException`. Новый `tests/test_llm_check.py` (3 теста, sentinel + `structlog.testing.capture_logs()`). 500/500 pytest passed. Известный долг (новые ⬜ пункты): startup health-check OpenAI key, frontend handling 503. |
| 2026-05-08 | `18586af` | **BLOCKING B1+B2** закрыты. `safe_path` (`is_relative_to` вместо `startswith`) + guard в `create_cards_from_lesson` + Pydantic regex на `lesson_slug` + FastAPI Query regex на `course` + structlog warning `path_traversal_blocked`. Новый `tests/test_security_paths.py` (9 тестов). 497/497 pytest passed, ruff чисто, security-review 0 findings, python-review 3 suggestion (1 закрыт — лог; 2 known-debt). |
| 2026-05-07 | `260cff3` | IMPORTANT Backend: `HTTPException ... from e` (B904) в `auth/router.py`. IMPORTANT Docker: caps json-file логов (10m × 5 per container). Дополнительно: structured logs middleware (`request_completed`, `lesson_completed`, `srs_reviewed`, `answer_checked`, `auth_failed`) — это новая функциональность, формально не из аудита, но уменьшает «слепоту» бэка. |
| 2026-05-07 | `77e074d` | Базовая точка аудита. fix: compute lesson score against actual max XP. _Ironically critiqued in TS5 (fallback `?? 10` остался)._ |

---

*Документ ведётся вручную. При каждом фиксе: обновить статус → дата → хеш коммита → одной строкой что сделано. Перепроверять после каждого `git pull`.*
