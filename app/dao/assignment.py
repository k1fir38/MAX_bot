from sqlalchemy import and_, not_, select


from app.dao.base import BaseDAO
from app.models.assignment import Assignment
from app.database import async_session_maker
from app.models.user_result import UserResult


class AssignmentDAO(BaseDAO):
    model = Assignment

    @classmethod
    async def get_for_student(cls, student_id: int, group_name: str, discipline_id: int):
        async with async_session_maker() as session:
            subquery = select(UserResult.assignment_id).where(UserResult.student_id == student_id)
            
            query = select(cls.model).where(
                and_(
                    cls.model.target_group == group_name,
                    cls.model.discipline_id == discipline_id, # ФИЛЬТР ПО ПРЕДМЕТУ
                    not_(cls.model.id.in_(subquery))
                )
            ).limit(1)
            
            result = await session.execute(query)
            return result.scalar_one_or_none()

    @classmethod
    async def get_all_available_for_student(cls, max_id: int, group_name: str, discipline_id: int):
        async with async_session_maker() as session:
            # Подзапрос: ID заданий, которые студент уже сдавал
            subquery = select(UserResult.assignment_id).where(UserResult.student_max_id == max_id)
            
            # Ищем ВСЕ задания для группы и предмета, которых нет в подзапросе
            query = select(cls.model).where(
                and_(
                    cls.model.target_group == group_name,
                    cls.model.discipline_id == discipline_id,
                    not_(cls.model.id.in_(subquery))
                )
            )
            
            result = await session.execute(query)
            return result.scalars().all()