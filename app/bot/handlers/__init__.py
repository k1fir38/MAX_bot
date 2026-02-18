from maxapi import Dispatcher, Bot, F
from maxapi.types import Command, MessageCreated, MessageCallback
from maxapi.enums.parse_mode import ParseMode

# Импортируем наши новые файлы
from . import common, auth, teacher, student, ai
from app.bot.logic import USER_STATES
from app.gigachat import ai_service
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
        
        # Общие / Смена аккаунта
        if payload == "menu:reset_account":
            await common.cmd_reset(event.message) # Передаем message из callback
        
        # AI-ассистент
        elif payload == "menu:chat":
            await ai.handle_ai_menu(event)

        elif payload.startswith("ai_role:"):
            await ai.handle_ai_role_selection(event, payload)

        # Авторизация
        elif payload.startswith("reg:"):
            await auth.handle_callback(event, payload, bot)
        
        # Учитель
        elif payload.startswith(("menu:create", "disc_", "menu:check")):
            await teacher.handle_callback(event, payload, bot)
            
        # Студент
        elif payload.startswith(("menu:get", "st_disc", "answer:", "menu:grades")):
            await student.handle_callback(event, payload, bot)


    # 3. МАРШРУТИЗАТОР ТЕКСТА
    @dp.message_created(F.message.body.text)
    async def router_text(event: MessageCreated):
        text = event.message.body.text
        if text.startswith('/'): return

        user_id = event.message.sender.user_id
        state = USER_STATES.get(user_id)

        # Если нет состояния -> Идем в AI чат
        if not state:
            await common.handle_ai_chat(event)
            return

        # Если состояние авторизации
        if state.startswith("waiting_student") or state == "waiting_teacher_name":
            await auth.handle_text(event, state)
        
        # Если состояние учителя
        elif state.startswith("waiting_task") or state == "waiting_discipline_name":
            await teacher.handle_text(event, state)