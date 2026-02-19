import asyncio

from maxapi.types import MessageCreated
from maxapi.enums.parse_mode import ParseMode

from app.bot import keyboards as kb
from app.bot.logic import USER_STATES, get_user_role_and_data
from app.dao.student import StudentDAO
from app.dao.teacher import TeacherDAO
from app.dao.result import ResultDAO
from app.dao.assignment import AssignmentDAO
from app.gigachat import ai_service

async def cmd_start(event: MessageCreated):
    user_id = event.message.sender.user_id
    if user_id in USER_STATES: del USER_STATES[user_id]
        
    role, user = await get_user_role_and_data(user_id)
    if role == "student":
        await event.message.answer(
            f"С возвращением, студент {user.full_name} ({user.group_name})! 👋", 
            attachments=[kb.kb_student_menu()])
    elif role == "teacher":
        await event.message.answer(
            f"Здравствуйте, {user.full_name}! 👋 Вы в панели преподавателя.",
              attachments=[kb.kb_teacher_menu()])
    else:
        await event.message.answer(
            "Добро пожаловать в GigaBot! 🤖\nДля начала выберите, кто вы:", 
                                   attachments=[kb.kb_auth_role()])

async def cmd_reset(event_or_msg, user_id=None):
    """
    Универсальная функция запуска сброса. 
    1. Если вызвана как команда: аргумент один (event)
    2. Если вызвана из кнопки: передаем (message, user_id)
    """
    if user_id is None:
        # Вызов как команды /reset
        current_user_id = event_or_msg.message.sender.user_id
        target_message = event_or_msg.message
    else:
        # Вызов из кнопки подтверждения
        current_user_id = user_id
        target_message = event_or_msg

    await target_message.answer(
        "⚠️ **Внимание!**\nСмена роли приведет к полному удалению вашего текущего профиля и всех результатов тестов.\n\nВы уверены?",
        attachments=[kb.kb_confirm_reset()],
        parse_mode=ParseMode.MARKDOWN
    )

async def execute_reset(user_id: int, message_to_answer):
    """Реальное удаление (выполняется только после нажатия кнопки 'Да')"""
    role, user = await get_user_role_and_data(user_id)
    
    if role == "student":
        await ResultDAO.delete(student_id=user.id)
        await StudentDAO.delete(max_id=user_id)
    elif role == "teacher":
        await AssignmentDAO.delete(author_id=user.id)
        await TeacherDAO.delete(max_id=user_id)
        
    await message_to_answer.answer("♻️ Данные успешно удалены. Используйте /start для новой регистрации.")

async def handle_ai_chat(event: MessageCreated):
    user_id = event.message.sender.user_id
    user_text = event.message.body.text
    
    # 1. Получаем текущую роль AI, которую использует ai_service
    # Нам нужно получить доступ к ai_service.current_ai_roles 
    # ВНИМАНИЕ: ai_service импортирован в main.py, но не в common.py. 
    # Давай импортируем его здесь, если его нет.
    
    # Проверяем, какая роль установлена в сервисе для этого пользователя
    current_ai_role_key = ai_service.current_ai_roles.get(user_id, ai_service.user_roles.get(user_id, 'default'))
    
    role_names = {
        "coder": "Senior Developer 💻",
        "teacher": "Учитель 🎓",
        "english": "English Tutor 🇬🇧",
        "friend": "Друг 🍕",
        "default": "Обычный помощник ♻️"
    }
    current_name = role_names.get(current_ai_role_key, "Обычный")
    
    # 2. Отправляем сообщение об ожидании ИИ И с указанием роли
    await event.message.answer(f"🤖 **AI-Ассистент активен.**\nТекущий режим: `{current_name}`", parse_mode=ParseMode.MARKDOWN)
    
    await event.message.answer("⏳ Думаю...")

    response_text = await asyncio.to_thread(
        ai_service.generate_response, 
        user_id, 
        user_text
    )
    
    await event.message.answer(text=response_text, parse_mode=ParseMode.MARKDOWN)