from sqlalchemy import Column, Integer, String, BigInteger
from sqlalchemy.orm import relationship
from app.database import Base


class Student(Base):
    __tablename__ = 'students'

    id = Column(Integer, primary_key=True, index=True)
    max_id = Column(BigInteger, unique=True, index=True) 
    full_name = Column(String, nullable=False)                
    group_name = Column(String, index=True, nullable=False)   
    
    # Связь: Студент имеет много результатов
    results = relationship("UserResult", back_populates="student")