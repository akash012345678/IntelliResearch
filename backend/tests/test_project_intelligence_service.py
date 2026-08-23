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
from app.models.paper_model import ResearchPaper
from app.schemas.project_schema import ResearchProjectCreate
from app.schemas.proposal_persistence_schema import ProposalCreate
from app.services.research_project_service import ResearchProjectService
from app.services.proposal_persistence_service import ProposalPersistenceService
from app.services.project_intelligence_service import ProjectIntelligenceService


class TestProjectIntelligenceService(unittest.TestCase):
    """
    Unit tests for project-scoped research intelligence calculation.
    """

    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(cls.engine)
        cls.SessionLocal = sessionmaker(bind=cls.engine)

    def setUp(self):
        self.db = self.SessionLocal()

        # Add 3 test papers
        self.p1 = ResearchPaper(
            title="Driver Drowsiness Detection using CNN",
            abstract="CNN based visual driver drowsiness monitoring.",
            full_text="Sample full text for paper 1",
            filename="paper1.pdf",
            keywords=["drowsiness", "vision"],
            algorithms=["CNN"],
            datasets=["NTHU-DDD"],
            methodologies=["Deep Learning"],
            application_domains=["Autonomous Driving"]
        )
        self.p2 = ResearchPaper(
            title="Temporal Modeling for Fatigue with LSTM",
            abstract="Recurrent neural network monitoring for driver fatigue.",
            full_text="Sample full text for paper 2",
            filename="paper2.pdf",
            keywords=["drowsiness", "recurrent"],
            algorithms=["LSTM"],
            datasets=["NTHU-DDD"],
            methodologies=["Deep Learning"],
            application_domains=["Autonomous Driving"]
        )
        self.p3 = ResearchPaper(
            title="Unrelated Paper on Quantum Computing",
            abstract="Quantum algorithms and Qubit error correction.",
            full_text="Sample full text for paper 3",
            filename="paper3.pdf",
            keywords=["quantum", "qubit"],
            algorithms=["Shor Algorithm"],
            datasets=["Qiskit-Bench"],
            methodologies=["Quantum Circuit"],
            application_domains=["Physics"]
        )

        self.db.add_all([self.p1, self.p2, self.p3])
        self.db.commit()

        # Create Project & assign ONLY p1 and p2 (NOT p3)
        self.project = ResearchProjectService.create_project(self.db, ResearchProjectCreate(
            name="Driver Safety Intelligence Project"
        ))
        ResearchProjectService.add_paper_to_project(self.db, self.project.id, self.p1.id)
        ResearchProjectService.add_paper_to_project(self.db, self.project.id, self.p2.id)


    def tearDown(self):
        self.db.rollback()
        for table in reversed(Base.metadata.sorted_tables):
            self.db.execute(table.delete())
        self.db.commit()
        self.db.close()

    def test_01_analyze_project_scoped_isolation(self):
        """Verify project analysis analyzes ONLY assigned papers (2 papers, NOT 3)."""
        res = ProjectIntelligenceService.analyze_project(self.project.id, self.db)
        self.assertEqual(res.collection_summary.total_papers, 2)
        self.assertEqual(len(res.paper_landscape), 2)

        paper_ids = [p.id for p in res.paper_landscape]
        self.assertIn(self.p1.id, paper_ids)
        self.assertIn(self.p2.id, paper_ids)
        self.assertNotIn(self.p3.id, paper_ids)

    def test_02_shared_concepts_and_coverage(self):
        """Verify shared concept classification and coverage percentage calculation."""
        res = ProjectIntelligenceService.analyze_project(self.project.id, self.db)
        algos = res.shared_concepts["algorithms"]
        algo_names = [a.name for a in algos]
        self.assertIn("CNN", algo_names)
        self.assertIn("LSTM", algo_names)

        # CNN appears in 1/2 papers -> UNDERREPRESENTED
        cnn_item = next(a for a in algos if a.name == "CNN")
        self.assertEqual(cnn_item.paper_count, 1)
        self.assertEqual(cnn_item.coverage_percentage, 50.0)
        self.assertEqual(cnn_item.classification, "UNDERREPRESENTED")

        # NTHU-DDD dataset appears in 2/2 papers -> COMMON
        datasets = res.shared_concepts["datasets"]
        nthu_item = next(d for d in datasets if d.name == "NTHU-DDD")
        self.assertEqual(nthu_item.paper_count, 2)
        self.assertEqual(nthu_item.coverage_percentage, 100.0)
        self.assertEqual(nthu_item.classification, "COMMON")

    def test_03_empty_project_state(self):
        """Verify empty project with 0 papers returns clean empty collection summary."""
        empty_proj = ResearchProjectService.create_project(self.db, ResearchProjectCreate(name="Empty Project"))
        res = ProjectIntelligenceService.analyze_project(empty_proj.id, self.db)
        self.assertEqual(res.collection_summary.total_papers, 0)
        self.assertEqual(len(res.paper_landscape), 0)

    def test_04_proposal_traceability(self):
        """Verify saved proposal is connected in Proposal Traceability."""
        prop = ProposalPersistenceService.create_proposal(self.db, ProposalCreate(
            project_id=self.project.id,
            source_direction_id="dir_1",
            title="Drowsiness Proposal V1",
            proposal_data={
                "title": "Drowsiness Proposal V1",
                "candidate_algorithms": ["CNN", "LSTM"],
                "supporting_papers": [{"paper_id": self.p1.id, "title": self.p1.title}]
            }
        ))

        res = ProjectIntelligenceService.analyze_project(self.project.id, self.db)
        self.assertEqual(len(res.proposal_traceability), 1)
        tr = res.proposal_traceability[0]
        self.assertEqual(tr.proposal_id, prop.id)
        self.assertEqual(tr.title, "Drowsiness Proposal V1")
        self.assertEqual(tr.current_version_number, 1)


if __name__ == "__main__":
    unittest.main()
