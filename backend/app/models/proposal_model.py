from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey, UniqueConstraint, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.session import Base


class Proposal(Base):
    __tablename__ = "proposals"

    id = Column(Integer, primary_key=True, index=True)
    proposal_uuid = Column(String(100), unique=True, index=True, nullable=False)
    project_id = Column(Integer, ForeignKey("research_projects.id", ondelete="CASCADE"), nullable=False, index=True)
    source_direction_id = Column(String(100), nullable=True)
    title = Column(String(500), nullable=False)
    status = Column(String(50), nullable=False, default="DRAFT")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    project = relationship("ResearchProject", back_populates="proposals")
    versions = relationship("ProposalVersion", back_populates="proposal", cascade="all, delete-orphan", order_by="ProposalVersion.version_number")

    def __repr__(self) -> str:
        return f"<Proposal(id={self.id}, uuid='{self.proposal_uuid}', title='{self.title[:30]}', status='{self.status}')>"


class ProposalVersion(Base):
    __tablename__ = "proposal_versions"

    id = Column(Integer, primary_key=True, index=True)
    proposal_id = Column(Integer, ForeignKey("proposals.id", ondelete="CASCADE"), nullable=False, index=True)
    version_number = Column(Integer, nullable=False)
    proposal_data = Column(JSON, nullable=False)
    generation_mode = Column(String(50), nullable=False, default="template")
    change_summary = Column(Text, nullable=True)
    is_restored = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint('proposal_id', 'version_number', name='uq_proposal_version'),
    )

    # Relationships
    proposal = relationship("Proposal", back_populates="versions")

    def __repr__(self) -> str:
        return f"<ProposalVersion(proposal_id={self.proposal_id}, version={self.version_number}, mode='{self.generation_mode}')>"

