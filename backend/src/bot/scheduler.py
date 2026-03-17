import structlog
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select

from src.bot.handlers import webapp_url
from src.database import async_session
from src.progress.models import User, UserStats

logger = structlog.get_logger()


def setup_scheduler(scheduler: AsyncIOScheduler, bot: Bot) -> None:
    """Configure daily push notifications: morning lesson, afternoon review, evening quiz."""

    # Morning lesson — 09:00 UTC+5 (Tashkent) = 04:00 UTC
    scheduler.add_job(
        send_morning_lesson,
        "cron",
        hour=4,
        minute=0,
        args=[bot],
        id="morning_lesson",
    )

    # Afternoon review — 14:00 UTC+5 = 09:00 UTC
    scheduler.add_job(
        send_afternoon_review,
        "cron",
        hour=9,
        minute=0,
        args=[bot],
        id="afternoon_review",
    )

    # Evening reminder — 21:00 UTC+5 = 16:00 UTC
    scheduler.add_job(
        send_evening_reminder,
        "cron",
        hour=16,
        minute=0,
        args=[bot],
        id="evening_reminder",
    )

    logger.info("scheduler_configured", jobs=3)


async def get_active_users() -> list[tuple[int, int, str]]:
    """Get all users with their telegram_id, streak, title."""
    async with async_session() as db:
        result = await db.execute(
            select(
                User.telegram_id, UserStats.streak_days, UserStats.current_title
            ).join(UserStats, User.id == UserStats.user_id)
        )
        return [(row[0], row[1], row[2]) for row in result.all()]


async def send_morning_lesson(bot: Bot) -> None:
    """Morning push: new lesson available."""
    users = await get_active_users()

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📖 Начать урок",
                    web_app=WebAppInfo(url=webapp_url()),
                )
            ],
        ]
    )

    sent = 0
    for telegram_id, streak, _title in users:
        try:
            streak_text = f" 🔥{streak}" if streak > 0 else ""
            await bot.send_message(
                telegram_id,
                f"Xayrli tong! ☀️{streak_text}\n\nНовый урок готов. 5 минут — и ты станешь ближе к цели.",
                reply_markup=keyboard,
            )
            sent += 1
        except Exception:
            pass

    logger.info("morning_lesson_sent", count=sent)


async def send_afternoon_review(bot: Bot) -> None:
    """Afternoon push: SRS review cards."""
    users = await get_active_users()

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🧠 Повторить",
                    web_app=WebAppInfo(url=webapp_url("/review")),
                )
            ],
        ]
    )

    sent = 0
    for telegram_id, _streak, _title in users:
        try:
            await bot.send_message(
                telegram_id,
                "Время повторить слова! 🧠\n3 минуты — и они останутся в памяти надолго.",
                reply_markup=keyboard,
            )
            sent += 1
        except Exception:
            pass

    logger.info("afternoon_review_sent", count=sent)


async def send_evening_reminder(bot: Bot) -> None:
    """Evening push: streak reminder if no activity today."""
    users = await get_active_users()

    from datetime import date

    today = date.today()

    async with async_session() as db:
        for telegram_id, streak, _title in users:
            # Check if user was active today
            result = await db.execute(
                select(UserStats.last_activity_date)
                .join(User, User.id == UserStats.user_id)
                .where(User.telegram_id == telegram_id)
            )
            last_date = result.scalar_one_or_none()

            if last_date == today:
                continue  # Already active, skip

            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="📖 Пройти урок",
                            web_app=WebAppInfo(url=webapp_url()),
                        )
                    ],
                ]
            )

            try:
                if streak > 0:
                    await bot.send_message(
                        telegram_id,
                        f"Не потеряй streak 🔥{streak} дней!\n"
                        f"Осталось 3 часа. Урок займёт 5 минут.",
                        reply_markup=keyboard,
                    )
                else:
                    await bot.send_message(
                        telegram_id,
                        "Вечерний квиз ждёт! 🌙\n3 минуты — и день засчитан.",
                        reply_markup=keyboard,
                    )
            except Exception:
                pass

    logger.info("evening_reminder_sent")
