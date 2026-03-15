# Tutor Agent — Исследование

---

## ЧАСТЬ 1: Лучшие языковые платформы

### Сравнительная таблица ТОП-5

| | Duolingo | Memrise | Babbel | Pimsleur | Busuu |
|---|---|---|---|---|---|
| **Методика** | Implicit, translation | Vocab + SRS | Grammar-explicit | Audio, active recall | CEFR-aligned |
| **Геймификация** | Эталон | Средняя | Слабая | Нет | Слабая |
| **Урок** | 3-5 мин | 5-10 мин | 10-15 мин | 30 мин | 10-15 мин |
| **SRS** | Непрозрачный | Лучший | Review Manager | Graduated Interval | AI review |
| **Grammar** | Нет | Слабая | Лучший | Через контекст | Хорошая |
| **Для бота** | Высокая | Высокая | Средняя | Алгоритм — да | Средняя |

### Что берём от каждого

**Duolingo → Геймификация + привычка:**
- Streak (серия дней) — главный крючок
- XP за каждое действие
- Bite-sized уроки 3-5 мин
- Push-напоминания

**Memrise → SRS + запоминание:**
- Адаптивный SRS для каждого слова (SM-2 алгоритм)
- Daily review — бот сам присылает карточки
- Mnemonics — ассоциации к сложным словам

**Babbel → Grammar + структура:**
- Короткие grammar tips в контексте
- Уроки вокруг реальных ситуаций (рынок, такси)
- Sequential progression

**Pimsleur → Active recall:**
- Graduated Interval Recall: слово → 30 сек → 5 мин → 2 часа → день → неделя
- Active production: пиши сам, не выбирай из вариантов

**Busuu → Progression + feedback:**
- CEFR-like уровни (A1 → A2 → B1)
- AI feedback на ответы

### Что НЕ берём

| Фича | Почему |
|---|---|
| Hearts/Lives (Duolingo) | Наказание за ошибки — демотивирует |
| Leaderboards (MVP) | Overengineering, добавить позже |
| Video с носителями | Невозможно в Telegram |
| Community correction | Нужна critical mass |
| 30-мин уроки | Слишком длинно для бота |
| Голосовое распознавание | Ненадёжно в Telegram. Фаза 2 |

---

## ЧАСТЬ 2: Источники контента для узбекского

### TIER 1 — Public Domain / CC (можно использовать свободно)

| Ресурс | Тип | Лицензия | Качество |
|--------|-----|----------|----------|
| **Peace Corps Uzbek** | Полный курс + аудио, 11 тем | Public Domain | 8/10 |
| **50Languages** | 100 уроков с аудио носителей | Creative Commons | 9/10 |
| **Wikivoyage Phrasebook** | Разговорник по темам | CC BY-SA | 7/10 |
| **Uzbek Speech Corpus** | 105 ч аудио, 958 спикеров | CC BY 4.0 | 9/10 |
| **Uzbek Corpus Sample** | 100 000 предложений | Open Source | 7/10 |
| **Wiktionary Uzbek** | Глаголы, грамматика | CC BY-SA | 7/10 |

**URLs:**
- Peace Corps: https://www.livelingua.com/course/peace-corps/Uzbek_Language_Lessons
- 50Languages: https://www.50languages.com/em/learn/phrasebook/uz
- Wikivoyage: https://en.wikivoyage.org/wiki/Uzbek_phrasebook
- Speech Corpus: https://huggingface.co/datasets/issai/Uzbek_Speech_Corpus
- Text Corpus: https://github.com/elmurod1202/Uzbek-Corpus-Sample

### TIER 2 — Бесплатные (ограничения по лицензии)

| Ресурс | Тип | Для чего |
|--------|-----|----------|
| **YEP.uz** | 34+ урока с аудио | Образец структуры уроков |
| **TeachYourselfUzbek** | Агрегатор PDF учебников | Учебники DLI, Cambridge |
| **1000 Most Common Words** | Частотный список | Слово дня |
| **Pinhok 2000 words** | Частотный словарь | Прогрессивное обучение |
| **Forvo** | 5098 слов, 261 носитель | Произношение |
| **Uzbek Brian** | Таблицы спряжений | Грамматический модуль |

### Что генерировать AI

1. **Русско-узбекский контент** — большинство ресурсов англ→узб
2. **Тематические словари** — еда, транспорт, семья, рынок
3. **Ситуативные диалоги** — такси, базар, ресторан, поликлиника
4. **Упражнения и тесты** — quiz-формат для Telegram
5. **Озвучка** — Google TTS поддерживает узбекский

### Ключевой факт

**Узбекского нет в Duolingo** — огромная незанятая ниша.

---

## ЧАСТЬ 3: Архитектура MVP

### Core фичи (must have)

1. **SRS-движок** — SM-2 алгоритм, адаптивный интервал повторения per user per word
2. **Streak** — счётчик дней подряд, push-напоминания
3. **Bite-sized уроки (3-5 мин)** — по ситуациям (рынок, транспорт, приветствия)
4. **Daily review** — бот сам присылает карточки для повторения
5. **XP** — очки за действия, daily goal
6. **Active production** — user пишет ответ сам, LLM проверяет
7. **Grammar tips** — короткие пояснения в контексте
8. **Уровни** — A1.1 → A1.2 → A2.1 — чёткий прогресс

### Phase 2 (после MVP)

- AI conversation mode (свободный диалог на узбекском)
- Leaderboard (семейный)
- Voice messages (произношение)
- Badges / achievements
- Выбор тем

### Стратегия наполнения

| Модуль бота | Источник контента |
|-------------|-------------------|
| Слово дня | Pinhok 2000 + 1000mostcommonwords |
| Фразы | 50Languages (CC) + Wikivoyage (CC BY-SA) |
| Уроки | Peace Corps (PD) + AI-генерация на русском |
| Грамматика | Uzbek Brian + Wiktionary + AI |
| Диалоги | Peace Corps + AI-генерация |
| Произношение | Google TTS (узбекский поддерживается) |
| Тесты/Quiz | AI-генерация |
| Spaced Repetition | SM-2 алгоритм (собственная реализация) |
