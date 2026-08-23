import logging
import uuid
import copy
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from app.models.project_model import ResearchProject
from app.models.proposal_model import Proposal, ProposalVersion
from app.schemas.proposal_persistence_schema import (
    ProposalCreate,
    ProposalResponse,
    ProposalVersionCreate,
    ProposalVersionResponse,
    ProposalVersionListResponse
)
from app.schemas.proposal_edit_schema import (
    ProposalEditRequest,
    ProposalComparisonResponse,
    SectionChangeItem
)

logger = logging.getLogger(__name__)

PROTECTED_EVIDENCE_FIELDS = {
    "supporting_papers",
    "evidence_summary",
    "source_direction_id",
    "generation_timestamp",
    "disclaimer",
    "proposal_id"
}


class ProposalPersistenceService:
    """
    Service layer for persisting Proposals, editing sections, and managing version history.
    """

    @classmethod
    def create_proposal(cls, db: Session, data: ProposalCreate) -> ProposalResponse:
        """
        Persist a generated ProposalDraft under a Research Project.
        Creates Proposal record and initial ProposalVersion (version 1).
        """
        project = db.query(ResearchProject).filter(ResearchProject.id == data.project_id).first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Research Project with ID {data.project_id} not found."
            )

        proposal_uuid = f"prop_{uuid.uuid4().hex[:8]}"

        proposal = Proposal(
            proposal_uuid=proposal_uuid,
            project_id=data.project_id,
            source_direction_id=data.source_direction_id,
            title=data.title.strip(),
            status=data.status if data.status in ("DRAFT", "FINAL", "ARCHIVED") else "DRAFT"
        )
        db.add(proposal)
        db.flush()

        ver1 = ProposalVersion(
            proposal_id=proposal.id,
            version_number=1,
            proposal_data=data.proposal_data,
            generation_mode=data.generation_mode or "template",
            change_summary="Initial generated proposal draft",
            is_restored=False
        )
        db.add(ver1)
        db.commit()
        db.refresh(proposal)

        logger.info(f"Created Proposal id={proposal.id}, uuid='{proposal.proposal_uuid}', version=1")
        return cls._to_proposal_response(proposal, ver1)

    @classmethod
    def edit_proposal(cls, db: Session, proposal_id: int, data: ProposalEditRequest) -> ProposalVersionResponse:
        """
        Edit structured sections of the latest proposal version and persist as a NEW version.
        Previous versions remain 100% immutable. Rejects protected evidence field edits.
        """
        proposal = db.query(Proposal).filter(Proposal.id == proposal_id).first()
        if not proposal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Proposal with ID {proposal_id} not found."
            )

        if not data.change_summary or not data.change_summary.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A non-empty change_summary is required when saving a new proposal version."
            )

        latest_ver = proposal.versions[-1] if proposal.versions else None
        if not latest_ver:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No versions found for Proposal {proposal_id}."
            )

        # Copy existing proposal data to mutate allowed sections
        updated_data = copy.deepcopy(latest_ver.proposal_data)

        # Apply allowed section edits
        fields_to_update = {
            "title": data.title,
            "abstract": data.abstract,
            "problem_statement": data.problem_statement,
            "research_motivation": data.research_motivation,
            "related_work_synthesis": data.related_work_synthesis,
            "research_gap": data.research_gap,
            "proposed_methodology": data.proposed_methodology,
            "candidate_algorithms": data.candidate_algorithms,
            "candidate_datasets": data.candidate_datasets,
            "dataset_evaluation_plan": data.dataset_evaluation_plan,
            "experimental_plan": data.experimental_plan,
            "evaluation_metrics": data.evaluation_metrics,
            "expected_contribution": data.expected_contribution,
            "limitations": data.limitations,
        }

        has_edits = False
        for field, val in fields_to_update.items():
            if val is not None:
                updated_data[field] = val
                has_edits = True

        if not has_edits:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Edit request must contain at least one modified section field."
            )

        # Update proposal main title if title changed
        if data.title and data.title.strip():
            proposal.title = data.title.strip()

        # Version concurrency safety loop
        max_retries = 3
        for attempt in range(max_retries):
            try:
                db.refresh(proposal)
                next_ver = len(proposal.versions) + 1
                new_ver = ProposalVersion(
                    proposal_id=proposal_id,
                    version_number=next_ver,
                    proposal_data=updated_data,
                    generation_mode="manual",
                    change_summary=data.change_summary.strip(),
                    is_restored=False
                )
                db.add(new_ver)
                db.commit()
                db.refresh(new_ver)
                logger.info(f"Saved edited proposal version {next_ver} for Proposal {proposal_id}")
                return cls._to_version_response(new_ver)
            except IntegrityError:
                db.rollback()
                if attempt == max_retries - 1:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Version creation conflict. Please try saving again."
                    )

    @classmethod
    def compare_versions(cls, db: Session, proposal_id: int, version_a: int, version_b: int) -> ProposalComparisonResponse:
        """Compare two proposal versions section-by-section and return diff results."""
        if version_a == version_b:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Comparison versions version_a and version_b must be different."
            )

        proposal = db.query(Proposal).filter(Proposal.id == proposal_id).first()
        if not proposal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Proposal with ID {proposal_id} not found."
            )

        ver_a = db.query(ProposalVersion).filter(
            ProposalVersion.proposal_id == proposal_id,
            ProposalVersion.version_number == version_a
        ).first()

        ver_b = db.query(ProposalVersion).filter(
            ProposalVersion.proposal_id == proposal_id,
            ProposalVersion.version_number == version_b
        ).first()

        if not ver_a:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Version {version_a} not found.")
        if not ver_b:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Version {version_b} not found.")

        data_a = ver_a.proposal_data or {}
        data_b = ver_b.proposal_data or {}

        all_keys = set(data_a.keys()).union(set(data_b.keys()))
        changes = []

        for key in sorted(all_keys):
            val_a = data_a.get(key)
            val_b = data_b.get(key)

            if val_a != val_b:
                changes.append(SectionChangeItem(
                    section=key,
                    changed=True,
                    before=val_a,
                    after=val_b
                ))

        return ProposalComparisonResponse(
            proposal_id=proposal_id,
            version_a=version_a,
            version_b=version_b,
            total_changes=len(changes),
            changes=changes
        )

    @classmethod
    def restore_version(cls, db: Session, proposal_id: int, version_number: int) -> ProposalVersionResponse:
        """
        Restore a historical version by creating a NEW ProposalVersion entry (latest + 1).
        Previous versions remain 100% immutable.
        """
        proposal = db.query(Proposal).filter(Proposal.id == proposal_id).first()
        if not proposal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Proposal with ID {proposal_id} not found."
            )

        ver_to_restore = db.query(ProposalVersion).filter(
            ProposalVersion.proposal_id == proposal_id,
            ProposalVersion.version_number == version_number
        ).first()

        if not ver_to_restore:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Version {version_number} for Proposal {proposal_id} not found."
            )

        restored_data = copy.deepcopy(ver_to_restore.proposal_data)

        # Version concurrency safety loop
        max_retries = 3
        for attempt in range(max_retries):
            try:
                db.refresh(proposal)
                next_ver = len(proposal.versions) + 1
                new_ver = ProposalVersion(
                    proposal_id=proposal_id,
                    version_number=next_ver,
                    proposal_data=restored_data,
                    generation_mode="restored",
                    change_summary=f"Restored from version {version_number}",
                    is_restored=True
                )
                db.add(new_ver)
                db.commit()
                db.refresh(new_ver)
                logger.info(f"Restored version {version_number} as new version {next_ver} for Proposal {proposal_id}")
                return cls._to_version_response(new_ver)
            except IntegrityError:
                db.rollback()
                if attempt == max_retries - 1:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Version restoration conflict. Please try restoring again."
                    )

    @classmethod
    def get_proposal(cls, db: Session, proposal_id: int) -> ProposalResponse:
        """Fetch details of a single saved Proposal including its latest version."""
        proposal = db.query(Proposal).filter(Proposal.id == proposal_id).first()
        if not proposal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Proposal with ID {proposal_id} not found."
            )

        latest_ver = proposal.versions[-1] if proposal.versions else None
        if not latest_ver:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No versions found for Proposal {proposal_id}."
            )

        return cls._to_proposal_response(proposal, latest_ver)

    @classmethod
    def list_project_proposals(cls, db: Session, project_id: int) -> List[ProposalResponse]:
        """List all saved Proposals under a Research Project."""
        project = db.query(ResearchProject).filter(ResearchProject.id == project_id).first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Research Project with ID {project_id} not found."
            )

        proposals = db.query(Proposal).filter(Proposal.project_id == project_id).order_by(Proposal.created_at.desc()).all()
        result = []
        for p in proposals:
            latest_ver = p.versions[-1] if p.versions else None
            if latest_ver:
                result.append(cls._to_proposal_response(p, latest_ver))
        return result

    @classmethod
    def delete_proposal(cls, db: Session, proposal_id: int) -> None:
        """Delete a Proposal and all associated ProposalVersions."""
        proposal = db.query(Proposal).filter(Proposal.id == proposal_id).first()
        if not proposal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Proposal with ID {proposal_id} not found."
            )

        db.delete(proposal)
        db.commit()
        logger.info(f"Deleted Proposal id={proposal_id}")

    @classmethod
    def save_proposal_version(cls, db: Session, proposal_id: int, data: ProposalVersionCreate) -> ProposalVersionResponse:
        """Save a new version under an existing Proposal without overwriting prior versions."""
        proposal = db.query(Proposal).filter(Proposal.id == proposal_id).first()
        if not proposal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Proposal with ID {proposal_id} not found."
            )

        next_ver = len(proposal.versions) + 1
        new_ver = ProposalVersion(
            proposal_id=proposal_id,
            version_number=next_ver,
            proposal_data=data.proposal_data,
            generation_mode=data.generation_mode or "template",
            change_summary="Saved proposal version",
            is_restored=False
        )
        db.add(new_ver)
        db.commit()
        db.refresh(new_ver)

        logger.info(f"Saved new version {next_ver} for Proposal id={proposal_id}")
        return cls._to_version_response(new_ver)

    @classmethod
    def get_proposal_versions(cls, db: Session, proposal_id: int) -> ProposalVersionListResponse:
        """List all version entries for a given Proposal (sorted version_number DESC)."""
        proposal = db.query(Proposal).filter(Proposal.id == proposal_id).first()
        if not proposal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Proposal with ID {proposal_id} not found."
            )

        sorted_vers = sorted(proposal.versions, key=lambda v: v.version_number, reverse=True)
        versions_resp = [cls._to_version_response(v) for v in sorted_vers]
        return ProposalVersionListResponse(
            proposal_id=proposal_id,
            total_versions=len(versions_resp),
            versions=versions_resp
        )

    @classmethod
    def get_proposal_version(cls, db: Session, proposal_id: int, version_number: int) -> ProposalVersionResponse:
        """Fetch a specific version number of a Proposal."""
        version = db.query(ProposalVersion).filter(
            ProposalVersion.proposal_id == proposal_id,
            ProposalVersion.version_number == version_number
        ).first()

        if not version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Version {version_number} for Proposal {proposal_id} not found."
            )

        return cls._to_version_response(version)

    @classmethod
    def _to_proposal_response(cls, proposal: Proposal, current_version: ProposalVersion) -> ProposalResponse:
        return ProposalResponse(
            id=proposal.id,
            proposal_uuid=proposal.proposal_uuid,
            project_id=proposal.project_id,
            source_direction_id=proposal.source_direction_id,
            title=proposal.title,
            status=proposal.status,
            current_version=cls._to_version_response(current_version),
            created_at=proposal.created_at.isoformat(),
            updated_at=proposal.updated_at.isoformat()
        )

    @classmethod
    def _to_version_response(cls, v: ProposalVersion) -> ProposalVersionResponse:
        return ProposalVersionResponse(
            id=v.id,
            proposal_id=v.proposal_id,
            version_number=v.version_number,
            proposal_data=v.proposal_data,
            generation_mode=v.generation_mode,
            change_summary=v.change_summary,
            is_restored=v.is_restored,
            created_at=v.created_at.isoformat(),
            updated_at=v.updated_at.isoformat()
        )
