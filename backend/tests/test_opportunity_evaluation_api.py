import sys
import unittest
from pathlib import Path
from fastapi.testclient import TestClient

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database.session import Base, get_db
from app.main import app

SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test_fixture.db"
engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


class TestOpportunityEvaluationAPI(unittest.TestCase):

    def setUp(self):
        Base.metadata.create_all(bind=engine)

    def test_01_evaluate_global_opportunity(self):
        """Test GET /api/research-directions/{direction_id}/evaluate returns valid evaluation response."""
        response = client.get("/api/research-directions/dir_1/evaluate")
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertIn("opportunity_id", data)
        self.assertIn("research_problem", data)
        self.assertIn("what_current_research_does", data)
        self.assertIn("what_is_missing", data)
        self.assertIn("why_relevant", data)
        self.assertIn("evidence", data)
        self.assertIn("implementation_preview", data)
        self.assertIn("candidate_algorithms", data)
        self.assertIn("candidate_datasets", data)
        self.assertIn("dataset_considerations", data)
        self.assertIn("experiment_plan", data)
        self.assertIn("possible_contribution", data)
        self.assertIn("limitations", data)
        self.assertIn("scorecard", data)
        self.assertIn("why_consider_this", data)
        self.assertIn("validation_checklist", data)
        self.assertIn("disclaimer", data)

        # Scoped vocabulary checks
        self.assertIn("collection", data["disclaimer"].lower())
        self.assertIn("collection", data["what_is_missing"].lower())

    def test_02_evaluate_project_opportunity(self):
        """Test GET /api/projects/{project_id}/research-directions/{direction_id}/evaluate returns project-scoped response."""
        response = client.get("/api/projects/1/research-directions/dir_1/evaluate")
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertIn("opportunity_id", data)
        self.assertIn("scorecard", data)
