import structlog
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, WebAppInfo

from src.config import settings

logger = structlog.get_logger()

router = Router()

DAILY_GOALS = {
    'goal_5': ('5 минут', 5),
    'goal_10': ('10 минут', 10),
    'goal_15': ('15 минут', 15),
}


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """Welcome message + daily goal selection."""
    user = message.from_user
    if not user:
        return

    logger.info('user_started', telegram_id=user.id, name=user.first_name)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text='🌱 5 мин', callback_data='goal_5'),
            InlineKeyboardButton(text='🌿 10 мин', callback_data='goal_10'),
            InlineKeyboardButton(text='🌳 15 мин', callback_data='goal_15'),
        ],
    ])

    await message.answer(
        f'🇺🇿 <b>Salom, {user.first_name}!</b>\n\n'
        f'Я — <b>Aqllify</b>, твой помощник в изучении узбекского языка.\n'
        f'5 минут в день — и через месяц заговоришь.\n\n'
        f'Выбери цель на день:',
        reply_markup=keyboard,
    )


@router.callback_query(F.data.in_(DAILY_GOALS.keys()))
async def set_daily_goal(callback: CallbackQuery) -> None:
    """Set daily goal and show first lesson button."""
    if not callback.data or not callback.message:
        return

    goal_text, goal_minutes = DAILY_GOALS[callback.data]

    logger.info('goal_set', telegram_id=callback.from_user.id, minutes=goal_minutes)

    # Mini App button
    webapp_url = f'{settings.frontend_url}'
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text='📖 Начать первый урок',
            web_app=WebAppInfo(url=webapp_url),
        )],
    ])

    await callback.message.edit_text(
        f'Отлично! Цель: <b>{goal_text}</b> в день.\n\n'
        f'Каждый день я буду присылать:\n'
        f'🌅 Утром — новый урок\n'
        f'☀️ Днём — повторение слов\n'
        f'🌙 Вечером — мини-квиз\n\n'
        f'Готов? Жми кнопку!',
        reply_markup=keyboard,
    )

    await callback.answer()


@router.message(F.text == '/stats')
async def cmd_stats(message: Message) -> None:
    """Show quick stats in chat."""
    user = message.from_user
    if not user:
        return

    # Open Mini App on progress page
    webapp_url = f'{settings.frontend_url}/progress'
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text='📊 Мой прогресс',
            web_app=WebAppInfo(url=webapp_url),
        )],
    ])

    await message.answer(
        'Жми кнопку, чтобы увидеть свой прогресс:',
        reply_markup=keyboard,
    )


@router.message(F.text == '/lesson')
async def cmd_lesson(message: Message) -> None:
    """Open current lesson in Mini App."""
    webapp_url = f'{settings.frontend_url}'
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text='📖 Открыть урок',
            web_app=WebAppInfo(url=webapp_url),
        )],
    ])

    await message.answer(
        'Жми кнопку для урока:',
        reply_markup=keyboard,
    )


@router.message(F.text == '/review')
async def cmd_review(message: Message) -> None:
    """Open SRS review in Mini App."""
    webapp_url = f'{settings.frontend_url}/review'
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text='🧠 Повторить слова',
            web_app=WebAppInfo(url=webapp_url),
        )],
    ])

    await message.answer(
        'Время повторить слова!',
        reply_markup=keyboard,
    )
