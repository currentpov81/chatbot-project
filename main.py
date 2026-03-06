import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage

from app.config import settings
from app.cache.redis_client import get_redis
from app.database.connection import create_tables
from app.handlers import start, onboarding, chat, commands
from app.middlewares.auth import RegisterMiddleware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


async def main():
    logger.info("Starting bot...")

    # Init Redis
    redis = await get_redis()

    # Init DB tables
    await create_tables()

    # FSM storage via Redis (survives restarts)
    storage = RedisStorage(redis=redis)

    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    dp = Dispatcher(storage=storage)

    # Register global middleware
    dp.message.middleware(RegisterMiddleware())
    dp.callback_query.middleware(RegisterMiddleware())

    # Register routers
    dp.include_router(start.router)
    dp.include_router(onboarding.router)
    dp.include_router(chat.router)
    dp.include_router(commands.router)

    # Drop pending updates on start
    await bot.delete_webhook(drop_pending_updates=True)

    logger.info("Bot is running. Polling...")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
