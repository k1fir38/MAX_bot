
from app.dao.base import BaseDAO
from app.models.teacher import Teacher


class TeacherDAO(BaseDAO):
    model = Teacher