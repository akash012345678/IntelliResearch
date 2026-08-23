import sys
import unittest
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database.session import Base
from app.models.paper_model import ResearchPaper
from app.models.project_model import ResearchProject, ProjectPaper
from app.services.global_research_intelligence_service import GlobalResearchIntelligenceService
from app.services.project_intelligence_service import ProjectIntelligenceService

SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test_relationship_dedup.db"
engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class TestPaperRelationshipDeduplication(unittest.TestCase):

    def setUp(self):
        Base.metadata.create_all(bind=engine)
        self.db = TestingSessionLocal()
        # Clean up database
        self.db.query(ProjectPaper).delete()
        self.db.query(ResearchProject).delete()
        self.db.query(ResearchPaper).delete()
        self.db.commit()

    def tearDown(self):
        self.db.close()

    def _create_paper(self, paper_id: int, title: str, abstract: str = "Abstract text"):
        p = ResearchPaper(
            id=paper_id,
            title=title,
            abstract=abstract,
            full_text=f"Full text content for paper {paper_id}",
            filename=f"paper_{paper_id}.pdf",
            keywords=["deep_learning", "computer_vision"],
            algorithms=["YOLO", "CNN"],
            datasets=["COCO"],
            methodologies=["Object Detection"],
            application_domains=["Autonomous Driving"]
        )
        self.db.add(p)
        self.db.commit()
        self.db.refresh(p)
        return p

    def test_01_four_papers_produce_at_most_six_unique_pairs(self):
        """TEST 1: 4 assigned papers produce at most 4*(4-1)/2 = 6 unique paper pairs."""
        for i in range(1, 5):
            self._create_paper(i, f"Research Paper {i}")

        project = ResearchProject(name="Test Project 4 Papers")
        self.db.add(project)
        self.db.commit()

        for i in range(1, 5):
            self.db.add(ProjectPaper(project_id=project.id, paper_id=i))
        self.db.commit()

        service = ProjectIntelligenceService()
        analysis = service.analyze_project(project.id, self.db)

        rels = analysis.paper_relationships
        self.assertLessEqual(len(rels), 6, f"Expected at most 6 relationships for 4 papers, got {len(rels)}")

    def test_02_mirrored_pairs_collapsed(self):
        """TEST 2: A-B and B-A collapse into one canonical relationship."""
        p1 = self._create_paper(10, "Paper Alpha")
        p2 = self._create_paper(20, "Paper Beta")

        project = ResearchProject(name="Test Mirrored")
        self.db.add(project)
        self.db.commit()

        self.db.add(ProjectPaper(project_id=project.id, paper_id=10))
        self.db.add(ProjectPaper(project_id=project.id, paper_id=20))
        self.db.commit()

        service = ProjectIntelligenceService()
        analysis = service.analyze_project(project.id, self.db)

        rels = analysis.paper_relationships
        self.assertEqual(len(rels), 1)
        r = rels[0]
        self.assertEqual(min(r.source_paper_id, r.target_paper_id), 10)
        self.assertEqual(max(r.source_paper_id, r.target_paper_id), 20)

    def test_03_self_relationships_never_returned(self):
        """TEST 3: A-A self-relationship is never created or returned."""
        p1 = self._create_paper(100, "Paper Solo")
        p2 = self._create_paper(101, "Paper Duo")

        project = ResearchProject(name="Test Self Rel")
        self.db.add(project)
        self.db.commit()

        self.db.add(ProjectPaper(project_id=project.id, paper_id=100))
        self.db.add(ProjectPaper(project_id=project.id, paper_id=101))
        self.db.commit()

        service = ProjectIntelligenceService()
        analysis = service.analyze_project(project.id, self.db)

        rels = analysis.paper_relationships
        for r in rels:
            self.assertNotEqual(r.source_paper_id, r.target_paper_id, f"Self relationship found for paper {r.source_paper_id}")

    def test_04_duplicate_titles_do_not_cause_incorrect_deduplication(self):
        """TEST 4: Papers with identical titles but different IDs are deduplicated by ID, not title."""
        p1 = self._create_paper(1, "Identical Paper Title")
        p2 = self._create_paper(2, "Identical Paper Title")

        project = ResearchProject(name="Test Duplicate Titles")
        self.db.add(project)
        self.db.commit()
        self.db.add(ProjectPaper(project_id=project.id, paper_id=1))
        self.db.add(ProjectPaper(project_id=project.id, paper_id=2))
        self.db.commit()

        service = ProjectIntelligenceService()
        analysis = service.analyze_project(project.id, self.db)

        rels = analysis.paper_relationships
        self.assertEqual(len(rels), 1)
        self.assertNotEqual(rels[0].source_paper_id, rels[0].target_paper_id)

    def test_05_different_paper_ids_with_identical_titles_remain_separate(self):
        """TEST 5: Different paper IDs with identical titles produce a valid pair."""
        p1 = self._create_paper(101, "Shared Title Study")
        p2 = self._create_paper(102, "Shared Title Study")

        service = GlobalResearchIntelligenceService()
        res = service.analyze_collection(db_session=self.db)
        rels = res["paper_relationships"]

        self.assertEqual(len(rels), 1)
        r = rels[0]
        self.assertIn(r["source_paper_id"], [101, 102])
        self.assertIn(r["target_paper_id"], [101, 102])
        self.assertNotEqual(r["source_paper_id"], r["target_paper_id"])

    def test_06_100pct_similarity_between_different_papers_allowed(self):
        """TEST 6: 100% (high) similarity between two different papers is allowed."""
        p1 = self._create_paper(301, "Identical Content Paper A", "Identical abstract text for testing")
        p2 = self._create_paper(302, "Identical Content Paper B", "Identical abstract text for testing")

        project = ResearchProject(name="Test 100pct Diff Papers")
        self.db.add(project)
        self.db.commit()
        self.db.add(ProjectPaper(project_id=project.id, paper_id=301))
        self.db.add(ProjectPaper(project_id=project.id, paper_id=302))
        self.db.commit()

        service = ProjectIntelligenceService()
        analysis = service.analyze_project(project.id, self.db)

        rels = analysis.paper_relationships
        self.assertEqual(len(rels), 1)
        self.assertNotEqual(rels[0].source_paper_id, rels[0].target_paper_id)
        self.assertGreaterEqual(rels[0].similarity_score, 90.0)

    def test_07_100pct_similarity_self_paper_never_returned(self):
        """TEST 7: 100% similarity of a paper with itself is never returned."""
        p1 = self._create_paper(500, "Single Unique Paper", "Unique text")

        service = GlobalResearchIntelligenceService()
        res = service.analyze_collection(db_session=self.db)
        rels = res["paper_relationships"]

        for r in rels:
            self.assertNotEqual(r["source_paper_id"], r["target_paper_id"])

    def test_08_project_scoped_connections_only_use_assigned_papers(self):
        """TEST 8: Project-scoped connections only compute pairs among assigned project papers."""
        p1 = self._create_paper(1, "Proj A Paper 1")
        p2 = self._create_paper(2, "Proj A Paper 2")
        p3 = self._create_paper(3, "Proj B Paper 3")

        projA = ResearchProject(name="Project A")
        self.db.add(projA)
        self.db.commit()
        self.db.add(ProjectPaper(project_id=projA.id, paper_id=1))
        self.db.add(ProjectPaper(project_id=projA.id, paper_id=2))
        self.db.commit()

        service = ProjectIntelligenceService()
        analysis = service.analyze_project(projA.id, self.db)

        rels = analysis.paper_relationships
        self.assertEqual(len(rels), 1)
        valid_ids = {1, 2}
        self.assertIn(rels[0].source_paper_id, valid_ids)
        self.assertIn(rels[0].target_paper_id, valid_ids)

    def test_09_global_intelligence_remains_global(self):
        """TEST 9: Global research intelligence computes across all collection papers."""
        for i in range(1, 6):
            self._create_paper(i, f"Global Paper {i}")

        service = GlobalResearchIntelligenceService()
        res = service.analyze_collection(db_session=self.db)
        rels = res["paper_relationships"]

        # 5 papers -> 5*4/2 = 10 pairs
        self.assertEqual(len(rels), 10)


if __name__ == "__main__":
    unittest.main()
