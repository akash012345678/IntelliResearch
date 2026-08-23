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
from app.schemas.project_schema import ResearchProjectCreate, ResearchProjectUpdate
from app.services.research_project_service import ResearchProjectService


class TestResearchProjectService(unittest.TestCase):
    """
    Unit tests for ResearchProjectService CRUD, paper association, and deletion safety.
    """

    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(cls.engine)
        cls.SessionLocal = sessionmaker(bind=cls.engine)

    def setUp(self):
        self.db = self.SessionLocal()
        # Seed a test paper
        self.sample_paper = ResearchPaper(
            title="Sample Integration Paper",
            abstract="Sample Abstract",
            full_text="Sample Full Text",
            filename="sample_test.pdf"
        )
        self.db.add(self.sample_paper)
        self.db.commit()
        self.db.refresh(self.sample_paper)

    def tearDown(self):
        self.db.rollback()
        # Clean up database tables
        for table in reversed(Base.metadata.sorted_tables):
            self.db.execute(table.delete())
        self.db.commit()
        self.db.close()

    def test_01_create_project(self):
        """Test creating a new research project."""
        create_data = ResearchProjectCreate(name="Autonomous Driving Study", description="Study on YOLOv8")
        project = ResearchProjectService.create_project(self.db, create_data)

        self.assertIsNotNone(project.id)
        self.assertEqual(project.name, "Autonomous Driving Study")
        self.assertEqual(project.status, "ACTIVE")

    def test_02_get_and_list_projects(self):
        """Test getting and listing projects."""
        p1 = ResearchProjectService.create_project(self.db, ResearchProjectCreate(name="Project A"))
        p2 = ResearchProjectService.create_project(self.db, ResearchProjectCreate(name="Project B"))

        projects = ResearchProjectService.list_projects(self.db)
        self.assertEqual(len(projects), 2)

        details = ResearchProjectService.get_project(self.db, p1.id)
        self.assertEqual(details.name, "Project A")

    def test_03_update_project(self):
        """Test updating project fields."""
        p = ResearchProjectService.create_project(self.db, ResearchProjectCreate(name="Old Name"))
        updated = ResearchProjectService.update_project(self.db, p.id, ResearchProjectUpdate(name="New Name", status="ARCHIVED"))

        self.assertEqual(updated.name, "New Name")
        self.assertEqual(updated.status, "ARCHIVED")

    def test_04_add_and_remove_paper(self):
        """Test assigning paper to project and removing paper."""
        p = ResearchProjectService.create_project(self.db, ResearchProjectCreate(name="Project Paper Test"))
        assoc = ResearchProjectService.add_paper_to_project(self.db, p.id, self.sample_paper.id)

        self.assertEqual(assoc.project_id, p.id)
        self.assertEqual(assoc.paper_id, self.sample_paper.id)

        # Duplicate assignment prevention
        with self.assertRaises(Exception):
            ResearchProjectService.add_paper_to_project(self.db, p.id, self.sample_paper.id)

        # Remove paper
        ResearchProjectService.remove_paper_from_project(self.db, p.id, self.sample_paper.id)
        papers = ResearchProjectService.get_project_papers(self.db, p.id)
        self.assertEqual(len(papers), 0)

        # Paper record must still exist
        paper_still_exists = self.db.query(ResearchPaper).filter(ResearchPaper.id == self.sample_paper.id).first()
        self.assertIsNotNone(paper_still_exists)

    def test_05_delete_project_preserves_papers(self):
        """Test project deletion removes project but DOES NOT delete research papers."""
        p = ResearchProjectService.create_project(self.db, ResearchProjectCreate(name="Project Delete Test"))
        ResearchProjectService.add_paper_to_project(self.db, p.id, self.sample_paper.id)

        ResearchProjectService.delete_project(self.db, p.id)

        # Paper must still exist in DB
        paper_still_exists = self.db.query(ResearchPaper).filter(ResearchPaper.id == self.sample_paper.id).first()
        self.assertIsNotNone(paper_still_exists)


if __name__ == "__main__":
    unittest.main()
