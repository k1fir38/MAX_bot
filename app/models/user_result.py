from sqlalchemy import BigInteger, Column, Integer, String, Text, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from app.database import Base


class UserResult(Base):
    __tablename__ = 'results'

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey('students.id', ondelete='SET NULL'), nullable=True) # Меняем CASCADE на SET NULL
    student_max_id = Column(BigInteger, index=True)      
    student_name = Column(String)  
    student_group = Column(String) 
    assignment_id = Column(Integer, ForeignKey('assignments.id')) 
          
    grade = Column(Integer, nullable=True)  
    feedback = Column(Text, nullable=True)  
    
    submitted_at = Column(DateTime(timezone=True), server_default=func.now()) 

    # Связи
    student = relationship("Student", back_populates="results")
    assignment = relationship("Assignment", back_populates="results")