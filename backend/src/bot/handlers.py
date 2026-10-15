import html
import time

import structlog
from aiogram import F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import CommandStart
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    WebAppInfo,
)
from sqlalchemy import func, select, update

from src.config import settings
from src.database import async_session
from src.progress.models import SrsCard, User, UserLessonProgress, UserStats

ADMIN_IDS = settings.admin_ids


def webapp_url(path: str = "") -> str:
    """Build Mini App URL with cache-busting parameter."""
    return f"{settings.frontend_url}{path}?v={int(time.time())}"


logger = structlog.get_logger()

router = Router()

DAILY_GOALS = {
    "goal_5": ("5 минут", 5),
    "goal_10": ("10 минут", 10),
    "goal_15": ("15 минут", 15),
}


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """Offer the Russian path and retain an explicit legacy-course entry."""
    user = message.from_user
    if not user:
        return

    logger.info("user_started", telegram_id=user.id, name=user.first_name)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Rus tilini o‘rganish", web_app=WebAppInfo(url=webapp_url())
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Учить узбекский", web_app=WebAppInfo(url=webapp_url("/uzbek"))
                ),
            ],
        ]
    )

    await message.answer(
        f"<b>Salom, {html.escape(user.first_name)}!</b>\n\n"
        "<b>Aqllify</b> bilan rus tilini kundalik vaziyatlarda mashq qiling.\n"
        "O‘zbekcha tushuntirishlar, qisqa suhbatlar va o‘z sur’atingizda darslar.\n\n"
        "Boshlang‘ich, o‘rta va yuqori bosqich dasturlari bilan tanishing.\n"
        "Hozir boshlang‘ich darslar mavjud.",
        reply_markup=keyboard,
    )


@router.callback_query(F.data.in_(DAILY_GOALS.keys()))
async def set_daily_goal(callback: CallbackQuery) -> None:
    """Set daily goal and show first lesson button."""
    if not callback.data or not callback.message:
        return

    goal_text, goal_minutes = DAILY_GOALS[callback.data]

    logger.info("goal_set", telegram_id=callback.from_user.id, minutes=goal_minutes)

    # Save goal to DB
    async with async_session() as db:
        await db.execute(
            update(User)
            .where(User.telegram_id == callback.from_user.id)
            .values(daily_goal_minutes=goal_minutes)
        )
        await db.commit()

    # Mini App button
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📖 Начать первый урок",
                    web_app=WebAppInfo(url=webapp_url("/uzbek")),
                )
            ],
        ]
    )

    await callback.message.edit_text(
        f"Отлично! Цель: <b>{goal_text}</b> в день.\n\n"
        f"Каждый день я буду присылать:\n"
        f"🌅 Утром — новый урок\n"
        f"☀️ Днём — повторение слов\n"
        f"🌙 Вечером — мини-квиз\n\n"
        f"Готов? Жми кнопку!",
        reply_markup=keyboard,
    )

    # Set persistent reply keyboard
    reply_kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💬 Обратная связь")],
        ],
        resize_keyboard=True,
    )
    await callback.message.answer(
        'Нажми кнопку "Учить" слева от поля ввода, чтобы открыть уроки!',
        reply_markup=reply_kb,
    )

    await callback.answer()


