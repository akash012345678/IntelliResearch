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
from app.schemas.proposal_persistence_schema import ProposalCreate, ProposalVersionCreate
from app.services.research_project_service import ResearchProjectService
from app.services.proposal_persistence_service import ProposalPersistenceService


class TestProposalPersistenceService(unittest.TestCase):
    """
    Unit tests for ProposalPersistenceService proposal creation, versioning, and retrieval.
    """

    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(cls.engine)
        cls.SessionLocal = sessionmaker(bind=cls.engine)

    def setUp(self):
        self.db = self.SessionLocal()
        self.project = ResearchProjectService.create_project(self.db, ResearchProjectCreate(name="Proposal Test Project"))
        self.sample_proposal_data_v1 = {
            "title": "Autonomous Proposal V1",
            "abstract": "Abstract V1",
            "problem_statement": "Problem V1",
            "generation_mode": "template"
        }
        self.sample_proposal_data_v2 = {
            "title": "Autonomous Proposal V2 (Edited)",
            "abstract": "Abstract V2 (Revised)",
            "problem_statement": "Problem V1",
            "generation_mode": "template"
        }

    def tearDown(self):
        self.db.rollback()
        for table in reversed(Base.metadata.sorted_tables):
            self.db.execute(table.delete())
        self.db.commit()
        self.db.close()

    def test_01_create_proposal_version_1(self):
        """Test persisting a proposal draft creates Version 1 automatically."""
        create_data = ProposalCreate(
            project_id=self.project.id,
            source_direction_id="dir_1",
            title="Autonomous Proposal V1",
            proposal_data=self.sample_proposal_data_v1,
            generation_mode="template"
        )

        resp = ProposalPersistenceService.create_proposal(self.db, create_data)
        self.assertIsNotNone(resp.id)
        self.assertTrue(resp.proposal_uuid.startswith("prop_"))
        self.assertEqual(resp.current_version.version_number, 1)
        self.assertEqual(resp.current_version.proposal_data["abstract"], "Abstract V1")

    def test_02_add_proposal_version_2(self):
        """Test adding Version 2 to an existing proposal without overwriting Version 1."""
        create_data = ProposalCreate(
            project_id=self.project.id,
            source_direction_id="dir_1",
            title="Autonomous Proposal V1",
            proposal_data=self.sample_proposal_data_v1,
            generation_mode="template"
        )
        prop = ProposalPersistenceService.create_proposal(self.db, create_data)

        # Add Version 2
        ver2 = ProposalPersistenceService.save_proposal_version(
            self.db,
            proposal_id=prop.id,
            data=ProposalVersionCreate(proposal_data=self.sample_proposal_data_v2, generation_mode="template")
        )

        self.assertEqual(ver2.version_number, 2)
        self.assertEqual(ver2.proposal_data["abstract"], "Abstract V2 (Revised)")

        # Verify Version 1 remains intact
        ver1 = ProposalPersistenceService.get_proposal_version(self.db, prop.id, 1)
        self.assertEqual(ver1.version_number, 1)
        self.assertEqual(ver1.proposal_data["abstract"], "Abstract V1")

        # List all versions
        ver_list = ProposalPersistenceService.get_proposal_versions(self.db, prop.id)
        self.assertEqual(ver_list.total_versions, 2)

    def test_03_delete_proposal(self):
        """Test deleting a proposal removes it and its versions."""
        prop = ProposalPersistenceService.create_proposal(self.db, ProposalCreate(
            project_id=self.project.id,
            title="To Delete",
            proposal_data=self.sample_proposal_data_v1
        ))

        ProposalPersistenceService.delete_proposal(self.db, prop.id)
        proposals = ProposalPersistenceService.list_project_proposals(self.db, self.project.id)
        self.assertEqual(len(proposals), 0)


if __name__ == "__main__":
    unittest.main()
