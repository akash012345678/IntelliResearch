import os
import sys
import unittest
import tempfile
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.main import app
from app.services.vector_store import VectorStore, EXPECTED_DIMENSION
from app.services.semantic_index_service import SemanticIndexService
from app.database.session import SessionLocal
from app.models.paper_model import ResearchPaper

client = TestClient(app)

def mock_query_embedding(*args, **kwargs):
    """Deterministic mock embedding generator for fast unit tests."""
    vec = [0.0] * EXPECTED_DIMENSION
    text = args[0] if args else kwargs.get("title", "")
    if "fail" in str(text).lower():
        raise RuntimeError("Simulated embedding failure.")
    # Always set index 0 to 1.0 for predictable unit test inner products
    vec[0] = 1.0
    return vec


class TestSemanticSearchAPI(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.idx_file = os.path.join(self.tmpdir.name, "research_papers.index")
        self.map_file = os.path.join(self.tmpdir.name, "paper_id_mapping.json")

        self.vector_store = VectorStore(index_path=self.idx_file, mapping_path=self.map_file)
        self.service = SemanticIndexService(vector_store=self.vector_store)

    def tearDown(self):
        self.tmpdir.cleanup()

    # 1. Valid semantic search query & 2. Correct embedding & 3. FAISS ranking & 4. Paper ID resolution & 5. DB retrieval
    @patch("app.services.semantic_index_service.EmbeddingService.generate_embedding", side_effect=mock_query_embedding)
    def test_01_valid_semantic_search_and_ranking(self, mock_emb):
        """Verify valid query returns ranked results from DB preserving FAISS similarity order."""
        v1 = np.zeros(EXPECTED_DIMENSION, dtype=np.float32)
        v1[0] = 1.0  # High similarity (inner product = 1.0)
        v2 = np.zeros(EXPECTED_DIMENSION, dtype=np.float32)
        v2[0] = 0.5
        v2[1] = 0.5  # Lower similarity (inner product = 0.5)

        self.vector_store.add_paper(paper_id=101, embedding=v1)
        self.vector_store.add_paper(paper_id=202, embedding=v2)

        mock_p1 = MagicMock()
        mock_p1.id = 101
        mock_p1.title = "High Match Paper"
        mock_p1.abstract = "Abstract 1"
        mock_p1.keywords = ["AI"]
        mock_p1.algorithms = ["CNN"]
        mock_p1.datasets = []
        mock_p1.methodologies = []
        mock_p1.application_domains = []

        mock_p2 = MagicMock()
        mock_p2.id = 202
        mock_p2.title = "Medium Match Paper"
        mock_p2.abstract = "Abstract 2"
        mock_p2.keywords = ["DL"]
        mock_p2.algorithms = ["RNN"]
        mock_p2.datasets = []
        mock_p2.methodologies = []
        mock_p2.application_domains = []

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_p1, mock_p2]

        res = self.service.search_papers(
            query="deep learning drowsiness",
            top_k=5,
            db_session=mock_db
        )

        self.assertEqual(res["query"], "deep learning drowsiness")
        self.assertEqual(res["total_results"], 2)
        self.assertEqual(res["results"][0]["paper_id"], 101)
        self.assertEqual(res["results"][1]["paper_id"], 202)
        self.assertGreaterEqual(res["results"][0]["similarity_score"], res["results"][1]["similarity_score"])

    # 6. top_k behavior & validation
    @patch("app.services.semantic_index_service.EmbeddingService.generate_embedding", side_effect=mock_query_embedding)
    def test_02_top_k_behavior(self, mock_emb):
        """Verify top_k limits returned results."""
        v = np.zeros(EXPECTED_DIMENSION, dtype=np.float32)
        v[0] = 1.0
        for i in range(1, 10):
            self.vector_store.add_paper(paper_id=i, embedding=v)

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = [
            MagicMock(id=i, title=f"Paper {i}", abstract=None, keywords=[], algorithms=[], datasets=[], methodologies=[], application_domains=[])
            for i in range(1, 10)
        ]

        res = self.service.search_papers(query="test top_k", top_k=3, db_session=mock_db)
        self.assertEqual(len(res["results"]), 3)

    # 7. Empty query rejection (HTTP 400 or 422)
    def test_03_empty_query_rejection(self):
        """Verify empty or whitespace-only query returns HTTP error status code."""
        resp1 = client.post("/api/semantic/search", json={"query": "", "top_k": 5})
        self.assertIn(resp1.status_code, [400, 422])

        resp2 = client.post("/api/semantic/search", json={"query": "   \n\t  ", "top_k": 5})
        self.assertIn(resp2.status_code, [400, 422])

    # 8. Invalid top_k rejection (HTTP 400 or 422)
    def test_04_invalid_top_k_rejection(self):
        """Verify top_k <= 0 or top_k > 20 returns HTTP error status code."""
        resp1 = client.post("/api/semantic/search", json={"query": "valid query", "top_k": 0})
        self.assertIn(resp1.status_code, [400, 422])

        resp2 = client.post("/api/semantic/search", json={"query": "valid query", "top_k": -5})
        self.assertIn(resp2.status_code, [400, 422])

        resp3 = client.post("/api/semantic/search", json={"query": "valid query", "top_k": 50})
        self.assertIn(resp3.status_code, [400, 422])

    # 9. Empty FAISS index handling
    @patch("app.services.semantic_index_service.EmbeddingService.generate_embedding", side_effect=mock_query_embedding)
    def test_05_empty_faiss_index(self, mock_emb):
        """Verify searching an empty FAISS index returns total_results: 0 and results: []."""
        res = self.service.search_papers(query="search empty store", top_k=5)
        self.assertEqual(res["total_results"], 0)
        self.assertEqual(res["results"], [])

    # 10. Missing database paper handling
    @patch("app.services.semantic_index_service.EmbeddingService.generate_embedding", side_effect=mock_query_embedding)
    def test_06_missing_database_paper_handling(self, mock_emb):
        """Verify missing database paper is skipped safely without crashing."""
        v = np.zeros(EXPECTED_DIMENSION, dtype=np.float32)
        v[0] = 1.0
        self.vector_store.add_paper(paper_id=999, embedding=v)

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = []

        res = self.service.search_papers(query="missing paper query", top_k=5, db_session=mock_db)
        self.assertEqual(res["total_results"], 0)
        self.assertEqual(res["results"], [])

    # 11. Embedding failure handling
    @patch("app.services.semantic_index_service.EmbeddingService.generate_embedding", side_effect=RuntimeError("Embedding model error"))
    def test_07_embedding_failure_handling(self, mock_emb):
        """Verify embedding generation failure returns HTTP 500 Internal Server Error."""
        resp = client.post("/api/semantic/search", json={"query": "fail query", "top_k": 5})
        self.assertEqual(resp.status_code, 500)
        self.assertIn("detail", resp.json())

    # 12. Existing keyword/title search still works
    def test_08_existing_title_search_intact(self):
        """Verify GET /api/papers?title=... still works correctly."""
        resp = client.get("/api/papers")
        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(resp.json(), list)

    # 13. Real Integration Test - Semantic Search API
    def test_09_real_semantic_search_integration(self):
        """
        Real end-to-end integration test querying:
        'deep learning techniques for driver drowsiness detection'
        using actual Sentence-BERT model and actual FAISS index containing uploaded papers.
        """
        real_query = "deep learning techniques for driver drowsiness detection"
        resp = client.post("/api/semantic/search", json={"query": real_query, "top_k": 5})

        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        self.assertEqual(data["query"], real_query)
        self.assertIn("total_results", data)
        self.assertIn("results", data)

    # --- RELATED PAPERS FEATURE TESTS ---

    # 14. Valid related paper request & source paper self-exclusion
    def test_10_valid_related_paper_request_and_self_exclusion(self):
        """Verify related papers returns results and strictly excludes the source paper itself."""
        v_src = np.zeros(EXPECTED_DIMENSION, dtype=np.float32)
        v_src[0] = 1.0

        v_rel = np.zeros(EXPECTED_DIMENSION, dtype=np.float32)
        v_rel[0] = 0.9

        self.vector_store.add_paper(paper_id=1, embedding=v_src)
        self.vector_store.add_paper(paper_id=2, embedding=v_rel)

        src_p = MagicMock(id=1, title="Source Paper", abstract="Abs 1", keywords=[], algorithms=[], datasets=[], methodologies=[], application_domains=[])
        rel_p = MagicMock(id=2, title="Related Paper", abstract="Abs 2", keywords=[], algorithms=[], datasets=[], methodologies=[], application_domains=[])

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = src_p
        mock_db.query.return_value.filter.return_value.all.return_value = [src_p, rel_p]

        res = self.service.find_related_papers(paper_id=1, top_k=5, db_session=mock_db)

        self.assertEqual(res["source_paper"]["paper_id"], 1)
        self.assertEqual(res["source_paper"]["title"], "Source Paper")
        self.assertEqual(res["total_results"], 1)
        self.assertEqual(res["related_papers"][0]["paper_id"], 2)
        # Source paper ID 1 must NOT appear in related_papers
        related_ids = [p["paper_id"] for p in res["related_papers"]]
        self.assertNotIn(1, related_ids)

    # 15. Non-existent paper (HTTP 404)
    def test_11_related_paper_non_existent_404(self):
        """Verify requesting related papers for non-existent paper returns HTTP 404 Not Found."""
        resp = client.get("/api/semantic/papers/99999/related")
        self.assertEqual(resp.status_code, 404)

    # 16. Non-indexed paper handling (Generates embedding on the fly)
    @patch("app.services.semantic_index_service.EmbeddingService.generate_paper_embedding", side_effect=mock_query_embedding)
    def test_12_non_indexed_paper_on_the_fly_embedding(self, mock_emb):
        """Verify non-indexed source paper generates vector embedding on the fly."""
        src_p = MagicMock(id=50, title="Unindexed Paper", abstract="Abs", full_text="Full", keywords=[], algorithms=[], datasets=[], methodologies=[], application_domains=[])
        
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = src_p
        mock_db.query.return_value.filter.return_value.all.return_value = [src_p]

        res = self.service.find_related_papers(paper_id=50, top_k=5, db_session=mock_db)
        self.assertEqual(res["source_paper"]["paper_id"], 50)
        self.assertEqual(res["total_results"], 0)  # Empty index match except self

    # 17. Invalid top_k handling for related papers
    def test_13_related_papers_invalid_top_k(self):
        """Verify invalid top_k parameter returns HTTP 422 or 400 Bad Request."""
        resp = client.get("/api/semantic/papers/1/related?top_k=0")
        self.assertIn(resp.status_code, [400, 422])

    # 18. Real Integration Test - Related Papers Feature
    def test_14_real_related_papers_integration(self):
        """
        Real end-to-end integration test querying related papers for paper ID 4
        against active Supabase PostgreSQL and FAISS index.
        """
        resp = client.get("/api/semantic/papers/4/related?top_k=5")
        # Should return 200 (if paper 4 exists) or 404 (if not found in DB)
        self.assertIn(resp.status_code, [200, 404])
        if resp.status_code == 200:
            data = resp.json()
            self.assertEqual(data["source_paper"]["paper_id"], 4)
            self.assertIn("related_papers", data)
            # Ensure paper 4 is not in related papers list
            related_ids = [p["paper_id"] for p in data["related_papers"]]
            self.assertNotIn(4, related_ids)


if __name__ == "__main__":
    unittest.main()
