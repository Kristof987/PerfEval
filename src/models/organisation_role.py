from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from models.base import Base

class OrganisationRole(Base):
    __tablename__ = "organisation_roles"

    id = Column(Integer, primary_key=True)
    uuid = Column(String, unique=True, nullable=False)
    name = Column(String, unique=True, nullable=False)
    description = Column(String)

    employees = relationship("Employee", back_populates="org_role")
