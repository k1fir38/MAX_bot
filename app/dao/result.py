
from sqlalchemy import select
from app.dao.base import BaseDAO
from app.models.user_result import UserResult
from app.models.assignment import Assignment # Чтобы достать название задания
from app.models.student import Student
from app.models.teacher import Teacher
from app.database import async_session_maker

class UserResultDAO(BaseDAO):
    model = UserResult

    @classmethod
    async def get_results_with_task_name(cls, max_id: int):
        async with async_session_maker() as session:
            # Выбираем результат и название задания
            query = (
                select(cls.model, Assignment.title)
                .join(Assignment, cls.model.assignment_id == Assignment.id)
                .where(cls.model.student_max_id == max_id)
            )
            result = await session.execute(query)
            # Возвращаем список строк (результат, заголовок_задания)
            return result.all()
        
    @classmethod
    async def get_results_for_teacher_by_max_id(cls, teacher_max_id: int):
        """Возвращает результаты только для заданий, созданных этим преподавателем."""
        async with async_session_maker() as session:
            # 1. Находим внутренний ID учителя по его Telegram ID (max_id)
            teacher_stmt = select(Teacher.id).where(Teacher.max_id == teacher_max_id)
            teacher_res = await session.execute(teacher_stmt)
            teacher_db_id = teacher_res.scalar_one_or_none()

            if not teacher_db_id:
                return []

            # 2. Соединяем результаты с заданиями и фильтруем по автору
            query = (
                select(cls.model, Assignment.title)
                .join(Assignment, cls.model.assignment_id == Assignment.id)
                .where(Assignment.author_max_id == teacher_max_id)
                .order_by(cls.model.submitted_at.desc())
            )
            result = await session.execute(query)
            return result.all()