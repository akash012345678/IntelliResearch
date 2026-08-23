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


class TestProposalAPI(unittest.TestCase):
    """
    API Integration tests for Proposal Persistence and Versioning endpoints.
    """

    @patch("app.api.proposal_api.ProposalPersistenceService")
    def test_01_create_proposal_api(self, mock_service):
        mock_service.create_proposal.return_value = {
            "id": 1,
            "proposal_uuid": "prop_123",
            "project_id": 1,
            "source_direction_id": "dir_1",
            "title": "Saved Proposal",
            "status": "DRAFT",
            "current_version": {
                "id": 1,
                "proposal_id": 1,
                "version_number": 1,
                "proposal_data": {"abstract": "V1 Abstract"},
                "generation_mode": "template",
                "created_at": "2026-08-23T00:00:00Z",
                "updated_at": "2026-08-23T00:00:00Z"
            },
            "created_at": "2026-08-23T00:00:00Z",
            "updated_at": "2026-08-23T00:00:00Z"
        }

        payload = {
            "project_id": 1,
            "source_direction_id": "dir_1",
            "title": "Saved Proposal",
            "proposal_data": {"abstract": "V1 Abstract"},
            "generation_mode": "template"
        }

        response = client.post("/api/proposals", json=payload)
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["proposal_uuid"], "prop_123")
        self.assertEqual(data["current_version"]["version_number"], 1)

    @patch("app.api.proposal_api.ProposalPersistenceService")
    def test_02_get_proposal_versions_api(self, mock_service):
        mock_service.get_proposal_versions.return_value = {
            "proposal_id": 1,
            "total_versions": 1,
            "versions": [
                {
                    "id": 1,
                    "proposal_id": 1,
                    "version_number": 1,
                    "proposal_data": {"abstract": "V1 Abstract"},
                    "generation_mode": "template",
                    "created_at": "2026-08-23T00:00:00Z",
                    "updated_at": "2026-08-23T00:00:00Z"
                }
            ]
        }

        response = client.get("/api/proposals/1/versions")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["total_versions"], 1)


if __name__ == "__main__":
    unittest.main()
