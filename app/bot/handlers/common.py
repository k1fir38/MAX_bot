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

async def cmd_reset(event: MessageCreated):
    user_id = event.message.sender.user_id
    role, user = await get_user_role_and_data(user_id)
    
    if role == "student":
        await ResultDAO.delete(student_id=user.id)
        await StudentDAO.delete(max_id=user_id)
    elif role == "teacher":
        await AssignmentDAO.delete(author_id=user.id)
        await TeacherDAO.delete(max_id=user_id)
        
    await event.message.answer("♻️ Аккаунт сброшен. Используйте /start для новой регистрации.")

async def handle_ai_chat(event: MessageCreated):
    user_id = event.message.sender.user_id
    user_text = event.message.body.text
    
    await event.message.answer("⏳ Думаю...")
    response_text = await asyncio.to_thread(ai_service.generate_response, user_id, user_text)
    await event.message.answer(text=response_text, parse_mode=ParseMode.MARKDOWN)