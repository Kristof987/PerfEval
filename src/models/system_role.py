from sqlalchemy import Column, Integer, String, ForeignKey

from models.base import Base

class SystemRole(Base):
    __tablename__ = "system_roles"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    system_permission_id = Column(Integer, ForeignKey('system_permissions.id'))
