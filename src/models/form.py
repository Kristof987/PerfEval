from sqlalchemy import Column, Integer, String
from sqlalchemy.dialects.postgresql import JSONB

from models.base import Base

class Form(Base):
    __tablename__ = "form"

    id = Column(Integer, primary_key=True)
    uuid = Column(String, unique=True, nullable=False)
    name = Column(String, unique=True, nullable=False)
    description = Column(String)
    questions = Column(JSONB, nullable=False)
