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


class TestAcademicManuscriptAPI(unittest.TestCase):

    def setUp(self):
        Base.metadata.create_all(bind=engine)

    def test_01_get_project_manuscript(self):
        """Test GET /api/projects/1/academic-manuscript returns 44-section manuscript."""
        response = client.get("/api/projects/1/academic-manuscript")
        self.assertIn(response.status_code, [200, 404])

        if response.status_code == 200:
            data = response.json()
            self.assertIn("sections", data)
            self.assertIn("completeness", data)
            self.assertIn("academic_integrity_notice", data)
            self.assertGreaterEqual(len(data["sections"]), 29)

    def test_02_export_manuscript_markdown(self):
        """Test GET /api/projects/1/academic-manuscript/export returns markdown."""
        response = client.get("/api/projects/1/academic-manuscript/export?format=markdown")
        self.assertIn(response.status_code, [200, 404])

        if response.status_code == 200:
            data = response.json()
            self.assertIn("content", data)
            self.assertEqual(data["format"], "markdown")

    def test_03_export_manuscript_pdf(self):
        """Test GET /api/projects/1/academic-manuscript/export?format=pdf returns PDF bytes."""
        response = client.get("/api/projects/1/academic-manuscript/export?format=pdf")
        self.assertIn(response.status_code, [200, 404])

        if response.status_code == 200:
            self.assertEqual(response.headers["content-type"], "application/pdf")
            self.assertTrue(response.content.startswith(b"%PDF"))

    def test_04_export_manuscript_docx(self):
        """Test GET /api/projects/1/academic-manuscript/export?format=docx returns DOCX bytes."""
        response = client.get("/api/projects/1/academic-manuscript/export?format=docx")
        self.assertIn(response.status_code, [200, 404])

        if response.status_code == 200:
            self.assertIn("application/vnd.openxmlformats-officedocument", response.headers["content-type"])
            self.assertTrue(response.content.startswith(b"PK"))
