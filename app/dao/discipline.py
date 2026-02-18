from app.dao.base import BaseDAO
from app.models.discipline import Discipline


class DisciplineDAO(BaseDAO):
    model = Discipline