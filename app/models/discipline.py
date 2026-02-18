from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.database import Base

class Discipline(Base):
    __tablename__ = 'disciplines'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False) 
    
    # Связь: Дисциплина имеет много заданий
    assignments = relationship("Assignment", back_populates="discipline")