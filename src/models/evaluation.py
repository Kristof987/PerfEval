from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, CheckConstraint
from sqlalchemy.dialects.postgresql import JSONB

from models.base import Base

class Evaluation(Base):
    __tablename__ = "evaluation"

    id = Column(Integer, primary_key=True)
    uuid = Column(String, unique=True, nullable=False)
    campaign_id = Column(Integer, nullable=False) #TODO: link to campaign
    evaluator_id = Column(Integer, ForeignKey('organisation_employees.id'), nullable=False)
    evaluatee_id = Column(Integer, ForeignKey('organisation_employees.id'), nullable=False)
    form_id = Column(Integer, nullable=False) #TODO: link to form
    status = Column(String(20), nullable=False, default='todo')
    finish_date = Column(DateTime(timezone=True))
    answers = Column(JSONB)

    __table_args__ = (
        CheckConstraint("status IN ('todo', 'pending', 'completed')", name='status_check'),
    )
