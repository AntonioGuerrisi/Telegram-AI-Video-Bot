import asyncio
import logging

from aiogram import Bot, Dispatcher

from bot.config import load_settings
from bot.handlers import cancel_pending_tasks, register_handlers
from bot.logger import setup_app_logger


async def main():
    settings = load_settings()
    logger = setup_app_logger(settings.log_level)
    logger.info("Starting Telegram video bot")

    bot = Bot(token=settings.bot_token)
    dp = Dispatcher()
    register_handlers(dp, settings)
    dp.shutdown.register(cancel_pending_tasks)

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped")
