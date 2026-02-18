

from app.dao.student import StudentDAO
from app.dao.teacher import TeacherDAO

# Хранилище состояний: {user_id: "название_состояния"}
USER_STATES = {}

# Временное хранилище данных регистрации: {user_id: {"name": "...", "role": "..."}}
TEMP_DATA = {}

async def get_user_role_and_data(user_id: int):
    """Определяет роль пользователя"""
    student = await StudentDAO.find_one_or_none(max_id=user_id)
    if student: 
        return "student", student
    
    teacher = await TeacherDAO.find_one_or_none(max_id=user_id)
    if teacher: 
        return "teacher", teacher
    
    return None, None

async def register_user(user_id: int, role: str, text: str):
    """Логика сохранения пользователя в зависимости от роли"""
    if role == "student":
        await StudentDAO.add(max_id=user_id, full_name=text, group_name=text.upper())
    elif role == "teacher":
        await TeacherDAO.add(max_id=user_id, full_name=text)
    
    if user_id in USER_STATES:
        del USER_STATES[user_id]