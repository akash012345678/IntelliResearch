from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.session import Base


class ResearchProject(Base):
    __tablename__ = "research_projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default="ACTIVE")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    project_papers = relationship("ProjectPaper", back_populates="project", cascade="all, delete-orphan")
    saved_directions = relationship("SavedResearchDirection", back_populates="project", cascade="all, delete-orphan")
    proposals = relationship("Proposal", back_populates="project", cascade="all, delete-orphan")
    experiments = relationship("ResearchExperiment", back_populates="project", cascade="all, delete-orphan")
    manuscripts = relationship("ResearchManuscript", back_populates="project", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<ResearchProject(id={self.id}, name='{self.name}', status='{self.status}')>"


class ProjectPaper(Base):
    __tablename__ = "project_papers"

    project_id = Column(Integer, ForeignKey("research_projects.id", ondelete="CASCADE"), primary_key=True)
    paper_id = Column(Integer, ForeignKey("research_papers.id", ondelete="CASCADE"), primary_key=True)
    added_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    project = relationship("ResearchProject", back_populates="project_papers")
    paper = relationship("ResearchPaper")

    def __repr__(self) -> str:
        return f"<ProjectPaper(project_id={self.project_id}, paper_id={self.paper_id})>"


class SavedResearchDirection(Base):
    __tablename__ = "saved_directions"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("research_projects.id", ondelete="CASCADE"), nullable=False, index=True)
    source_direction_id = Column(String(100), nullable=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    confidence = Column(String(50), nullable=True)
    direction_data = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    project = relationship("ResearchProject", back_populates="saved_directions")

    def __repr__(self) -> str:
        return f"<SavedResearchDirection(id={self.id}, project_id={self.project_id}, title='{self.title[:30]}')>"


class ResearchExperiment(Base):
    __tablename__ = "research_experiments"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("research_projects.id", ondelete="CASCADE"), nullable=False, index=True)
    direction_id = Column(String(100), nullable=True)
    name = Column(String(255), nullable=False)
    purpose = Column(Text, nullable=True)
    experiment_type = Column(String(100), nullable=False, default="BASELINE_COMPARISON")
    status = Column(String(50), nullable=False, default="PLANNED")
    research_question = Column(Text, nullable=True)
    hypothesis_h0 = Column(Text, nullable=True)
    hypothesis_h1 = Column(Text, nullable=True)
    dataset_config = Column(JSON, nullable=True)
    baseline_config = Column(JSON, nullable=True)
    proposed_config = Column(JSON, nullable=True)
    environment_config = Column(JSON, nullable=True)
    execution_config = Column(JSON, nullable=True)
    notes = Column(Text, nullable=True)
    limitations = Column(Text, nullable=True)
    reproducibility_checklist = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    project = relationship("ResearchProject", back_populates="experiments")
    runs = relationship("ExperimentRun", back_populates="experiment", cascade="all, delete-orphan")


class ExperimentRun(Base):
    __tablename__ = "experiment_runs"

    id = Column(Integer, primary_key=True, index=True)
    experiment_id = Column(Integer, ForeignKey("research_experiments.id", ondelete="CASCADE"), nullable=False, index=True)
    run_number = Column(Integer, nullable=False, default=1)
    seed = Column(Integer, nullable=True, default=42)
    duration_seconds = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    experiment = relationship("ResearchExperiment", back_populates="runs")
    results = relationship("ExperimentResult", back_populates="run", cascade="all, delete-orphan")


class ExperimentResult(Base):
    __tablename__ = "experiment_results"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("experiment_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(String(100), nullable=False)  # Store numeric or string metric
    unit = Column(String(50), nullable=True)
    method_type = Column(String(50), nullable=False, default="proposed")  # 'baseline' | 'proposed' | 'ablation'
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    run = relationship("ExperimentRun", back_populates="results")


class ResearchManuscript(Base):
    __tablename__ = "research_manuscripts"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("research_projects.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False, default="DRAFT")  # 'DRAFT' | 'REVISED' | 'COMPLETE'
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    project = relationship("ResearchProject", back_populates="manuscripts")
    versions = relationship("ResearchManuscriptVersion", back_populates="manuscript", cascade="all, delete-orphan")


class ResearchManuscriptVersion(Base):
    __tablename__ = "research_manuscript_versions"

    id = Column(Integer, primary_key=True, index=True)
    manuscript_id = Column(Integer, ForeignKey("research_manuscripts.id", ondelete="CASCADE"), nullable=False, index=True)
    version_number = Column(Integer, nullable=False)
    content_json = Column(JSON, nullable=False)
    change_summary = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    manuscript = relationship("ResearchManuscript", back_populates="versions")

