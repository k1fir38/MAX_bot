import asyncio
from maxapi import F
from maxapi.types import MessageCreated, Command, MessageCallback
from maxapi.enums.parse_mode import ParseMode

from app.bot import keyboards as kb
from app.bot.logic import USER_STATES, TEMP_DATA, get_user_role_and_data
from app.dao.student import StudentDAO
from app.dao.teacher import TeacherDAO
from app.gigachat import ai_service


def register_handlers(dp, bot):

    @dp.message_created(Command('start'))
    async def start_handler(event: MessageCreated):
        user_id = event.message.sender.user_id
        
        # Очищаем состояние, если оно было
        if user_id in USER_STATES:
            del USER_STATES[user_id]
            
        # Проверяем БД
        role, user = await get_user_role_and_data(user_id)
        
        if role == "student":
            await event.message.answer(
                f"С возвращением, студент {user.full_name} ({user.group_name})! 👋",
                attachments=[kb.kb_student_menu()]
            )
        elif role == "teacher":
            await event.message.answer(
                f"Здравствуйте, {user.full_name}! 👋 Вы в панели преподавателя.",
                attachments=[kb.kb_teacher_menu()]
            )
        else:
            # Пользователя нет в базе
            await event.message.answer(
                "Добро пожаловать в GigaBot! 🤖\nДля начала выберите, кто вы:",
                attachments=[kb.kb_auth_role()]
            )
        
    @dp.message_created(Command('reset'))
    async def reset_command_handler(event: MessageCreated):
        user_id = event.message.sender.user_id
        role, user = await get_user_role_and_data(user_id)
        
        if role == "student":
            await StudentDAO.delete(max_id=user_id)
        elif role == "teacher":
            await TeacherDAO.delete(max_id=user_id)
            
        await event.message.answer(
            text="♻️ Аккаунт сброшен. Используйте /start для новой регистрации."
        )

    @dp.message_callback()
    async def callback_handler(event: MessageCallback):
        user_id = event.callback.user.user_id
        payload = event.callback.payload
        chat_id = event.message.recipient.chat_id
        
        # --- ЛОГИКА РЕГИСТРАЦИИ ---
        if payload == "reg:student":
            USER_STATES[user_id] = "waiting_student_fio" 
            await bot.send_message(chat_id, text="Введите ваше ФИО (например, Иванов Иван Иванович):")
        
        elif payload == "reg:teacher":
            USER_STATES[user_id] = "waiting_teacher_name"
            await bot.send_message(chat_id=chat_id, text="Введите ваше ФИО (например, Иванов И.И.):")

        # --- ЛОГИКА МЕНЮ ---
        elif payload == "menu:chat":
            await bot.send_message(chat_id=chat_id, text="Режим общения с AI активирован. Просто пишите текст.")
            
        elif payload == "menu:get_task":
            # Здесь будет логика выдачи задания
            await bot.send_message(chat_id=chat_id, text="🔍 Ищу доступные задания для вашей группы...")
            
        elif payload == "menu:create_task":
            await bot.send_message(chat_id=chat_id, text="🔧 Функционал создания заданий в разработке.")

        # --- ЛОГИКА СМЕНЫ ПОЛЬЗОВАТЕЛЯ ---
        if payload == "menu:reset_account":
            # 1. Определяем, кто это (студент или учитель)
            role, user = await get_user_role_and_data(user_id)
            
            # 2. Удаляем из соответствующей таблицы
            if role == "student":
                await StudentDAO.delete(max_id=user_id)
            elif role == "teacher":
                await TeacherDAO.delete(max_id=user_id)
                
            # 3. Отправляем сообщение и возвращаем к выбору роли
            await bot.send_message(
                chat_id=chat_id, 
                text="♻️ Ваши данные удалены. Выберите новую роль:"
            )
            await bot.send_message(
                chat_id=chat_id, 
                text="Кто вы?", 
                attachments=[kb.kb_auth_role()]
        )

    
    @dp.message_created(F.message.body.text)
    async def text_handler(event: MessageCreated):
        user_text = event.message.body.text
        user_id = event.message.sender.user_id
        
        # Игнорируем команды
        if user_text.startswith('/'):
            return

        # Проверяем состояние (если пользователь сейчас регистрируется)
        state = USER_STATES.get(user_id)

        # --- РЕГИСТРАЦИЯ СТУДЕНТА: ШАГ 1 (ФИО) ---
        if state == "waiting_student_fio":
            # Сохраняем ФИО во временное хранилище
            TEMP_DATA[user_id] = {"full_name": user_text}
            
            # Переходим к следующему шагу
            USER_STATES[user_id] = "waiting_student_group"
            await event.message.answer("Отлично! Теперь введите номер вашей группы:")
            return
        
        # --- РЕГИСТРАЦИЯ СТУДЕНТА: ШАГ 2 (ГРУППА) ---
        elif state == "waiting_student_group":
            # Достаем ФИО, которое сохранили на прошлом шаге
            user_data = TEMP_DATA.get(user_id)
            if user_data:
                fio = user_data.get("full_name")
            else:
                fio = "Неизвестный"

            # Сохраняем всё в базу данных
            await StudentDAO.add(
                max_id=user_id, 
                full_name=fio, 
                group_name=user_text.upper()
            )
            
            # Очищаем временные данные
            del USER_STATES[user_id]
            if user_id in TEMP_DATA:
                del TEMP_DATA[user_id]
                
            await event.message.answer(
                f"✅ Регистрация завершена!\n👤 Имя: {fio}\n👥 Группа: {user_text.upper()}",
                attachments=[kb.kb_student_menu()]
            )
            return
        
        # --- РЕГИСТРАЦИЯ ПРЕПОДАВАТЕЛЯ  ---
        elif state == "waiting_teacher_name":
            await TeacherDAO.add(
                max_id=user_id,
                full_name=user_text
            )
            
            # Обязательно удаляем состояние
            del USER_STATES[user_id]
            
            await event.message.answer(
                f"✅ Вы зарегистрированы как преподаватель: {user_text}",
                attachments=[kb.kb_teacher_menu()]
            )
            return

        # --- СЦЕНАРИЙ: ОБЫЧНЫЙ ДИАЛОГ С AI ---
        # Если состояний нет, отправляем запрос в GigaChat
        await event.message.answer("⏳ Думаю...")
        
        response_text = await asyncio.to_thread(
            ai_service.generate_response, 
            user_id, 
            user_text
        )
        
        # Удаляем сообщение "Думаю..." (если API позволяет) или просто шлем ответ
        await event.message.answer(text=response_text, parse_mode=ParseMode.MARKDOWN)