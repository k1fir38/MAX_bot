from sqlalchemy import Column, Integer, Text, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from app.database import Base


class UserResult(Base):
    __tablename__ = 'results'

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey('students.id'))       
    assignment_id = Column(Integer, ForeignKey('assignments.id')) 
    
    student_answer = Column(Text)           
    grade = Column(Integer, nullable=True)  
    feedback = Column(Text, nullable=True)  
    
    submitted_at = Column(DateTime(timezone=True), server_default=func.now()) 

    # Связи
    student = relationship("Student", back_populates="results")
    assignment = relationship("Assignment", back_populates="results")