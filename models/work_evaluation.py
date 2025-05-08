from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from database import Base

class WorkEvaluation(Base):
    __tablename__ = 'work_evaluations'
    
    id = Column(Integer, primary_key=True)
    score = Column(Integer, nullable=False)
    comment = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<WorkEvaluation(id={self.id}, score={self.score})>" 