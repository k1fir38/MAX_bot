
from sqlalchemy import delete, insert, select
from sqlalchemy.exc import SQLAlchemyError

from app.database import async_session_maker

class BaseDAO:

    model = None

    @classmethod
    async def find_by_id(cls, model_id: int):
        """Находит одну запись в базе данных по её первичному ключу (ID)."""
        # Создаем экземпляр сессии через фабрику сессий
        async with async_session_maker() as session:
            # Формируем запрос: SELECT * FROM model WHERE id = model_id
            query = select(cls.model).filter_by(id=model_id)
            # Отправляем запрос в БД асинхронно
            result = await session.execute(query)
            # scalar_one_or_none вернет один объект модели или None, если запись не найдена.
            # Если найдется больше одной записи (что для ID невозможно), бросит ошибку.
            return result.scalar_one_or_none()


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
        Пример использования: find_one_or_none(email="test@test.com")
        """
        async with async_session_maker() as session:
            # Распаковываем фильтры (**filter_by) прямо в метод SQLAlchemy
            query = select(cls.model).filter_by(**filter_by)
            result = await session.execute(query)
            # Возвращаем найденный объект или None
            return result.scalar_one_or_none()
        
    @classmethod
    async def find_all(cls, **filter_by):
        """
        Находит все записи, соответствующие фильтрам. 
        Если фильтры не переданы — возвращает все записи из таблицы.
        """
        async with async_session_maker() as session:
            # Строим запрос с фильтрацией (если она есть)
            query = select(cls.model).filter_by(**filter_by)
            result = await session.execute(query)
            # scalars() превращает результат из строк (кортежей) в объекты нашей модели.
            # all() собирает их все в обычный Python-список.
            return result.scalars().all()
        
        
    @classmethod
    async def delete(cls, **filter_by):
        """Удаляет записи по фильтру."""
        async with async_session_maker() as session:
            query = delete(cls.model).filter_by(**filter_by)
            await session.execute(query)
            await session.commit()