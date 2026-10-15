# Aqllify

A Telegram Mini App for Uzbek-speaking adults learning practical Russian, with Uzbek Latin explanations and Russian Cyrillic examples. Everyday situations include introductions, arranging meetings, shopping, asking for clarification and discussing plans.

## Learning experience

- **Beginner:** 12 lessons, 48 phrases with generated Russian audio, 60 exercises and short dialogues. Listen, replay more slowly, practise recall and apply phrases in a new situation.
- **Intermediate and advanced:** curriculum outlines, entry criteria and transition goals. Full lessons are not available yet.
- **Starting point:** six optional reading, listening and response-choice questions, with manual level selection. This is an approximate recommendation, not a proficiency certificate.
- **Progress:** server-graded answers, 80% completion threshold, 40 XP once per completed lesson, retained best score and safe retries after interrupted connections.
- **Review:** recall a phrase, reveal the example and self-rate. Reviews grant no XP; intervals are 1, 3, 7 and 14 days, or 10 minutes for another practice.
- **Optional conversation:** short Russian exchanges with Uzbek feedback. GPT-6 Luna with medium reasoning is the default. Conversation does not determine grades or rewards, and the deterministic course works without an API key.

The previous Russian-to-Uzbek course remains at `/uzbek`. Its progress and reminders remain separate from the Russian course. Existing lesson, review and progress URLs still work.

## Development

Python 3.12, PostgreSQL, Node.js and a Telegram bot token are required. The backend uses FastAPI, SQLAlchemy/asyncpg and Alembic; the frontend uses React, TypeScript and Vite.

```bash
python3.12 -m venv .venv
.venv/bin/pip install -r backend/requirements.txt
cp .env.example backend/.env
# Configure DATABASE_URL, BOT_TOKEN and FRONTEND_URL in backend/.env.
# OPENAI_API_KEY is optional for the Russian course.
cd backend
PYTHONPATH=. ../.venv/bin/alembic upgrade head
PYTHONPATH=. ../.venv/bin/uvicorn src.main:app --reload
```

In another terminal:

```bash
cd frontend
npm install
VITE_API_URL=http://localhost:8000 npm run dev
```

Open the app through Telegram for signed authentication. There is no product authentication bypass for local development. The browser regression script provides its own synthetic, signed test identity.

The Compose setup mounts `courses/` read-only at `/courses`. Migration `002` adds `learning_attempts`, `learning_progress` and `learning_reviews`; it does not rewrite legacy rows. Back up the database before applying migrations to a live installation. Russian records use verified Telegram identities and the authored course version. A changed version requires an explicit data migration; old attempts are not silently regraded.

## Checks

From the project root:

```bash
.venv/bin/ruff check backend
.venv/bin/ruff format --check backend
PYTHONPATH=backend .venv/bin/pytest backend/tests -q
cd frontend
npm run type-check
npm run build
```

Database tests are skipped unless explicitly configured. For the full backend suite, provide `TEST_DATABASE_URL` pointing to a migrated disposable database and `TEST_MIGRATION_DATABASE_URL` pointing to a separate **empty** disposable database. Both database names must contain `test`. The migration test intentionally leaves its fixtures intact; use a new empty database for another run. CI creates these databases and runs both checks.

For browser regression, install Playwright separately (`.venv/bin/pip install playwright` and `.venv/bin/playwright install chromium`). Start the API at `127.0.0.1:8019` with `BOT_TOKEN=local-browser-test`, `OPENAI_API_KEY=''`, `FRONTEND_URL=http://127.0.0.1:5179` and a migrated disposable database. Start Vite on port 5179 with `VITE_API_URL=http://127.0.0.1:8019`, then run:

```bash
.venv/bin/python backend/scripts/check_russian_browser.py
```

The script checks placement, manual level choice, real audio playback, interrupted-save recovery, resume, double clicks, review and the legacy route. It sends no Telegram messages and calls no live language model.

## Content and API

`courses/russian/course.json` is the authored course source. `backend/src/learning/` validates content and exposes `/api/v1/learning`: catalog, lessons, placement, attempts/answers/completion, progress, review and optional dialogue. Protected endpoints require `X-Telegram-InitData`; public audio is restricted to the course's asset allowlist. Answer keys and AI scenario instructions are excluded from public lesson responses.

Russian audio files are included. To generate missing files after editing content:

```bash
.venv/bin/python backend/scripts/generate_russian_audio.py
```

Generation uses gTTS and requires network access; playback uses local assets. Text changes need corresponding hashed filenames. Text, audio and accepted answer alternatives need editorial review before a public course release. Automated checks do not establish learning effectiveness or certify pronunciation.

The conversation limiter is per user and per process, suitable for the current single-worker setup. Revisit it before running multiple workers. No automatic pronunciation scoring is implemented.

## Deployment

The existing GitHub workflow deploys after a successful push to `main`. Local implementation and tests do not publish a release. Live Telegram behavior, model availability/quality and deployment health need verification in the release environment.

## License

[GNU AGPL-3.0](LICENSE)
