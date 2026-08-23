import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.project_model import ResearchProject, ProjectPaper
from app.models.paper_model import ResearchPaper
from app.schemas.citation_schema import ReferenceItem

logger = logging.getLogger(__name__)


class AcademicCitationService:
    """
    Service for managing, formatting, and rendering verified project reference citations in IEEE, APA, and Harvard styles.
    Strictly avoids metadata fabrication for missing authors, years, or DOIs.
    """

    @classmethod
    def get_project_references(cls, db: Session, project_id: int) -> List[ReferenceItem]:
        project = db.query(ResearchProject).filter(ResearchProject.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail=f"Research project {project_id} not found")

        papers = [assoc.paper for assoc in project.project_papers if assoc.paper]
        references: List[ReferenceItem] = []

        for idx, p in enumerate(papers, start=1):
            raw_authors = getattr(p, 'authors', None)
            authors_str = str(raw_authors).strip() if raw_authors else "Authors Not Recorded"

            raw_year = getattr(p, 'publication_year', None)
            year_str = str(raw_year) if raw_year else "n.d."

            venue_str = getattr(p, 'venue', None) or "IntelliResearch Collection"
            doi_str = getattr(p, 'doi', None) or "N/A"
            url_str = getattr(p, 'url', None) or "N/A"

            has_complete = bool(raw_authors and raw_year)

            # IEEE Format: [1] A. Author, "Title," Venue, Year.
            ieee = f"[{idx}] {authors_str}, \"{p.title},\" {venue_str}, {year_str}."
            if not has_complete:
                ieee += " [Bibliographic metadata incomplete]"

            # APA Format: Author (Year). Title. Venue.
            apa = f"{authors_str} ({year_str}). {p.title}. {venue_str}."
            if not has_complete:
                apa += " [Bibliographic metadata incomplete]"

            # Harvard Format: Author, Year. Title. Venue.
            harvard = f"{authors_str}, {year_str}. {p.title}. {venue_str}."
            if not has_complete:
                harvard += " [Bibliographic metadata incomplete]"

            references.append(
                ReferenceItem(
                    id=idx,
                    paper_id=p.id,
                    title=p.title,
                    authors=authors_str,
                    publication_year=year_str,
                    source_venue=venue_str,
                    doi=doi_str,
                    url=url_str,
                    formatted_ieee=ieee,
                    formatted_apa=apa,
                    formatted_harvard=harvard,
                    has_complete_metadata=has_complete,
                    citation_key=f"[{idx}]"
                )
            )

        return references
