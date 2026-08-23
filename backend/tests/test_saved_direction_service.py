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
from app.schemas.project_schema import ResearchProjectCreate, SavedDirectionCreate
from app.services.research_project_service import ResearchProjectService
from app.services.saved_direction_service import SavedDirectionService


class TestSavedDirectionService(unittest.TestCase):
    """
    Unit tests for SavedDirectionService direction snapshot persistence.
    """

    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(cls.engine)
        cls.SessionLocal = sessionmaker(bind=cls.engine)

    def setUp(self):
        self.db = self.SessionLocal()
        self.project = ResearchProjectService.create_project(self.db, ResearchProjectCreate(name="Direction Test Project"))

    def tearDown(self):
        self.db.rollback()
        for table in reversed(Base.metadata.sorted_tables):
            self.db.execute(table.delete())
        self.db.commit()
        self.db.close()

    def test_01_save_and_get_direction(self):
        """Test saving and retrieving an immutable direction snapshot."""
        create_data = SavedDirectionCreate(
            project_id=self.project.id,
            source_direction_id="dir_1",
            title="Explore YOLOv8 + Transformer",
            description="Proposed exploration",
            confidence="High",
            direction_data={"title": "Explore YOLOv8 + Transformer", "score": 0.88}
        )

        saved = SavedDirectionService.save_direction(self.db, create_data)
        self.assertIsNotNone(saved.id)
        self.assertEqual(saved.title, "Explore YOLOv8 + Transformer")
        self.assertEqual(saved.direction_data["score"], 0.88)

        fetched = SavedDirectionService.get_saved_direction(self.db, saved.id)
        self.assertEqual(fetched.id, saved.id)

    def test_02_list_and_delete_direction(self):
        """Test listing directions for a project and deleting a direction."""
        SavedDirectionService.save_direction(self.db, SavedDirectionCreate(
            project_id=self.project.id,
            source_direction_id="dir_1",
            title="Direction 1",
            direction_data={"d": 1}
        ))
        d2 = SavedDirectionService.save_direction(self.db, SavedDirectionCreate(
            project_id=self.project.id,
            source_direction_id="dir_2",
            title="Direction 2",
            direction_data={"d": 2}
        ))

        directions = SavedDirectionService.list_project_directions(self.db, self.project.id)
        self.assertEqual(len(directions), 2)

        SavedDirectionService.delete_saved_direction(self.db, d2.id)
        directions_after = SavedDirectionService.list_project_directions(self.db, self.project.id)
        self.assertEqual(len(directions_after), 1)


if __name__ == "__main__":
    unittest.main()
