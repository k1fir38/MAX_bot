
from app.database import Base
from app.models.student import Student
from app.models.teacher import Teacher
from app.models.discipline import Discipline
from app.models.assignment import Assignment
from app.models.user_result import UserResult

# Собираем всё в список для удобства
__all__ = [
    "Base",
    "Student",
    "Teacher",
    "Discipline",
    "Assignment",
    "UserResult",
]