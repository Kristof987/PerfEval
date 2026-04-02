from datetime import datetime, UTC

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import relationship

from models.base import Base

#TODO: Refactor whole class may be necessary
class Employee(Base):
    __tablename__ = "organisation_employees"

    id = Column(Integer, primary_key=True)
    uuid = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    org_role_id = Column(
        Integer,
        ForeignKey('organisation_roles.id'),
    )
    created_at = Column(DateTime, default=datetime.now(UTC), nullable=False)

    org_role = relationship("OrganisationRole", back_populates="employees")
    org_role_name = association_proxy('org_role', 'name')

    #TODO: where else do we need employee relationship?