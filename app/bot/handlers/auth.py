from maxapi.types import MessageCallback, MessageCreated

from app.bot import keyboards as kb
from app.bot.logic import USER_STATES, TEMP_DATA
from app.dao.student import StudentDAO
from app.dao.teacher import TeacherDAO

async def handle_callback(event: MessageCallback, payload: str, bot):
    user_id = event.callback.user.user_id
    chat_id = event.message.recipient.chat_id

    if payload == "reg:student":
        USER_STATES[user_id] = "waiting_student_fio" 
        await bot.send_message(chat_id, text="Введите ваше ФИО (например, Иванов Иван Иванович):")
    
    elif payload == "reg:teacher":
        USER_STATES[user_id] = "waiting_teacher_name"
        await bot.send_message(chat_id=chat_id, text="Введите ваше ФИО (например, Иванов И.И.):")

async def handle_text(event: MessageCreated, state: str):
    user_id = event.message.sender.user_id
    text = event.message.body.text

    # --- СТУДЕНТ ---
    if state == "waiting_student_fio":
        TEMP_DATA[user_id] = {"full_name": text}
        USER_STATES[user_id] = "waiting_student_group"
        await event.message.answer("Отлично! Теперь введите номер вашей группы (например, ИКВТ-22):")

    elif state == "waiting_student_group":
        data = TEMP_DATA.get(user_id, {})
        fio = data.get("full_name", "Неизвестный")
        await StudentDAO.add(max_id=user_id, full_name=fio, group_name=text.upper())
        
        del USER_STATES[user_id]
        if user_id in TEMP_DATA: del TEMP_DATA[user_id]
        await event.message.answer(f"✅ Регистрация завершена!\n👤 Имя: {fio}\n👥 Группа: {text.upper()}", attachments=[kb.kb_student_menu()])

    # --- ПРЕПОДАВАТЕЛЬ ---
    elif state == "waiting_teacher_name":
        await TeacherDAO.add(max_id=user_id, full_name=text)
        del USER_STATES[user_id]
        await event.message.answer(f"✅ Вы зарегистрированы как преподаватель: {text}", attachments=[kb.kb_teacher_menu()])