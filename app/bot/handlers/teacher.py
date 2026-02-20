import json

from maxapi.types import MessageCallback, MessageCreated
from maxapi.enums.parse_mode import ParseMode

from app.bot import keyboards as kb
from app.bot.logic import USER_STATES, TEMP_DATA, get_user_role_and_data
from app.dao.discipline import DisciplineDAO
from app.dao.assignment import AssignmentDAO
from app.dao.result import UserResultDAO

async def handle_callback(event: MessageCallback, payload: str, bot):
    user_id = event.callback.user.user_id
    chat_id = event.message.recipient.chat_id
    role, user = await get_user_role_and_data(user_id)

    if user is None:
        await event.message.answer(
            "⚠️ **Профиль не найден!**\nВаш аккаунт был удален или не зарегистрирован. Введите /start",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    elif payload == "menu:manage_assignments":
        tasks = await AssignmentDAO.find_all(author_id=user.id)
        if not tasks:
            await handle_manage_assignments(event.message, user_id)
            return
        
        await handle_manage_assignments(event.message, user_id)
        return

    # 1. Нажали на задание из списка
    elif payload.startswith("task_manage:"):
        task_id = int(payload.split(":")[1])
        task = await AssignmentDAO.find_one_or_none(id=task_id, author_id=user.id) # Проверяем, что это его задание
        
        if task:
            await event.message.answer(
                f"⚙️ Управление заданием: **{task.title}**\nГруппа: `{task.target_group}`\n\n"
                "Что вы хотите сделать?",
                attachments=[kb.kb_manage_single_assignment(task.id, task.title, task.target_group)],
                parse_mode=ParseMode.MARKDOWN
            )
        else:
             await event.message.answer("Задание не найдено или не принадлежит вам.")

    # 2. Запрос на удаление (Ведет к окну подтверждения)
    elif payload.startswith("task_del:"):
        task_id = int(payload.split(":")[1])
        # Временно сохраняем ID для подтверждения
        TEMP_DATA[user_id] = {"task_to_delete": task_id} 
        task = await AssignmentDAO.find_one_or_none(id=task_id, author_id=user.id)
        
        if task:
            await event.message.answer(
                f"🔥 **Внимание!** Вы собираетесь удалить задание '{task.title}' (для группы:{task.target_group}). Это действие необратимо!",
                attachments=[kb.kb_confirm_delete_task(task_id)]
            )
        else:
            await event.message.answer("Задание не найдено.")
        
    # 3. Исполнение удаления (Теперь нужно использовать логику из execute_reset)
    elif payload.startswith("task_del_yes:"):
        task_id = int(payload.split(":")[1])
        task = await AssignmentDAO.find_one_or_none(id=task_id)
        
        # Получаем ID учителя (пользователя) из TEMP_DATA или текущего event, если нужно
        # Для простоты используем user.id, который мы должны получить в начале callback_handler
        
        try:
            await UserResultDAO.delete(assignment_id=task_id)
            await AssignmentDAO.delete(id=task_id)
            
            await event.message.answer(f"✅ Задание: '{task.title}' для группы: '{task.target_group}' успешно удалено.")
            await handle_manage_assignments(event.message, user_id) 
        except Exception as e:
            await event.message.answer(f"❌ Ошибка при удалении: {e}")


    elif payload.startswith("task_view:"):
        task_id = int(payload.split(":")[1])
        task = await AssignmentDAO.find_one_or_none(id=task_id, author_id=user.id)
        
        if task and task.questions:
            # Отправляем JSON как отформатированный код (Markdown)
            await event.message.answer(
                f"**JSON для задания '{task.title}':**\n"
                f"```json\n{task.questions}\n```",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await event.message.answer("Не удалось найти JSON для этого задания.")
    

    # 4. Возврат в главное меню
    elif payload == "menu:teacher_main":
        await event.message.answer("Главное меню преподавателя:", attachments=[kb.kb_teacher_menu()])

    elif payload == "menu:create_task":
        disciplines = await DisciplineDAO.find_all()
        await bot.send_message(chat_id=chat_id, text="Выберите дисциплину для задания:", 
                               attachments=[kb.kb_choose_discipline(disciplines)])

    elif payload == "disc_create_new":
        USER_STATES[user_id] = "waiting_discipline_name"
        await bot.send_message(chat_id=chat_id, text="Введите название новой дисциплины (например, Высшая математика):")

    elif payload.startswith("disc_select:"):
        disc_id = int(payload.split(":")[1])
        TEMP_DATA[user_id] = {"discipline_id": disc_id}
        USER_STATES[user_id] = "waiting_task_group"
        await bot.send_message(chat_id=chat_id, text="Для какой группы это задание? (например, ИКВТ-22):")

    elif payload == "menu:check":
        results = await UserResultDAO.get_results_for_teacher_by_max_id(user_id)
        if not results:
            await bot.send_message(chat_id=chat_id, text="📈 Ведомость пока пуста.")
            return
        
        msg = "📊 **Общая ведомость результатов:**\n\n"
        for res, task_title in results:
            msg += (f"👤 {res.student_name} ({res.student_group})\n"
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
        await event.message.answer(f"🧩 **Введите вопросы в формате JSON.**\nПример:\n`{template}`", 
                                   parse_mode=ParseMode.MARKDOWN)

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
            discipline_id=data["discipline_id"],
            author_id=teacher.id,
            author_max_id=user_id,
            title=data["title"],
            questions=text,
            target_group=data["target_group"]
        )
        del USER_STATES[user_id]
        del TEMP_DATA[user_id]
        await event.message.answer("🚀 Задание успешно создано!",
                                   attachments=[kb.kb_teacher_menu()])

    elif state == "waiting_task_group":
        TEMP_DATA[user_id]["target_group"] = text.upper()
        USER_STATES[user_id] = "waiting_task_title"
        await event.message.answer("🏷 Введите заголовок задания (например, Билет №1):")
        return

    elif state == "waiting_task_title":
        TEMP_DATA[user_id]["title"] = text
        USER_STATES[user_id] = "waiting_task_questions"
        await event.message.answer("🧩 Теперь введите вопросы в формате JSON:")
        return

    
async def handle_manage_assignments(message, user_id):
    """Показывает обновленный список заданий, созданных этим учителем."""
    
    # Получаем данные пользователя, чтобы найти его ID в БД и ФИО
    role, user = await get_user_role_and_data(user_id) 
    
    if user is None:
        await message.answer("⚠️ Профиль не найден. Введите /start для регистрации.")
        return

    # Ищем все задания, где author_id соответствует ID пользователя в БД
    tasks = await AssignmentDAO.find_all(author_id=user.id)
    
    if not tasks:
        await message.answer("🛢 У вас пока нет созданных заданий.")
        return
    
    # Формируем текст для вывода
    task_list_text = "📋 **Ваши задания:**\nНажмите на задание для управления:\n\n"
    
    # Отправляем сообщение с клавиатурой списка
    await message.answer(
        task_list_text,
        attachments=[kb.kb_teacher_assignments(tasks)],
        parse_mode=ParseMode.MARKDOWN
    )