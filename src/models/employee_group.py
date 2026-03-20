from datetime import datetime, UTC

from sqlalchemy import Column, Integer, ForeignKey, DateTime

from models.base import Base

class EmployeeGroup(Base):
    __tablename__ = "employee_groups"

    employee_id = Column(
        Integer,
        ForeignKey('organisation_employees.id', ondelete='CASCADE'),
        primary_key=True,
        nullable=False
    )
    group_id = Column(
        Integer,
        ForeignKey('organisation_groups.id', ondelete='CASCADE'),
        primary_key=True,
        nullable=False
    )
    joined_at = Column(DateTime, default=datetime.now(UTC), nullable=False)
