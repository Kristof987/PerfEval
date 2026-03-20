from datetime import datetime, UTC

from sqlalchemy import Column, Integer, ForeignKey, DateTime

from base import Base

class CampaignGroup(Base):
    __tablename__ = "campaign_groups"

    campaign_id = Column(
        Integer,
        ForeignKey('campaign.id', ondelete='CASCADE'),
        primary_key=True,
        nullable=False
    )
    group_id = Column(
        Integer,
        ForeignKey('organisation_groups.id', ondelete='CASCADE'),
        primary_key=True,
        nullable=False
    )
    assigned_at = Column(DateTime, default=datetime.now(UTC), nullable=False)
