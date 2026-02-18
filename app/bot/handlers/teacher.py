import json

from maxapi.types import MessageCallback, MessageCreated
from maxapi.enums.parse_mode import ParseMode

from app.bot import keyboards as kb
from app.bot.logic import USER_STATES, TEMP_DATA, get_user_role_and_data
from app.dao.discipline import DisciplineDAO
from app.dao.assignment import AssignmentDAO
from app.dao.result import ResultDAO

async def handle_callback(event: MessageCallback, payload: str, bot):
    user_id = event.callback.user.user_id
    chat_id = event.message.recipient.chat_id

    if payload == "menu:create_task":
        disciplines = await DisciplineDAO.find_all()
        await bot.send_message(chat_id=chat_id, text="Выберите дисциплину для задания:", attachments=[kb.kb_choose_discipline(disciplines)])

    elif payload == "disc_create_new":
        USER_STATES[user_id] = "waiting_discipline_name"
        await bot.send_message(chat_id=chat_id, text="Введите название новой дисциплины (например, Высшая математика):")

    elif payload.startswith("disc_select:"):
        disc_id = int(payload.split(":")[1])
        TEMP_DATA[user_id] = {"discipline_id": disc_id}
        USER_STATES[user_id] = "waiting_task_group"
        await bot.send_message(chat_id=chat_id, text="Для какой группы это задание? (например, ИКВТ-22):")

    elif payload == "menu:check":
        results = await ResultDAO.get_all_results_for_teacher()
        if not results:
            await bot.send_message(chat_id=chat_id, text="📈 Ведомость пока пуста.")
            return
        
        msg = "📊 **Общая ведомость результатов:**\n\n"
        for res, student, task_title in results:
            msg += (f"👤 {student.full_name} ({student.group_name})\n"
                    f"📝 {task_title}: `{res.grade}%`\n"
                    f"📅 {res.submitted_at.strftime('%d.%m %H:%M')}\n-------------------\n")
        await bot.send_message(chat_id=chat_id, text=msg, parse_mode=ParseMode.MARKDOWN)

async def handle_text(event: MessageCreated, state: str):
    user_id = event.message.sender.user_id
    text = event.message.body.text

    if state == "waiting_discipline_name":
        await DisciplineDAO.add(name=text)
        del USER_STATES[user_id]
        await event.message.answer(f"✅ Дисциплина '{text}' создана! Нажмите 'Создать задание' снова.")

    elif state == "waiting_task_group":
        TEMP_DATA[user_id]["target_group"] = text.upper()
        USER_STATES[user_id] = "waiting_task_title"
        await event.message.answer("Введите заголовок задания (например, Билет №1):")

    elif state == "waiting_task_title":
        TEMP_DATA[user_id]["title"] = text
        USER_STATES[user_id] = "waiting_task_questions"
        template = """[{"n": 1, "q": "Вопрос?", "options": ["Да", "Нет"], "answer": "Да"}]"""
        await event.message.answer(f"🧩 **Введите вопросы в формате JSON.**\nПример:\n`{template}`", parse_mode=ParseMode.MARKDOWN)

    elif state == "waiting_task_questions":
        try:
            questions_data = json.loads(text)
            if not isinstance(questions_data, list): raise ValueError("JSON должен быть списком [...]")
            # (Тут твоя проверка полей...)
        except Exception as e:
            await event.message.answer(f"❌ Ошибка JSON: {e}")
            return

        data = TEMP_DATA.get(user_id)
        role, teacher = await get_user_role_and_data(user_id)
        await AssignmentDAO.add(
            discipline_id=data["discipline_id"], author_id=teacher.id,
            title=data["title"], questions=text, target_group=data["target_group"]
        )
        del USER_STATES[user_id]
        del TEMP_DATA[user_id]
        await event.message.answer("🚀 Задание успешно создано!", attachments=[kb.kb_teacher_menu()])