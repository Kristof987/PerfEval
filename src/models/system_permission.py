from sqlalchemy import Column, Integer, String

from models.base import Base

class SystemPermission(Base):
    __tablename__ = "system_permissions"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String)