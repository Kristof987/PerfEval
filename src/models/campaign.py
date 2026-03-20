from datetime import datetime, UTC

from sqlalchemy import Column, Integer, String, DateTime, Boolean

from models.base import Base

class Campaign(Base):
    __tablename__ = 'campaign'

    id = Column(Integer, primary_key=True)
    uuid = Column(String, unique=True, nullable=False)
    name = Column(String, unique=True, nullable=False)
    description = Column(String)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime)
    is_active = Column(Boolean, default=True, nullable=False)
    comment = Column(String)

    #TODO: #TODO: where else do we need campaign relationship?
