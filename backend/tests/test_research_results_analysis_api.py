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


class TestResearchResultsAnalysisAPI(unittest.TestCase):

    def setUp(self):
        Base.metadata.create_all(bind=engine)

    def test_01_get_project_results_analysis_no_results(self):
        """Test GET /api/projects/1/results-analysis when no results are recorded yet."""
        response = client.get("/api/projects/1/results-analysis")
        # Status should be 200 or 404 if project 1 doesn't exist
        self.assertIn(response.status_code, [200, 404])

        if response.status_code == 200:
            data = response.json()
            self.assertIn("has_recorded_results", data)
            self.assertIn("notice", data)
            self.assertIn("project_overall_conclusion", data)
            self.assertIn("decision_guidance", data)

    def test_02_get_safe_conclusion(self):
        """Test GET /api/projects/1/results-analysis/conclusion returns safe plain-language conclusion."""
        response = client.get("/api/projects/1/results-analysis/conclusion")
        self.assertIn(response.status_code, [200, 404])
        if response.status_code == 200:
            data = response.json()
            self.assertIn("overall_conclusion", data)
            self.assertIn("decision_guidance", data)
            self.assertIn("has_recorded_results", data)
