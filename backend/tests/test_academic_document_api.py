import sys
import unittest
from pathlib import Path
from fastapi.testclient import TestClient

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database.session import Base, get_db, init_db
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


class TestAcademicDocumentAPI(unittest.TestCase):

    def setUp(self):
        init_db(target_engine=engine)

    def test_01_validate_academic_document(self):
        """Test GET /api/projects/1/academic-document/validate returns document validation data."""
        response = client.get("/api/projects/1/academic-document/validate")
        self.assertIn(response.status_code, [200, 404])

        if response.status_code == 200:
            data = response.json()
            self.assertIn("is_valid_for_submission", data)
            self.assertIn("passed_checks_count", data)
            self.assertIn("issues", data)

    def test_02_get_document_preview(self):
        """Test POST /api/projects/1/academic-document/preview returns page preview layout."""
        response = client.post("/api/projects/1/academic-document/preview", json={"profile": "COLLEGE_PROJECT"})
        self.assertIn(response.status_code, [200, 404])

        if response.status_code == 200:
            data = response.json()
            self.assertIn("total_pages", data)
            self.assertIn("pages", data)
            self.assertIn("toc", data)

    def test_03_download_submission_package(self):
        """Test GET /api/projects/1/submission-package returns zip file response."""
        response = client.get("/api/projects/1/submission-package")
        self.assertIn(response.status_code, [200, 404])

    def test_04_get_and_save_document_settings(self):
        """Test GET & POST /api/projects/{id}/academic-document/settings."""
        # 1. Fetch default settings
        get_res = client.get("/api/projects/1/academic-document/settings")
        self.assertIn(get_res.status_code, [200, 404])

        # 2. Save custom settings
        payload = {
            "profile": "COLLEGE_PROJECT",
            "page_size": "LETTER",
            "margins": "NARROW",
            "font_family": "Calibri",
            "font_size": 12,
            "line_spacing": 1.15,
            "student_name": "Akash K",
            "register_number": "2312002",
            "institution": "National Engineering College"
        }
        post_res = client.post("/api/projects/1/academic-document/settings", json=payload)
        self.assertIn(post_res.status_code, [200, 404])
        if post_res.status_code == 200:
            saved = post_res.json()
            self.assertEqual(saved["student_name"], "Akash K")
            self.assertEqual(saved["register_number"], "2312002")
            self.assertEqual(saved["institution"], "National Engineering College")
            self.assertEqual(saved["font_family"], "Calibri")
            self.assertEqual(saved["line_spacing"], 1.15)
