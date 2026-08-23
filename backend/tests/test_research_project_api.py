import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.main import app

client = TestClient(app)


class TestResearchProjectAPI(unittest.TestCase):
    """
    API Integration tests for Research Projects and Project-Paper association endpoints.
    """

    @patch("app.api.research_project_api.ResearchProjectService")
    def test_01_create_project_api(self, mock_service):
        mock_service.create_project.return_value = {
            "id": 1,
            "name": "Test Project",
            "description": "Test Desc",
            "status": "ACTIVE",
            "created_at": "2026-08-23T00:00:00Z",
            "updated_at": "2026-08-23T00:00:00Z",
            "paper_count": 0,
            "direction_count": 0,
            "proposal_count": 0
        }

        response = client.post("/api/projects", json={"name": "Test Project", "description": "Test Desc"})
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["name"], "Test Project")

    @patch("app.api.research_project_api.ResearchProjectService")
    def test_02_list_projects_api(self, mock_service):
        mock_service.list_projects.return_value = []
        response = client.get("/api/projects")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)


    @patch("app.api.research_project_api.ResearchProjectService")
    def test_03_add_paper_to_project_api(self, mock_service):
        mock_service.add_paper_to_project.return_value = {
            "project_id": 1,
            "paper_id": 10,
            "title": "Paper 10",
            "filename": "paper10.pdf",
            "added_at": "2026-08-23T00:00:00Z"
        }

        response = client.post("/api/projects/1/papers/10")
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["paper_id"], 10)


if __name__ == "__main__":
    unittest.main()
