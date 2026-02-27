from sqlalchemy import BigInteger, Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Assignment(Base):
    __tablename__ = 'assignments'

    id = Column(Integer, primary_key=True, index=True)
    
    # --- ССЫЛКИ НА ДРУГИЕ ТАБЛИЦЫ ---
    discipline_id = Column(Integer, ForeignKey('disciplines.id')) 
    author_id = Column(Integer, ForeignKey('teachers.id'))
    author_max_id = Column(BigInteger, index=True)
    
    # --- ОПИСАНИЕ ЗАДАНИЯ ---
    title = Column(String)                  
    questions = Column(Text, nullable=False) 
    target_group = Column(String, index=True) 
    
    # --- ОТНОШЕНИЯ (RELATIONSHIPS) ---
    discipline = relationship("Discipline", back_populates="assignments")
    results = relationship("UserResult", back_populates="assignment")
    
    # <--- (Связь с Teacher)
    author = relationship("Teacher", back_populates="created_assignments") 