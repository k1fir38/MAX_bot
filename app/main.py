import asyncio
import logging
import aiohttp

from maxapi import Bot, Dispatcher

from app.config import settings
from app.bot.handlers import register_handlers

# --- НАСТРОЙКА SSL (Костыль для MaxAPI/Aiohttp) ---

original_init = aiohttp.TCPConnector.__init__
def insecure_init(self, *args, **kwargs):
    kwargs['ssl'] = False
    original_init(self, *args, **kwargs)
aiohttp.TCPConnector.__init__ = insecure_init

logging.basicConfig(level=logging.INFO)

async def main():
    bot = Bot(token=settings.BOT_TOKEN)
    dp = Dispatcher()

    # Регистрируем все обработчики из внешнего файла
    register_handlers(dp, bot)

    print("🚀 Бот запущен...")
    await dp.start_polling(bot, skip_updates=True)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен.")
