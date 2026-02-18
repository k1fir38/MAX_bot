import asyncio
import json

from maxapi import F
from maxapi.types import MessageCreated, Command, MessageCallback
from maxapi.enums.parse_mode import ParseMode

from app.bot import keyboards as kb
from app.bot.logic import USER_STATES, TEMP_DATA, get_user_role_and_data
from app.dao.assignment import AssignmentDAO
from app.dao.discipline import DisciplineDAO
from app.dao.student import StudentDAO
from app.dao.teacher import TeacherDAO
from app.dao.result import ResultDAO
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
            
        # --- ЛОГИКА СМЕНЫ ПОЛЬЗОВАТЕЛЯ ---
        elif payload == "menu:reset_account":
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
        
        elif payload == "menu:create_task":
            # Получаем все дисциплины из базы
            disciplines = await DisciplineDAO.find_all()
            await bot.send_message(
                chat_id=chat_id, 
                text="Выберите дисциплину для задания:",
                attachments=[kb.kb_choose_discipline(disciplines)]
            )

        elif payload == "disc_create_new":
            USER_STATES[user_id] = "waiting_discipline_name"
            await bot.send_message(chat_id=chat_id, text="Введите название новой дисциплины (например, Высшая математика):")

        elif payload.startswith("disc_select:"):
            disc_id = int(payload.split(":")[1])
            TEMP_DATA[user_id] = {"discipline_id": disc_id}
            USER_STATES[user_id] = "waiting_task_group"
            await bot.send_message(chat_id=chat_id, text="Для какой группы это задание? (например, ИКВТ-22):")

        elif payload == "menu:get_task":
            # Показываем выбор предметов
            disciplines = await DisciplineDAO.find_all()
            
            if not disciplines:
                await bot.send_message(chat_id=chat_id, text="📚 Предметов пока не создано.")
                return

            await bot.send_message(
                chat_id=chat_id, 
                text="Выберите предмет, по которому хотите получить задание:",
                attachments=[kb.kb_student_choose_discipline(disciplines)]
            )

        elif payload.startswith("st_disc_select:"):
            disc_id = int(payload.split(":")[1])
            role, user = await get_user_role_and_data(user_id)
            
            # Ищем задание именно по этой дисциплине
            task = await AssignmentDAO.get_for_student(
                student_id=user.id, 
                group_name=user.group_name, 
                discipline_id=disc_id
            )
            
            if not task:
                await bot.send_message(chat_id=chat_id, text="✅ По этому предмету новых заданий для вас нет!")
                return

            # Дальше идет старая логика запуска теста (парснг JSON и т.д.)
            questions = json.loads(task.questions)
            TEMP_DATA[user_id] = {
                "task_id": task.id,
                "questions": questions,
                "current_idx": 0,
                "correct_count": 0
            }
            
            q = questions[0]
            await bot.send_message(
                chat_id=chat_id,
                text=f"📝 **{task.title}**\n\nВопрос 1: {q['q']}",
                attachments=[kb.kb_test_options(q['options'])],
                parse_mode=ParseMode.MARKDOWN
            )


        # --- ОБРАБОТКА ОТВЕТОВ НА ТЕСТ ---
        elif payload.startswith("answer:"):
            data = TEMP_DATA.get(user_id)
            if not data or "questions" not in data:
                return # Сессия теста не найдена

            user_answer = payload.replace("answer:", "")
            current_idx = data["current_idx"]
            questions = data["questions"]
            current_q = questions[current_idx]
            
            # Проверяем правильность
            if str(user_answer) == str(current_q["answer"]):
                data["correct_count"] += 1

            # Переходим к следующему вопросу
            data["current_idx"] += 1
            
            if data["current_idx"] < len(questions):
                # Показываем следующий вопрос
                next_idx = data["current_idx"]
                next_q = questions[next_idx]
                await bot.send_message(
                    chat_id=chat_id,
                    text=f"Вопрос {next_idx + 1}: {next_q['q']}",
                    attachments=[kb.kb_test_options(next_q['options'])]
                )
            else:
                # ФИНИШ ТЕСТА
                score = data["correct_count"]
                total = len(questions)

                if total > 0:
                    percentage = round((score / total) * 100) 
                else:
                    percentage = 0


                role, user = await get_user_role_and_data(user_id)
                
                # Сохраняем результат в БД
                await ResultDAO.add(
                    student_id=user.id,
                    assignment_id=data["task_id"],
                    grade=percentage,
                    feedback=f"Решено верно: {score} из {total}"
                )
                
                await bot.send_message(
                    chat_id=chat_id,
                    text=f"🏁 **Тест завершен!**\n\nВаш результат: `{percentage}%` \n({score} из {total} правильных ответов).",
                    attachments=[kb.kb_student_menu()],
                    parse_mode=ParseMode.MARKDOWN
                )
                # Очищаем временные данные
                del TEMP_DATA[user_id]
        
        # --- ЛОГИКА ПРОСМОТРА ОЦЕНОК ---
        elif payload == "menu:grades":
            role, user = await get_user_role_and_data(user_id)
            
            # 1. Получаем список результатов из БД
            results = await ResultDAO.get_results_with_task_name(user.id)
            
            if not results:
                await bot.send_message(
                    chat_id=chat_id, 
                    text="📭 Вы еще не сдали ни одного задания."
                )
                return

            # 2. Формируем красивый текст
            msg_text = "📊 **Ваши результаты:**\n\n"
            
            for res, task_title in results:
                # res — это объект UserResult, task_title — строка с названием
                msg_text += (
                    f"📌 **{task_title}**\n"
                    f"└ Оценка: `{res.grade}%`\n"
                    f"└ Комментарий: _{res.feedback}_\n"
                    f"--- \n"
                )

            # 3. Отправляем студенту
            await bot.send_message(
                chat_id=chat_id, 
                text=msg_text,
                parse_mode=ParseMode.MARKDOWN
            )
        
        elif payload == "menu:check":
            results = await ResultDAO.get_all_results_for_teacher()
            
            if not results:
                await bot.send_message(chat_id=chat_id, text="📈 Ведомость пока пуста.")
                return

            msg = "📊 **Общая ведомость результатов:**\n\n"
            for res, student, task_title in results:
                msg += (
                    f"👤 {student.full_name} ({student.group_name})\n"
                    f"📝 {task_title}: `{res.grade}%`\n"
                    f"📅 {res.submitted_at.strftime('%d.%m %H:%M')}\n"
                    f"-------------------\n"
                )
            
            await bot.send_message(chat_id=chat_id, text=msg, parse_mode=ParseMode.MARKDOWN)
    
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
            await event.message.answer("Отлично! Теперь введите номер вашей группы (например, ИКВТ-22):")
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
        
        # 1. Создание дисциплины
        elif state == "waiting_discipline_name":
            await DisciplineDAO.add(name=user_text)
            del USER_STATES[user_id]
            await event.message.answer(f"✅ Дисциплина '{user_text}' создана! Нажмите 'Создать задание' снова.")
            return

        # 2. Ввод группы для задания
        elif state == "waiting_task_group":
            TEMP_DATA[user_id]["target_group"] = user_text.upper()
            USER_STATES[user_id] = "waiting_task_title"
            await event.message.answer("Введите заголовок задания (например, Билет №1 или Контрольная):")
            return

        # 3. Ввод заголовка
        elif state == "waiting_task_title":
            TEMP_DATA[user_id]["title"] = user_text
            USER_STATES[user_id] = "waiting_task_questions"
            template = """[
                {
                    "n": 1,
                    "q": "Что такое Python?",
                    "options": ["Язык программирования", "Змея", "Тип данных"],
                    "answer": "Язык программирования"
                },
                {
                    "n": 2,
                    "q": "2 + 2 = ?",
                    "options": ["3", "4", "5"],
                    "answer": "4"
                }
            ]"""

            await event.message.answer(
                "🧩 **Введите вопросы в формате JSON.**\n\n"
                "Соблюдайте структуру: номер (`n`), вопрос (`q`), варианты (`options`) и правильный ответ (`answer`).\n\n"
                "**Пример (можно скопировать и изменить):**",
                parse_mode=ParseMode.MARKDOWN
                )

            # Отправляем шаблон отдельным сообщением в виде кода, чтобы его было удобно копировать одним нажатием
            await event.message.answer(f"`{template}`", parse_mode=ParseMode.MARKDOWN)

            await event.message.answer("⚠️ *Важно: используйте двойные кавычки и квадратные скобки.*")
            return

        # 4. Финальный шаг: ввод вопросов и сохранение
        elif state == "waiting_task_questions":
            import json
            try:
                # 1. Проверка синтаксиса JSON
                questions_data = json.loads(user_text)
                
                # 2. Проверка, что это список (массив)
                if not isinstance(questions_data, list):
                    raise ValueError("JSON должен начинаться с `[` и заканчиваться `]` (быть списком).")

                # 3. Проверка каждого вопроса на наличие обязательных полей
                for idx, item in enumerate(questions_data):
                    required_keys = ["n", "q", "options", "answer"]
                    for key in required_keys:
                        if key not in item:
                            raise ValueError(f"В вопросе №{idx+1} отсутствует поле '{key}'")
                    
                    if not isinstance(item["options"], list):
                        raise ValueError(f"В вопросе №{idx+1} поле 'options' должно быть списком.")

            except (json.JSONDecodeError, ValueError) as e:
                # Если любая проверка не прошла — выводим конкретную причину и ВЫХОДИМ
                await event.message.answer(f"❌ Ошибка в формате: {str(e)}\n\nПопробуйте исправить и прислать еще раз.")
                return # <--- Это не дает боту сохранить плохой JSON

            # --- ЕСЛИ МЫ ДОШЛИ СЮДА, ЗНАЧИТ JSON ИДЕАЛЕН ---
            data = TEMP_DATA.get(user_id)
            role, teacher_user = await get_user_role_and_data(user_id)
            
            await AssignmentDAO.add(
                discipline_id=data["discipline_id"],
                author_id=teacher_user.id,
                title=data["title"],
                questions=user_text,
                target_group=data["target_group"]
            )
            
            del USER_STATES[user_id]
            del TEMP_DATA[user_id]
            
            await event.message.answer("🚀 Задание успешно создано!", attachments=[kb.kb_teacher_menu()])
            return

        # --- СЦЕНАРИЙ: ОБЫЧНЫЙ ДИАЛОГ С AI ---
        # Если состояний нет, отправляем запрос в GigaChat
        if state is None:
            await event.message.answer("⏳ Думаю...")
            
            response_text = await asyncio.to_thread(
                ai_service.generate_response, 
                user_id, 
                user_text
            )
            
            # Удаляем сообщение "Думаю..." (если API позволяет) или просто шлем ответ
            await event.message.answer(text=response_text, parse_mode=ParseMode.MARKDOWN)