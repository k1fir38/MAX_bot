from sqlalchemy import delete, insert, select

from app.database import async_session_maker

class BaseDAO:

    model = None

    @classmethod
    async def add(cls, **data):
        async with async_session_maker() as session:
            # Запрос на добавление записи в таблицу
            query = insert(cls.model).values(**data)
            await session.execute(query)
            # Нужно обязательно коммитить изменения в бд
            await session.commit()

    @classmethod
    async def find_one_or_none(cls, **filter_by):
        """
        Находит одну запись, соответствующую произвольным фильтрам.
        """
        async with async_session_maker() as session:
            query = select(cls.model).filter_by(**filter_by)
            result = await session.execute(query)
            return result.scalar_one_or_none()
        
    @classmethod
    async def find_all(cls, **filter_by):
        """
        Находит все записи, соответствующие фильтрам. 
        Если фильтры не переданы — возвращает все записи из таблицы.
        """
        async with async_session_maker() as session:
            query = select(cls.model).filter_by(**filter_by)
            result = await session.execute(query)
            return result.scalars().all()
        
    @classmethod
    async def delete(cls, **filter_by):
        """Удаляет записи по фильтру."""
        async with async_session_maker() as session:
            query = delete(cls.model).filter_by(**filter_by)
            await session.execute(query)
            await session.commit()
