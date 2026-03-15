import asyncio

import structlog
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.bot.handlers import router
from src.bot.scheduler import setup_scheduler
from src.config import settings

logger = structlog.get_logger()


async def main() -> None:
    bot = Bot(token=settings.bot_token, parse_mode=ParseMode.HTML)
    dp = Dispatcher()

    dp.include_router(router)

    # Setup scheduled reminders
    scheduler = AsyncIOScheduler()
    setup_scheduler(scheduler, bot)
    scheduler.start()

    logger.info('aqllify_bot_starting')

    try:
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown()
        await bot.session.close()
        logger.info('aqllify_bot_stopped')


if __name__ == '__main__':
    asyncio.run(main())
