import json

from maxapi.types import MessageCallback
from maxapi.enums.parse_mode import ParseMode

from app.bot import keyboards as kb
from app.bot.logic import TEMP_DATA, get_user_role_and_data
from app.dao.discipline import DisciplineDAO
from app.dao.assignment import AssignmentDAO
from app.dao.result import ResultDAO

async def handle_callback(event: MessageCallback, payload: str, bot):
    user_id = event.callback.user.user_id
    chat_id = event.message.recipient.chat_id

    if payload == "menu:get_task":
        disciplines = await DisciplineDAO.find_all()
        if not disciplines:
            await bot.send_message(chat_id=chat_id, text="📚 Предметов пока не создано.")
            return
        await bot.send_message(chat_id=chat_id, text="Выберите предмет:", attachments=[kb.kb_student_choose_discipline(disciplines)])

    elif payload.startswith("st_disc_select:"):
        disc_id = int(payload.split(":")[1])
        role, user = await get_user_role_and_data(user_id)
        task = await AssignmentDAO.get_for_student(student_id=user.id, group_name=user.group_name, discipline_id=disc_id)
        
        if not task:
            await bot.send_message(chat_id=chat_id, text="✅ Заданий нет!")
            return

        questions = json.loads(task.questions)
        TEMP_DATA[user_id] = {"task_id": task.id, "questions": questions, "current_idx": 0, "correct_count": 0}
        q = questions[0]
        await bot.send_message(chat_id=chat_id, text=f"📝 **{task.title}**\n\nВопрос 1: {q['q']}", attachments=[kb.kb_test_options(q['options'])], parse_mode=ParseMode.MARKDOWN)

    elif payload.startswith("answer:"):
        data = TEMP_DATA.get(user_id)
        if not data: return
        user_answer = payload.replace("answer:", "")
        q = data["questions"][data["current_idx"]]
        
        if str(user_answer) == str(q["answer"]): data["correct_count"] += 1
        data["current_idx"] += 1
        
        if data["current_idx"] < len(data["questions"]):
            nxt = data["questions"][data["current_idx"]]
            await bot.send_message(chat_id=chat_id, text=f"Вопрос {data['current_idx']+1}: {nxt['q']}", attachments=[kb.kb_test_options(nxt['options'])])
        else:
            total = len(data["questions"])
            score = data["correct_count"]
            percent = round((score/total)*100) if total > 0 else 0
            role, user = await get_user_role_and_data(user_id)
            await ResultDAO.add(student_id=user.id, assignment_id=data["task_id"], grade=percent, feedback=f"Верно {score}/{total}")
            await bot.send_message(chat_id=chat_id, text=f"🏁 Результат: {percent}%", attachments=[kb.kb_student_menu()])
            del TEMP_DATA[user_id]

    elif payload == "menu:grades":
        role, user = await get_user_role_and_data(user_id)
        results = await ResultDAO.get_results_with_task_name(user.id)
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