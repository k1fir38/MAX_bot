
from app.dao.base import BaseDAO
from app.models.student import Student


class StudentDAO(BaseDAO):
    model = Student