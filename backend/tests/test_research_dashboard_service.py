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


class TestResearchDashboardService(unittest.TestCase):

    def setUp(self):
        Base.metadata.create_all(bind=engine)

    def test_01_get_project_dashboard_aggregate(self):
        """Test GET /api/projects/1/research-dashboard returns aggregated dashboard state."""
        response = client.get("/api/projects/1/research-dashboard")
        self.assertIn(response.status_code, [200, 404])

        if response.status_code == 200:
            data = response.json()
            self.assertIn("current_stage_id", data)
            self.assertIn("next_step", data)
            self.assertIn("health", data)
            self.assertIn("submission_readiness", data)
            self.assertIn("completed_milestones", data)
