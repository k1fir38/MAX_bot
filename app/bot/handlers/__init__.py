from maxapi import Dispatcher, Bot, F
from maxapi.types import Command, MessageCreated, MessageCallback
from maxapi.enums.parse_mode import ParseMode

# Импортируем наши новые файлы
from . import common, auth, teacher, student, ai
from app.bot.logic import USER_STATES
from app.services.gigachat import ai_service
from app.bot import keyboards as kb

def register_handlers(dp: Dispatcher, bot: Bot):
    
    # 1. КОМАНДЫ
    dp.message_created(Command('start'))(common.cmd_start)
    dp.message_created(Command('reset'))(common.cmd_reset)

    # 2. МАРШРУТИЗАТОР КНОПОК (CALLBACK)
    @dp.message_callback()
    async def router_callback(event: MessageCallback):
        payload = event.callback.payload
        user_id = event.callback.user.user_id
        
        # --- ЛОГИКА СБРОСА ---
        if payload == "menu:reset_account":
            # Просто спрашиваем подтверждение
            await common.cmd_reset(event.message, user_id)

        elif payload == "reset:confirm":
            # Пользователь подтвердил — удаляем
            await common.execute_reset(user_id, event.message)
            # Удаляем сообщение с кнопками подтверждения, чтобы нельзя было нажать дважды
            await event.message.delete() 

        elif payload == "reset:cancel":
            # Пользователь передумал
            await event.message.delete() # Удаляем вопрос
            await event.message.answer("Действие отменено. Вы остались в своей роли.")
        
        # AI-ассистент
        elif payload == "menu:chat":
            await ai.handle_ai_menu(event)

        elif payload.startswith("ai_role:"):
            await ai.handle_ai_role_selection(event, payload)

        # Авторизация
        elif payload.startswith("reg:"):
            await auth.handle_callback(event, payload, bot)
        
        # Преподаватель
        elif payload.startswith((
            "menu:create", 
            "disc_", 
            "menu:check", 
            "menu:manage_assignments", 
            "task_manage:",            
            "task_del:",       
            "task_del_yes:", 
            "task_view",   
            "menu:teacher_main",     
        )):
            await teacher.handle_callback(event, payload, bot)
            
        # Студент
        elif payload.startswith((
            "menu:get",
            "st_disc", 
            "st_task_select",
            "answer:", 
            "menu:grades")):
            await student.handle_callback(event, payload, bot)


    # 3. МАРШРУТИЗАТОР ТЕКСТА
    @dp.message_created(F.message.body.text)
    async def router_text(event: MessageCreated):
        text = event.message.body.text
        if text.startswith('/'): return

        user_id = event.message.sender.user_id
        state = USER_STATES.get(user_id)

        # Если пользователь РЕШАЕТ ТЕСТ - блокируем любой текст
        if state == "solving_test":
            await event.message.answer("⚠️ **Идет тест!**\nПожалуйста, используй кнопки для выбора ответа. Текстовый ввод отключен.")
            return

        # Если включен режим АИ - отправляем в GigaChat
        if state == "ai_chat_active":
            await ai.process_ai_chat(event, bot)
            return

        # Обработка регистрации и создания заданий
        if state:
            if state.startswith("waiting_student") or state == "waiting_teacher_name":
                await auth.handle_text(event, state)
                return
            elif state.startswith("waiting_task") or state == "waiting_discipline_name":
                await teacher.handle_text(event, state)
                return

        # Если вообще нет состояния просим выбрать действие
        if not state:
            await event.message.answer(
                "🤖 Я не знаю, что делать с этим текстом.\n\n"
                "• Если хочешь пообщаться с нейросетью — нажми кнопку **'Чат с AI'**.\n"
                "• Если хочешь учиться — нажми **'Получить задание'**."
            )