@router.message(F.text.in_({"/stats", "📊 Прогресс"}))
async def cmd_stats(message: Message) -> None:
    """Show stats: admin sees platform stats, others see Mini App."""
    user = message.from_user
    if not user:
        return

    # Admin — full platform stats
    if user.id in ADMIN_IDS:
        async with async_session() as db:
            total_users = (
                await db.execute(select(func.count()).select_from(User))
            ).scalar() or 0
            today_users = (
                await db.execute(
                    select(func.count())
                    .select_from(User)
                    .where(func.date(User.created_at) == func.current_date())
                )
            ).scalar() or 0
            total_lessons = (
                await db.execute(
                    select(func.count())
                    .select_from(UserLessonProgress)
                    .where(UserLessonProgress.completed.is_(True))
                )
            ).scalar() or 0
            total_cards = (
                await db.execute(select(func.count()).select_from(SrsCard))
            ).scalar() or 0
            active_today = (
                await db.execute(
                    select(func.count())
                    .select_from(UserStats)
                    .where(UserStats.last_activity_date == func.current_date())
                )
            ).scalar() or 0

            # Top 5 users by XP
            top_users = (
                await db.execute(
                    select(
                        User.first_name,
                        UserStats.total_xp,
                        UserStats.streak_days,
                        UserStats.current_title,
                    )
                    .join(UserStats, User.id == UserStats.user_id)
                    .order_by(UserStats.total_xp.desc())
                    .limit(5)
                )
            ).all()

        top_text = (
            "\n".join(
                f"  {i + 1}. {html.escape(u.first_name)} — {u.total_xp} XP, streak {u.streak_days}, {u.current_title}"
                for i, u in enumerate(top_users)
            )
            if top_users
            else "  пока нет данных"
        )

        await message.answer(
            f"📊 <b>Aqllify — Статистика курса узбекского</b>\n\n"
            f"👥 Всего пользователей: <b>{total_users}</b>\n"
            f"🆕 Новых сегодня: <b>{today_users}</b>\n"
            f"📱 Активных сегодня: <b>{active_today}</b>\n"
            f"📖 Уроков пройдено: <b>{total_lessons}</b>\n"
            f"🧠 SRS карточек: <b>{total_cards}</b>\n\n"
            f"🏆 <b>Топ-5:</b>\n{top_text}",
        )
        return

    # Regular user — open Mini App
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Rus tili natijalari",
                    web_app=WebAppInfo(url=webapp_url("/learn/progress")),
                )
            ],
        ]
    )

    await message.answer(
        "Rus tili bo‘yicha natijalaringizni ko‘ring:",
        reply_markup=keyboard,
    )


@router.message(F.text.in_({"/lesson", "📖 Урок"}))
async def cmd_lesson(message: Message) -> None:
    """Open current lesson in Mini App."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Darslarni ochish",
                    web_app=WebAppInfo(url=webapp_url()),
                )
            ],
        ]
    )

    await message.answer(
        "Darslarni ochish uchun tugmani bosing:",
        reply_markup=keyboard,
    )


@router.message(F.text.in_({"/review", "🧠 Повторить"}))
async def cmd_review(message: Message) -> None:
    """Open SRS review in Mini App."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Iboralarni takrorlash",
                    web_app=WebAppInfo(url=webapp_url("/learn/review")),
                )
            ],
        ]
    )

    await message.answer(
        "Ruscha iboralarni yana bir bor eslaymiz:",
        reply_markup=keyboard,
    )


@router.message(F.text.in_({"💬 Обратная связь", "/feedback"}))
async def cmd_feedback(message: Message) -> None:
    """Prompt user to send feedback, forward to admin."""
    await message.answer(
        "💬 <b>Обратная связь</b>\n\n"
        "Напиши свой отзыв, предложение или баг — "
        "следующее сообщение будет отправлено разработчику.",
    )


@router.message(F.reply_to_message)
async def forward_feedback(message: Message) -> None:
    """Forward replied messages to admin (for feedback flow)."""
    # Skip replies to avoid confusion


@router.message(~F.text.startswith("/"))
async def catch_feedback(message: Message) -> None:
    """Forward any text message to admin as feedback."""
    user = message.from_user
    if not user or user.id in ADMIN_IDS:
        return

    # Forward to all admins
    try:
        for admin_id in ADMIN_IDS:
            await message.bot.send_message(
                admin_id,
                f"💬 <b>Feedback от {html.escape(user.first_name)}</b> "
                f"(@{user.username or 'no_username'}, id:{user.id}):\n\n"
                f"{html.escape(message.text or '')}",
            )
        await message.answer("Спасибо за отзыв! Мы обязательно прочитаем.")
    except TelegramAPIError as exc:
        logger.warning("telegram_feedback_failed", error_type=type(exc).__name__)
        await message.answer("Спасибо за отзыв!")
