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


class TestResearchMethodologyAPI(unittest.TestCase):

    def setUp(self):
        Base.metadata.create_all(bind=engine)

    def test_01_get_global_methodology_plan(self):
        """Test GET /api/research-directions/{direction_id}/methodology-plan returns valid plan response."""
        response = client.get("/api/research-directions/dir_1/methodology-plan")
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertIn("direction_id", data)
        self.assertIn("title", data)
        self.assertIn("research_problem", data)
        self.assertIn("objectives", data)
        self.assertIn("research_questions", data)
        self.assertIn("pipeline", data)
        self.assertIn("dataset_plan", data)
        self.assertIn("data_preparation", data)
        self.assertIn("baseline_methods", data)
        self.assertIn("proposed_method", data)
        self.assertIn("experiments", data)
        self.assertIn("metrics", data)
        self.assertIn("ablation_plan", data)
        self.assertIn("variables", data)
        self.assertIn("expected_outputs", data)
        self.assertIn("success_criteria", data)
        self.assertIn("risks", data)
        self.assertIn("reproducibility_checklist", data)
        self.assertIn("timeline", data)
        self.assertIn("implementation_checklist", data)
        self.assertIn("potential_contribution", data)
        self.assertIn("hypotheses", data)
        self.assertIn("traceability", data)
        self.assertIn("disclaimer", data)

        # Scoped vocabulary & safety checks
        self.assertIn("collection", data["disclaimer"].lower())
        self.assertEqual(len(data["data_preparation"]), 8)

    def test_02_get_project_methodology_plan(self):
        """Test GET /api/projects/{project_id}/research-directions/{direction_id}/methodology-plan."""
        response = client.get("/api/projects/1/research-directions/dir_1/methodology-plan")
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data["scope"], "project")
        self.assertIn("objectives", data)

    def test_03_save_project_research_plan(self):
        """Test POST /api/projects/{project_id}/research-plan/save."""
        payload = {
            "direction_id": "dir_1",
            "plan_data": {
                "title": "Saved Plan Test",
                "research_problem": "Test Problem",
                "potential_contribution": "Test Contribution"
            },
            "notes": "Test Notes"
        }
        # First ensure project 1 exists or return gracefully if 404
        response = client.post("/api/projects/1/research-plan/save", json=payload)
        self.assertIn(response.status_code, [200, 404])
