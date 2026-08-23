import sys
import unittest
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.database.session import Base
import app.models  # noqa: F401
from app.schemas.project_schema import ResearchProjectCreate
from app.schemas.proposal_persistence_schema import ProposalCreate
from app.schemas.proposal_edit_schema import ProposalEditRequest
from app.services.research_project_service import ResearchProjectService
from app.services.proposal_persistence_service import ProposalPersistenceService


class TestProposalVersioningService(unittest.TestCase):
    """
    Unit tests for editing, diff comparison, and restoring proposal versions.
    """

    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(cls.engine)
        cls.SessionLocal = sessionmaker(bind=cls.engine)

    def setUp(self):
        self.db = self.SessionLocal()
        self.project = ResearchProjectService.create_project(self.db, ResearchProjectCreate(name="Versioning Test Project"))
        self.proposal = ProposalPersistenceService.create_proposal(self.db, ProposalCreate(
            project_id=self.project.id,
            source_direction_id="dir_1",
            title="Autonomous Driving Proposal V1",
            proposal_data={
                "title": "Autonomous Driving Proposal V1",
                "abstract": "Abstract V1",
                "problem_statement": "Problem V1",
                "candidate_algorithms": ["YOLOv5"],
                "supporting_papers": [{"paper_id": 1, "title": "Paper 1"}]
            },
            generation_mode="template"
        ))

    def tearDown(self):
        self.db.rollback()
        for table in reversed(Base.metadata.sorted_tables):
            self.db.execute(table.delete())
        self.db.commit()
        self.db.close()

    def test_01_edit_proposal_creates_new_version(self):
        """Test editing a proposal creates Version 2 and leaves Version 1 immutable."""
        edit_req = ProposalEditRequest(
            title="Autonomous Driving Proposal V2 (Edited)",
            abstract="Abstract V2 (Refined)",
            candidate_algorithms=["YOLOv5", "YOLOv8"],
            change_summary="Added YOLOv8 algorithm and refined abstract"
        )

        ver2 = ProposalPersistenceService.edit_proposal(self.db, self.proposal.id, edit_req)
        self.assertEqual(ver2.version_number, 2)
        self.assertEqual(ver2.generation_mode, "manual")
        self.assertEqual(ver2.change_summary, "Added YOLOv8 algorithm and refined abstract")
        self.assertEqual(ver2.proposal_data["abstract"], "Abstract V2 (Refined)")

        # Verify Version 1 remains unchanged
        ver1 = ProposalPersistenceService.get_proposal_version(self.db, self.proposal.id, 1)
        self.assertEqual(ver1.proposal_data["abstract"], "Abstract V1")
        self.assertEqual(ver1.proposal_data["candidate_algorithms"], ["YOLOv5"])

    def test_02_compare_versions(self):
        """Test section-level diff comparison between Version 1 and Version 2."""
        ProposalPersistenceService.edit_proposal(self.db, self.proposal.id, ProposalEditRequest(
            abstract="Abstract V2 (Changed)",
            change_summary="Changed abstract"
        ))

        diff = ProposalPersistenceService.compare_versions(self.db, self.proposal.id, 1, 2)
        self.assertEqual(diff.version_a, 1)
        self.assertEqual(diff.version_b, 2)
        self.assertTrue(diff.total_changes > 0)
        changed_sections = [c.section for c in diff.changes]
        self.assertIn("abstract", changed_sections)

    def test_03_restore_version_creates_new_version(self):
        """Test restoring Version 1 when at Version 2 creates Version 3."""
        # Create Version 2
        ProposalPersistenceService.edit_proposal(self.db, self.proposal.id, ProposalEditRequest(
            abstract="Abstract V2",
            change_summary="Edit for V2"
        ))

        # Restore Version 1
        ver3 = ProposalPersistenceService.restore_version(self.db, self.proposal.id, 1)
        self.assertEqual(ver3.version_number, 3)
        self.assertEqual(ver3.generation_mode, "restored")
        self.assertTrue(ver3.is_restored)
        self.assertEqual(ver3.change_summary, "Restored from version 1")
        self.assertEqual(ver3.proposal_data["abstract"], "Abstract V1")

        # Verify total version count is 3
        history = ProposalPersistenceService.get_proposal_versions(self.db, self.proposal.id)
        self.assertEqual(history.total_versions, 3)
        # History sorted DESC
        self.assertEqual(history.versions[0].version_number, 3)

    def test_04_empty_change_summary_rejected(self):
        """Test editing without change summary is rejected."""
        with self.assertRaises(Exception):
            ProposalPersistenceService.edit_proposal(self.db, self.proposal.id, ProposalEditRequest(
                abstract="New Abstract",
                change_summary=""
            ))


if __name__ == "__main__":
    unittest.main()
