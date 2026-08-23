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


class TestOpportunityValidationAPI(unittest.TestCase):

    def setUp(self):
        Base.metadata.create_all(bind=engine)

    def test_01_validate_global_opportunity(self):
        """Test GET /api/research-directions/{direction_id}/validate returns valid response."""
        response = client.get("/api/research-directions/dir_1/validate")
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertIn("direction_id", data)
        self.assertIn("validation_status", data)
        self.assertIn("collection_summary", data)
        self.assertIn("core_assumption", data)
        self.assertIn("suggested_search_queries", data)
        self.assertIn("validation_checklist", data)
        self.assertIn("external_validation", data)
        self.assertIn("refinement_areas", data)
        self.assertIn("invalidation_conditions", data)
        self.assertIn("validation_summary_text", data)
        self.assertIn("recommended_action", data)
        self.assertIn("disclaimer", data)

        # Verify 5 search queries generated
        self.assertEqual(len(data["suggested_search_queries"]), 5)

        # Scoped vocabulary assertions
        self.assertIn("collection", data["disclaimer"].lower())

    def test_02_validate_project_opportunity(self):
        """Test GET /api/projects/{project_id}/research-directions/{direction_id}/validate."""
        response = client.get("/api/projects/1/research-directions/dir_1/validate")
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data["scope"], "project")
        self.assertIn("collection_summary", data)

    def test_03_literature_search_runner(self):
        """Test POST /api/research-directions/literature-search returns search results."""
        payload = {"query": "driver drowsiness detection Vision Transformer", "top_k": 3}
        response = client.post("/api/research-directions/literature-search", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data["query"], payload["query"])
        self.assertIn("results", data)
        self.assertIn("provider", data)
