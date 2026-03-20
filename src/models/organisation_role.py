from sqlalchemy import Column, Integer, String, ForeignKey

from models.base import Base

class OrganisationRole(Base):
    __tablename__ = "organisation_roles"

    id = Column(Integer, primary_key=True)
    uuid = Column(String, unique=True, nullable=False)
    name = Column(String, unique=True, nullable=False)
    description = Column(String)
