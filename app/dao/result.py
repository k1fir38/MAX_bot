
from app.dao.base import BaseDAO
from app.models.user_result import UserResult


class ResultDAO(BaseDAO):
    model = UserResult