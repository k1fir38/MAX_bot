import asyncio
from maxapi.types import MessageCreated, MessageCallback
from maxapi.enums.parse_mode import ParseMode

from app.bot import keyboards as kb
from app.bot.logic import USER_STATES
from app.services.gigachat import ai_service

async def handle_ai_menu(event: MessageCallback):
    """Показывает меню выбора ролей AI"""

    user_id = event.callback.user.user_id
    USER_STATES[user_id] = "ai_chat_active"
    await event.message.answer(
        "🤖 **Режим AI-ассистента**\nВыберите роль, в которой я должен отвечать:",
        attachments=[kb.kb_get_ai_role()], 
        parse_mode=ParseMode.MARKDOWN
    )

async def handle_ai_role_selection(event: MessageCallback, payload: str):
    """Устанавливает выбранную роль и отправляет подтверждение"""
    user_id = event.callback.user.user_id
    role_key = payload.split(":")[1]
    
    # Устанавливаем роль в сервисе
    ai_service.set_ai_role(user_id, role_key) 
    
    # Красивые названия для вывода
    friendly_names = {
        "coder": "Senior Developer 💻",
        "teacher": "Учитель 🎓",
        "english": "English Tutor 🇬🇧",
        "friend": "Твой лучший друг 🍕",
        "default": "Обычный помощник ♻️"
    }
    friendly_name = friendly_names.get(role_key, "Ассистент")
    
    await event.message.answer(
        f"✅ **Режим изменен!**\n"
        f"Теперь я: `{friendly_name}`\n\n"
        f"История диалога очищена. Жду твой вопрос!",
        parse_mode=ParseMode.MARKDOWN
    )

async def process_ai_chat(event: MessageCreated):
    """Отправляет сообщение пользователя в GigaChat и выводит ответ"""
    user_id = event.message.sender.user_id
    user_text = event.message.body.text
    
    await event.message.answer("⏳ Думаю...") 

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