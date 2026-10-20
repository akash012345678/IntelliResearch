from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.sql import func
from app.database.session import Base

class ResearchPaper(Base):
    __tablename__ = "research_papers"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False, index=True)
    abstract = Column(Text, nullable=True)
    full_text = Column(Text, nullable=False)
    filename = Column(String(255), nullable=False)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # New JSON array fields with empty list defaults
    keywords = Column(JSON, nullable=False, server_default='[]', default=list)
    algorithms = Column(JSON, nullable=False, server_default='[]', default=list)
    datasets = Column(JSON, nullable=False, server_default='[]', default=list)
    methodologies = Column(JSON, nullable=False, server_default='[]', default=list)
    application_domains = Column(JSON, nullable=False, server_default='[]', default=list)
    metrics = Column(JSON, nullable=False, server_default='[]', default=list)
    tasks = Column(JSON, nullable=False, server_default='[]', default=list)
    applications = Column(JSON, nullable=False, server_default='[]', default=list)

    # Structured provenance & evidence detail fields
    keyword_details = Column(JSON, nullable=False, server_default='[]', default=list)
    algorithm_details = Column(JSON, nullable=False, server_default='[]', default=list)
    dataset_details = Column(JSON, nullable=False, server_default='[]', default=list)
    methodology_details = Column(JSON, nullable=False, server_default='[]', default=list)

    def __repr__(self) -> str:
        return f"<ResearchPaper(id={self.id}, title='{self.title[:30]}...', filename='{self.filename}')>"


