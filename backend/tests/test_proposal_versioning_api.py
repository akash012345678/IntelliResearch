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


class TestProposalVersioningAPI(unittest.TestCase):
    """
    API Integration tests for Proposal editing, diff comparison, and restoration endpoints.
    """

    @patch("app.api.proposal_api.ProposalPersistenceService")
    def test_01_patch_edit_proposal_api(self, mock_service):
        mock_service.edit_proposal.return_value = {
            "id": 2,
            "proposal_id": 1,
            "version_number": 2,
            "proposal_data": {"abstract": "V2 Abstract"},
            "generation_mode": "manual",
            "change_summary": "Updated abstract",
            "is_restored": False,
            "created_at": "2026-08-23T00:00:00Z",
            "updated_at": "2026-08-23T00:00:00Z"
        }

        payload = {
            "abstract": "V2 Abstract",
            "change_summary": "Updated abstract"
        }

        response = client.patch("/api/proposals/1", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["version_number"], 2)
        self.assertEqual(data["generation_mode"], "manual")

    @patch("app.api.proposal_api.ProposalPersistenceService")
    def test_02_compare_proposal_versions_api(self, mock_service):
        mock_service.compare_versions.return_value = {
            "proposal_id": 1,
            "version_a": 1,
            "version_b": 2,
            "total_changes": 1,
            "changes": [
                {
                    "section": "abstract",
                    "changed": True,
                    "before": "V1 Abstract",
                    "after": "V2 Abstract"
                }
            ]
        }

        response = client.get("/api/proposals/1/compare?version_a=1&version_b=2")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["total_changes"], 1)

    @patch("app.api.proposal_api.ProposalPersistenceService")
    def test_03_restore_proposal_version_api(self, mock_service):
        mock_service.restore_version.return_value = {
            "id": 3,
            "proposal_id": 1,
            "version_number": 3,
            "proposal_data": {"abstract": "V1 Abstract"},
            "generation_mode": "restored",
            "change_summary": "Restored from version 1",
            "is_restored": True,
            "created_at": "2026-08-23T00:00:00Z",
            "updated_at": "2026-08-23T00:00:00Z"
        }

        response = client.post("/api/proposals/1/restore/1")
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["version_number"], 3)
        self.assertTrue(data["is_restored"])


if __name__ == "__main__":
    unittest.main()
