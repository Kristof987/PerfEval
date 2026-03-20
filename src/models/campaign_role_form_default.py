from datetime import datetime, UTC

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime

from base import Base

class CampaignRoleFormDefault(Base):
    __tablename__ = "campaign_role_form_defaults"

    campaign_id = Column(
        Integer,
        ForeignKey('campaign.id', ondelete='CASCADE'),
        primary_key=True,
        nullable=False
    )
    evaluator_role = Column(
        String(255),
        primary_key=True,
        nullable=False
    )
    evaluatee_role = Column(
        String(255),
        primary_key=True,
        nullable=False
    )
    form_id = Column(
        Integer,
        ForeignKey('form.id', ondelete='RESTRICT'),
        nullable=False
    )
    updated_at = Column(DateTime, default=datetime.now(UTC), nullable=False)
