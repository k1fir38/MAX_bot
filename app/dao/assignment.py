
from app.dao.base import BaseDAO
from app.models.assignment import Assignment


class AssignmentDAO(BaseDAO):
    model = Assignment