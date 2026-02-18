
from sqlalchemy import select
from app.dao.base import BaseDAO
from app.models.user_result import UserResult
from app.models.assignment import Assignment # Чтобы достать название задания
from app.models.student import Student
from app.database import async_session_maker

class ResultDAO(BaseDAO):
    model = UserResult

    @classmethod
    async def get_results_with_task_name(cls, student_db_id: int):
        async with async_session_maker() as session:
            # Выбираем результат и название задания
            query = (
                select(cls.model, Assignment.title)
                .join(Assignment, cls.model.assignment_id == Assignment.id)
                .where(cls.model.student_id == student_db_id)
            )
            result = await session.execute(query)
            # Возвращаем список строк (результат, заголовок_задания)
            return result.all()
        
    @classmethod
    async def get_all_results_for_teacher(cls):
        async with async_session_maker() as session:
            # Джоиним результаты со студентами и заданиями
            query = (
                select(cls.model, Student, Assignment.title)
                .join(Student, cls.model.student_id == Student.id)
                .join(Assignment, cls.model.assignment_id == Assignment.id)
                .order_by(cls.model.submitted_at.desc()) # Последние сверху
            )
            result = await session.execute(query)
            return result.all()