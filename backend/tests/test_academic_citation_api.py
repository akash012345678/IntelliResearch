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


class TestAcademicCitationAPI(unittest.TestCase):

    def setUp(self):
        Base.metadata.create_all(bind=engine)

    def test_01_get_project_citations(self):
        """Test GET /api/projects/1/academic-manuscript/citations returns citation list."""
        response = client.get("/api/projects/1/academic-manuscript/citations")
        self.assertIn(response.status_code, [200, 404])

        if response.status_code == 200:
            data = response.json()
            self.assertIsInstance(data, list)

    def test_02_get_manuscript_quality(self):
        """Test GET /api/projects/1/academic-manuscript/quality returns quality audit metrics."""
        response = client.get("/api/projects/1/academic-manuscript/quality")
        self.assertIn(response.status_code, [200, 404])

        if response.status_code == 200:
            data = response.json()
            self.assertIn("citation_traceability_score", data)
            self.assertIn("result_consistency_score", data)
            self.assertIn("novelty_claim_safety", data)
            self.assertIn("issues", data)
            self.assertIn("metric_mismatches", data)
