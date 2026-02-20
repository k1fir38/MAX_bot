import asyncio
import json

from maxapi.types import MessageCallback
from maxapi.enums.parse_mode import ParseMode

from app.bot import keyboards as kb
from app.bot.logic import TEMP_DATA, get_user_role_and_data
from app.dao.discipline import DisciplineDAO
from app.dao.assignment import AssignmentDAO
from app.dao.result import UserResultDAO
from app.services.gigachat import ai_service

async def handle_callback(event: MessageCallback, payload: str, bot):
    user_id = event.callback.user.user_id
    chat_id = event.message.recipient.chat_id
    role, user = await get_user_role_and_data(user_id)
    if user is None:
        await event.message.answer(
            "⚠️ **Ошибка:** Ваш профиль не найден в базе данных.\n"
            "Возможно, вы сбросили аккаунт. Пожалуйста, введите /start для регистрации.",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    if payload == "menu:get_task":
        disciplines = await DisciplineDAO.find_all()
        if not disciplines:
            await bot.send_message(chat_id=chat_id, text="📚 Предметов пока не создано.")
            return
        await bot.send_message(chat_id=chat_id, 
                               text="Выберите предмет:", 
                               attachments=[kb.kb_student_choose_discipline(disciplines)])

    elif payload.startswith("st_disc_select:"):
        disc_id = int(payload.split(":")[1])
        role, user = await get_user_role_and_data(user_id)

        tasks = await AssignmentDAO.get_all_available_for_student(
            max_id=user_id, 
            group_name=user.group_name, 
            discipline_id=disc_id
        )

        if not tasks:
            await event.message.answer("✅ По этому предмету заданий пока нет (или вы всё решили).")
            return

        await event.message.answer(
            "📋 **Выберите задание:**",
            attachments=[kb.kb_student_assignments_list(tasks)],
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    elif payload.startswith("st_task_select:"):
        task_id = int(payload.split(":")[1])
        
        # Загружаем конкретное задание из базы
        task = await AssignmentDAO.find_one_or_none(id=task_id)
        
        if not task:
            await event.message.answer("❌ Ошибка: Задание не найдено.")
            return

        # --- ЗАПУСК ТЕСТА (Твой старый код инициализации) ---
        questions = json.loads(task.questions)
        TEMP_DATA[user_id] = {
            "task_id": task.id, 
            "questions": questions, 
            "current_idx": 0, 
            "correct_count": 0,
            "history": [] 
        }
        
        q = questions[0]
        await event.message.answer(
            f"🚀 **Начинаем: {task.title}**\n\nВопрос 1: {q['q']}", 
            attachments=[kb.kb_test_options(q['options'])], 
            parse_mode=ParseMode.MARKDOWN
        )
        return

    elif payload.startswith("answer:"):
        data = TEMP_DATA.get(user_id)
        if not data: return
        user_answer = payload.replace("answer:", "")
        q = data["questions"][data["current_idx"]]
        
        is_correct = str(user_answer) == str(q["answer"])
        
        if is_correct: 
            data["correct_count"] += 1
            
        # ИЗМЕНЕНИЕ 2: Сохраняем ход решения
        data["history"].append({
            "question": q["q"],
            "student_answer": user_answer,
            "correct_answer": q["answer"],
            "is_correct": is_correct
        })

        data["current_idx"] += 1
        
        if data["current_idx"] < len(data["questions"]):
            nxt = data["questions"][data["current_idx"]]
            await bot.send_message(chat_id=chat_id, 
                                   text=f"Вопрос {data['current_idx']+1}: {nxt['q']}", 
                                   attachments=[kb.kb_test_options(nxt['options'])])
        else:
            # --- ФИНАЛ ТЕСТА С AI ---
            total = len(data["questions"])
            score = data["correct_count"]
            percent = round((score/total)*100) if total > 0 else 0
            
            # Сообщаем, что идет проверка
            wait_msg = await event.message.answer("🏁 Тест завершен! Нейросеть проверяет ваши ответы и пишет рецензию... ⏳")
            
            # Вызываем GigaChat (в отдельном потоке, чтобы не тормозить)
            ai_feedback = await asyncio.to_thread(
                ai_service.analyze_test_results, 
                data["history"]
            )
            
            # Удаляем сообщение "проверяет..."
            try: await bot.delete_message(chat_id=chat_id, message_id=wait_msg.message.id)
            except: pass

            role, user = await get_user_role_and_data(user_id)
            if user:
                await UserResultDAO.add(
                    student_id=user.id, 
                    student_max_id=user_id,
                    student_name=user.full_name, 
                    student_group=user.group_name,
                    assignment_id=data["task_id"], 
                    grade=percent, 
                    # Сохраняем рецензию от ИИ в базу!
                    feedback=ai_feedback 
                )
            
            # Выводим результат и рецензию
            await event.message.answer(
                f"📊 **Результат:** `{percent}%` ({score}/{total})\n\n"
                f"🧑‍🏫 **Рецензия преподавателя (AI):**\n{ai_feedback}", 
                attachments=[kb.kb_student_menu()],
                parse_mode=ParseMode.MARKDOWN
            )
            del TEMP_DATA[user_id]

    elif payload == "menu:grades":
        role, user = await get_user_role_and_data(user_id)
        results = await UserResultDAO.get_results_with_task_name(user_id)
        if not results:
            await bot.send_message(chat_id=chat_id, text="📭 Оценок нет.")
            return
        msg_text = "📊 **Ваши результаты:**\n\n"
            
        for res, task_title in results:
            # res — это объект UserResult, task_title — строка с названием
            msg_text += (
                f"📌 **{task_title}**\n"
                f"└ Оценка: `{res.grade}%`\n"
                f"└ Комментарий: _{res.feedback}_\n"
                f"--- \n"
            )
        await bot.send_message(
                chat_id=chat_id, 
                text=msg_text,
                parse_mode=ParseMode.MARKDOWN
            )