import asyncio
import logging
import aiohttp

# Отключаем проверку SSL
original_init = aiohttp.TCPConnector.__init__
def insecure_init(self, *args, **kwargs):
    kwargs['ssl'] = False
    original_init(self, *args, **kwargs)
aiohttp.TCPConnector.__init__ = insecure_init

from maxapi import Bot, Dispatcher, F
from maxapi.types import MessageCreated, Command, MessageCallback
from maxapi.enums.parse_mode import ParseMode

from maxapi.types.attachments.attachment import ButtonsPayload
from maxapi.types.attachments.buttons import CallbackButton

from app.config import settings
from app.service import ai_service

logging.basicConfig(level=logging.INFO)

bot = Bot(token=settings.BOT_TOKEN)
dp = Dispatcher()

# ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ ДЛЯ ОТВЕТОВ

RESPONSES = {
    "coder": "💻 Режим Senior Developer включен!",
    "teacher": "🎓 Режим учителя включен. Что разберем?",
    "english": "🇬🇧 English Tutor mode enabled. How are you?",
    "friend": "🍕 Режим друга включен. Че как, бро?",
    "default": "♻️ Режим сброшен до обычного. История очищена."
}

async def set_role_logic(event: MessageCreated, role: str):
    user_id = event.message.sender.user_id
    ai_service.change_role(user_id, role)
    await event.message.answer(text=RESPONSES.get(role, "Режим изменен."))

# КЛАВИАТУРА

def get_role_keyboard():
    buttons = [
        [
            CallbackButton(text="💻 Программист", payload="set_role:coder"),
            CallbackButton(text="🎓 Учитель", payload="set_role:teacher")
        ],
        [
            CallbackButton(text="🇬🇧 English", payload="set_role:english"),
            CallbackButton(text="🍕 Друг", payload="set_role:friend")
        ],
        [
            CallbackButton(text="♻️ Сбросить всё", payload="set_role:default")
        ]
    ]
    return ButtonsPayload(buttons=buttons).pack()

# ОБРАБОТЧИКИ КОМАНД

@dp.message_created(Command('start'))
async def start_handler(event: MessageCreated):
    user_id = event.message.sender.user_id
    ai_service.clear_history(user_id)
    await event.message.answer(
        text="Привет! 👋 Я AI-помощник GigaChat.\nВыбери режим работы:",
        attachments=[get_role_keyboard()]
    )

@dp.message_created(Command('help'))
async def help_handler(event: MessageCreated):
    await event.message.answer(
        "Доступные команды:\n"
        "/coder — Программист\n"
        "/teacher — Учитель\n"
        "/english — English Tutor\n"
        "/friend — Режим друга\n"
        "/reset — Сброс режима\n"
        "/start — Главное меню"
    )

@dp.message_created(Command('coder'))
async def role_coder(event: MessageCreated):
    await set_role_logic(event, 'coder')

@dp.message_created(Command('teacher'))
async def role_teacher(event: MessageCreated):
    await set_role_logic(event, 'teacher')

@dp.message_created(Command('english'))
async def role_english(event: MessageCreated):
    await set_role_logic(event, 'english')

@dp.message_created(Command('friend'))
async def role_friend(event: MessageCreated):
    await set_role_logic(event, 'friend')

@dp.message_created(Command('reset'))
async def role_reset(event: MessageCreated):
    await set_role_logic(event, 'default')

# ОБРАБОТКА НАЖАТИЙ КНОПОК

@dp.message_callback()
async def role_callback_handler(event: MessageCallback):
    user_id = event.callback.user.user_id
    payload = event.callback.payload
    chat_id = event.message.recipient.chat_id
    
    if payload and payload.startswith("set_role:"):
        role = payload.split(":")[1]
        ai_service.change_role(user_id, role)
        
        await bot.send_message(
            chat_id=chat_id, 
            text=RESPONSES.get(role, "Режим изменен.")
        )

# ОБРАБОТКА ОБЫЧНОГО ТЕКСТА

@dp.message_created(F.message.body.text)
async def ai_chat_handler(event: MessageCreated):
    user_text = event.message.body.text
    user_id = event.message.sender.user_id
    
    # Игнорируем всё, что начинается на / (если команда не была обработана выше)
    if user_text.startswith('/'):
        return

    # Запускаем генерацию в отдельном потоке, чтобы не блокировать бота
    response_text = await asyncio.to_thread(
        ai_service.generate_response, 
        user_id, 
        user_text
    )
    
    await event.message.answer(
        text=response_text, 
        parse_mode=ParseMode.MARKDOWN
    )

async def main():
    print("🚀 Бот запущен (Исправлены обработчики команд)...")
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен.")