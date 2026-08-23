import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.project_model import ResearchProject, ProjectPaper, SavedResearchDirection
from app.models.proposal_model import Proposal
from app.models.paper_model import ResearchPaper
from app.schemas.project_schema import (
    ResearchProjectCreate,
    ResearchProjectUpdate,
    ResearchProjectResponse,
    ProjectPaperResponse,
    BulkAddPapersResponse,
    AvailablePaperResponse,
    SavedDirectionResponse,
    ProposalSummaryResponse,
    ProjectDetailResponse
)

logger = logging.getLogger(__name__)


class ResearchProjectService:
    """
    Service layer for managing Research Projects and Project-Paper associations.
    """

    @classmethod
    def _build_project_paper_response(cls, assoc: ProjectPaper) -> ProjectPaperResponse:
        p = assoc.paper
        return ProjectPaperResponse(
            project_id=assoc.project_id,
            paper_id=p.id,
            title=p.title,
            filename=p.filename,
            abstract=p.abstract,
            keywords=p.keywords or [],
            algorithms=p.algorithms or [],
            datasets=p.datasets or [],
            methodologies=p.methodologies or [],
            application_domains=p.application_domains or [],
            uploaded_at=p.uploaded_at.isoformat() if p.uploaded_at else None,
            added_at=assoc.added_at.isoformat()
        )

    @classmethod
    def create_project(cls, db: Session, data: ResearchProjectCreate) -> ResearchProjectResponse:
        """Create a new Research Project."""
        project = ResearchProject(
            name=data.name.strip(),
            description=data.description.strip() if data.description else None,
            status=data.status if data.status in ("ACTIVE", "ARCHIVED") else "ACTIVE"
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        logger.info(f"Created ResearchProject id={project.id}, name='{project.name}'")
        return cls._to_project_response(project, db)

    @classmethod
    def get_project(cls, db: Session, project_id: int) -> ProjectDetailResponse:
        """Fetch detailed information for a Research Project including papers, directions, and proposals."""
        project = db.query(ResearchProject).filter(ResearchProject.id == project_id).first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Research Project with ID {project_id} not found."
            )

        # Build papers response with full metadata
        papers_resp = []
        for assoc in project.project_papers:
            if assoc.paper:
                papers_resp.append(cls._build_project_paper_response(assoc))

        # Build saved directions response
        directions_resp = []
        for d in project.saved_directions:
            directions_resp.append(SavedDirectionResponse(
                id=d.id,
                project_id=d.project_id,
                source_direction_id=d.source_direction_id,
                title=d.title,
                description=d.description,
                confidence=d.confidence,
                direction_data=d.direction_data,
                created_at=d.created_at.isoformat()
            ))

        # Build proposals summary response
        proposals_resp = []
        for p in project.proposals:
            curr_ver = len(p.versions)
            proposals_resp.append(ProposalSummaryResponse(
                id=p.id,
                proposal_uuid=p.proposal_uuid,
                project_id=p.project_id,
                source_direction_id=p.source_direction_id,
                title=p.title,
                status=p.status,
                current_version_number=curr_ver if curr_ver > 0 else 1,
                created_at=p.created_at.isoformat(),
                updated_at=p.updated_at.isoformat()
            ))

        return ProjectDetailResponse(
            id=project.id,
            name=project.name,
            description=project.description,
            status=project.status,
            created_at=project.created_at.isoformat(),
            updated_at=project.updated_at.isoformat(),
            paper_count=len(papers_resp),
            direction_count=len(directions_resp),
            proposal_count=len(proposals_resp),
            papers=papers_resp,
            saved_directions=directions_resp,
            proposals=proposals_resp
        )

    @classmethod
    def list_projects(cls, db: Session) -> List[ResearchProjectResponse]:
        """List all Research Projects with counts."""
        projects = db.query(ResearchProject).order_by(ResearchProject.created_at.desc()).all()
        return [cls._to_project_response(p, db) for p in projects]

    @classmethod
    def update_project(cls, db: Session, project_id: int, data: ResearchProjectUpdate) -> ResearchProjectResponse:
        """Update an existing Research Project."""
        project = db.query(ResearchProject).filter(ResearchProject.id == project_id).first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Research Project with ID {project_id} not found."
            )

        if data.name is not None:
            project.name = data.name.strip()
        if data.description is not None:
            project.description = data.description.strip() if data.description else None
        if data.status is not None and data.status in ("ACTIVE", "ARCHIVED"):
            project.status = data.status

        db.commit()
        db.refresh(project)
        logger.info(f"Updated ResearchProject id={project.id}")
        return cls._to_project_response(project, db)

    @classmethod
    def delete_project(cls, db: Session, project_id: int) -> None:
        """
        Delete a Research Project. Cascades to remove project associations, directions, and proposals,
        WITHOUT deleting underlying ResearchPaper records.
        """
        project = db.query(ResearchProject).filter(ResearchProject.id == project_id).first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Research Project with ID {project_id} not found."
            )

        db.delete(project)
        db.commit()
        logger.info(f"Deleted ResearchProject id={project_id}")

    @classmethod
    def add_paper_to_project(cls, db: Session, project_id: int, paper_id: int) -> ProjectPaperResponse:
        """Assign a ResearchPaper to a ResearchProject."""
        project = db.query(ResearchProject).filter(ResearchProject.id == project_id).first()
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project {project_id} not found.")

        paper = db.query(ResearchPaper).filter(ResearchPaper.id == paper_id).first()
        if not paper:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Paper {paper_id} not found.")

        existing = db.query(ProjectPaper).filter(
            ProjectPaper.project_id == project_id,
            ProjectPaper.paper_id == paper_id
        ).first()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Paper {paper_id} is already assigned to Project {project_id}."
            )

        assoc = ProjectPaper(project_id=project_id, paper_id=paper_id)
        db.add(assoc)
        db.commit()
        db.refresh(assoc)
        logger.info(f"Assigned paper_id={paper_id} to project_id={project_id}")

        return cls._build_project_paper_response(assoc)

    @classmethod
    def bulk_add_papers(cls, db: Session, project_id: int, paper_ids: List[int]) -> BulkAddPapersResponse:
        """Bulk assign multiple ResearchPaper IDs to a ResearchProject."""
        project = db.query(ResearchProject).filter(ResearchProject.id == project_id).first()
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project {project_id} not found.")

        added = []
        already_assigned = []
        not_found = []

        existing_assocs = db.query(ProjectPaper.paper_id).filter(ProjectPaper.project_id == project_id).all()
        assigned_ids = {a[0] for a in existing_assocs}

        for pid in paper_ids:
            paper = db.query(ResearchPaper).filter(ResearchPaper.id == pid).first()
            if not paper:
                not_found.append(pid)
            elif pid in assigned_ids:
                already_assigned.append(pid)
            else:
                assoc = ProjectPaper(project_id=project_id, paper_id=pid)
                db.add(assoc)
                assigned_ids.add(pid)
                added.append(pid)

        if added:
            db.commit()
            logger.info(f"Bulk assigned {len(added)} papers to project_id={project_id}")

        return BulkAddPapersResponse(
            added=added,
            already_assigned=already_assigned,
            not_found=not_found
        )

    @classmethod
    def remove_paper_from_project(cls, db: Session, project_id: int, paper_id: int) -> None:
        """Remove a ResearchPaper assignment from a ResearchProject without deleting the paper."""
        assoc = db.query(ProjectPaper).filter(
            ProjectPaper.project_id == project_id,
            ProjectPaper.paper_id == paper_id
        ).first()

        if not assoc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Association between project {project_id} and paper {paper_id} not found."
            )

        db.delete(assoc)
        db.commit()
        logger.info(f"Removed paper_id={paper_id} from project_id={project_id}")

    @classmethod
    def get_project_papers(cls, db: Session, project_id: int) -> List[ProjectPaperResponse]:
        """Fetch all papers assigned to a project with full metadata."""
        project = db.query(ResearchProject).filter(ResearchProject.id == project_id).first()
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project {project_id} not found.")

        result = []
        for assoc in project.project_papers:
            if assoc.paper:
                result.append(cls._build_project_paper_response(assoc))
        return result

    @classmethod
    def get_available_papers(
        cls,
        db: Session,
        project_id: int,
        search: Optional[str] = None,
        keyword: Optional[str] = None,
        algorithm: Optional[str] = None,
        dataset: Optional[str] = None,
        methodology: Optional[str] = None,
        domain: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[AvailablePaperResponse]:
        """Fetch ResearchPaper records NOT assigned to the given project, with search and tag filtering."""
        project = db.query(ResearchProject).filter(ResearchProject.id == project_id).first()
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project {project_id} not found.")

        assigned_tuples = db.query(ProjectPaper.paper_id).filter(ProjectPaper.project_id == project_id).all()
        assigned_ids = {t[0] for t in assigned_tuples}

        query = db.query(ResearchPaper)
        if assigned_ids:
            query = query.filter(ResearchPaper.id.notin_(assigned_ids))

        if search and search.strip():
            s = search.strip().lower()
            query = query.filter(ResearchPaper.title.ilike(f"%{s}%"))

        all_candidates = query.order_by(ResearchPaper.uploaded_at.desc()).all()

        filtered = []
        for p in all_candidates:
            if keyword and keyword.strip():
                k_target = keyword.strip().lower()
                if not any(k_target in (k or "").lower() for k in (p.keywords or [])):
                    continue

            if algorithm and algorithm.strip():
                a_target = algorithm.strip().lower()
                if not any(a_target in (a or "").lower() for a in (p.algorithms or [])):
                    continue

            if dataset and dataset.strip():
                d_target = dataset.strip().lower()
                if not any(d_target in (d or "").lower() for d in (p.datasets or [])):
                    continue

            if methodology and methodology.strip():
                m_target = methodology.strip().lower()
                if not any(m_target in (m or "").lower() for m in (p.methodologies or [])):
                    continue

            if domain and domain.strip():
                dom_target = domain.strip().lower()
                if not any(dom_target in (dom or "").lower() for dom in (p.application_domains or [])):
                    continue

            filtered.append(AvailablePaperResponse(
                id=p.id,
                title=p.title,
                abstract=p.abstract,
                filename=p.filename,
                keywords=p.keywords or [],
                algorithms=p.algorithms or [],
                datasets=p.datasets or [],
                methodologies=p.methodologies or [],
                application_domains=p.application_domains or [],
                uploaded_at=p.uploaded_at.isoformat() if p.uploaded_at else ""
            ))

        return filtered[skip: skip + limit]

    @classmethod
    def _to_project_response(cls, project: ResearchProject, db: Session) -> ResearchProjectResponse:
        paper_cnt = db.query(ProjectPaper).filter(ProjectPaper.project_id == project.id).count()
        dir_cnt = db.query(SavedResearchDirection).filter(SavedResearchDirection.project_id == project.id).count()
        prop_cnt = db.query(Proposal).filter(Proposal.project_id == project.id).count()

        return ResearchProjectResponse(
            id=project.id,
            name=project.name,
            description=project.description,
            status=project.status,
            created_at=project.created_at.isoformat(),
            updated_at=project.updated_at.isoformat(),
            paper_count=paper_cnt,
            direction_count=dir_cnt,
            proposal_count=prop_cnt
        )

