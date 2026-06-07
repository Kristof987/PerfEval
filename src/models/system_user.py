from sqlalchemy import Column, DateTime, ForeignKey, Integer, String

from models.base import Base


class SystemUser(Base):
    __tablename__ = "system_users"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    sys_szerep_id = Column(Integer, ForeignKey("system_roles.id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("organisation_employees.id"))
    created_at = Column(DateTime)
    last_login = Column(DateTime)
