import sys
import unittest
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.main import app

client = TestClient(app)


class TestProjectIntelligenceAPI(unittest.TestCase):
    """
    API Integration tests for Project Research Intelligence endpoint.
    """

    @patch("app.api.project_intelligence_api.ProjectIntelligenceService")
    def test_01_get_project_research_intelligence_api(self, mock_service):
        mock_service.analyze_project.return_value = {
            "project": {"id": 1, "name": "Test Proj", "description": "Desc", "status": "ACTIVE"},
            "collection_summary": {
                "total_papers": 2, "total_nodes": 10, "total_edges": 12,
                "total_keywords": 4, "total_algorithms": 2, "total_datasets": 1,
                "total_methodologies": 1, "total_domains": 1
            },
            "paper_landscape": [],
            "shared_concepts": {"keywords": [], "algorithms": [], "datasets": [], "methodologies": [], "domains": []},
            "paper_relationships": [],
            "research_gaps": [],
            "underrepresented_concepts": [],
            "candidate_research_directions": [],
            "proposal_traceability": [],
            "insight_summary": "Test synthesis summary"
        }

        response = client.get("/api/projects/1/research-intelligence")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["collection_summary"]["total_papers"], 2)
        self.assertEqual(data["project"]["id"], 1)


if __name__ == "__main__":
    unittest.main()
