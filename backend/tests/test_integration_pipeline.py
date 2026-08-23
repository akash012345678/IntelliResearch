import os
import sys
import unittest
import io
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


def mock_sbert_embedding(title, abstract=None, full_text=None, keywords=None, metadata=None):
    """Deterministic mock embedding for fast unit tests."""
    vec = [0.0] * EXPECTED_DIMENSION
    vec[0] = 1.0
    return vec


MINIMAL_PDF_BYTES = (
    b"%PDF-1.4\n"
    b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    b"2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj\n"
    b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<<>>>>endobj\n"
    b"xref\n"
    b"0 4\n"
    b"0000000000 65535 f \n"
    b"0000000009 00000 n \n"
    b"0000000052 00000 n \n"
    b"00000000101 00000 n \n"
    b"trailer<</Size 4/Root 1 0 R>>\n"
    b"startxref\n"
    b"178\n"
    b"%%EOF\n"
)


class TestIntegrationPipeline(unittest.TestCase):

    def setUp(self):
        Base.metadata.create_all(bind=engine)
        self.vector_store = VectorStore()
        if self.vector_store.index_path.exists():
            try:
                self.vector_store.index_path.unlink()
            except Exception:
                pass
        if self.vector_store.mapping_path.exists():
            try:
                self.vector_store.mapping_path.unlink()
            except Exception:
                pass
        self.vector_store = VectorStore()

    @patch("app.services.semantic_index_service.EmbeddingService.generate_paper_embedding", side_effect=mock_sbert_embedding)
    def test_01_upload_and_semantic_index_pipeline(self, mock_emb):
        """Test Upload PDF -> DB Record -> SBERT Embedding -> FAISS Vector Indexing."""
        file_data = io.BytesIO(MINIMAL_PDF_BYTES)

        response = client.post(
            "/api/upload",
            files={"file": ("test_integration_paper.pdf", file_data, "application/pdf")}
        )

        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertIn("paper_id", data)
        self.assertEqual(data["database_status"], "success")
        self.assertEqual(data["semantic_index_status"], "indexed")

        paper_id = data["paper_id"]
        
        # Verify FAISS vector store contains paper_id
        if self.vector_store.index_path.exists() and self.vector_store.mapping_path.exists():
            self.vector_store.load_index()
        self.assertTrue(self.vector_store.contains_paper(paper_id))
        self.assertIsNotNone(self.vector_store.get_vector_position(paper_id))

        # Cleanup created paper
        del_resp = client.delete(f"/api/paper/{paper_id}")
        self.assertEqual(del_resp.status_code, 200)
        if self.vector_store.index_path.exists() and self.vector_store.mapping_path.exists():
            self.vector_store.load_index()
        self.assertFalse(self.vector_store.contains_paper(paper_id))

    @patch("app.services.semantic_index_service.SemanticIndexService.index_paper", side_effect=RuntimeError("Simulated FAISS error"))
    def test_02_db_success_faiss_failure_isolation(self, mock_index):
        """Test DB save succeeds when SBERT/FAISS fails, returning semantic_index_status: failed."""
        file_data = io.BytesIO(MINIMAL_PDF_BYTES)

        response = client.post(
            "/api/upload",
            files={"file": ("test_fail_paper.pdf", file_data, "application/pdf")}
        )

        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["database_status"], "success")
        self.assertEqual(data["semantic_index_status"], "failed")

        paper_id = data["paper_id"]
        # Verify paper exists in DB (retrievable via API)
        get_resp = client.get(f"/api/paper/{paper_id}")
        self.assertEqual(get_resp.status_code, 200)

        # Cleanup
        client.delete(f"/api/paper/{paper_id}")

    @patch("app.services.semantic_index_service.EmbeddingService.generate_paper_embedding", side_effect=mock_sbert_embedding)
    def test_03_admin_reindex_endpoint(self, mock_emb):
        """Test administrative POST /api/semantic/reindex endpoint."""
        response = client.post("/api/semantic/reindex")
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertIn("total", data)
        self.assertIn("indexed", data)
        self.assertIn("failed", data)
        self.assertIn("failed_paper_ids", data)

    def test_04_real_pdf_end_to_end_pipeline(self):
        """
        Real end-to-end integration test using actual research PDF:
        PDF -> Supabase DB -> SBERT -> FAISS Vector Store.
        """
        real_pdf_path = Path(__file__).resolve().parent.parent / "app" / "uploads" / "original_papers" / "PD-Final Report.pdf"
        if not real_pdf_path.exists():
            self.skipTest("Real test PDF PD-Final Report.pdf not found.")

        with open(real_pdf_path, "rb") as f:
            response = client.post(
                "/api/upload",
                files={"file": ("PD-Final Report.pdf", f, "application/pdf")}
            )

        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["database_status"], "success")
        self.assertEqual(data["semantic_index_status"], "indexed")

        paper_id = data["paper_id"]
        if self.vector_store.index_path.exists() and self.vector_store.mapping_path.exists():
            self.vector_store.load_index()
        self.assertTrue(self.vector_store.contains_paper(paper_id))

        # Cleanup test paper
        client.delete(f"/api/paper/{paper_id}")
        if self.vector_store.index_path.exists() and self.vector_store.mapping_path.exists():
            self.vector_store.load_index()
        self.assertFalse(self.vector_store.contains_paper(paper_id))


if __name__ == "__main__":
    unittest.main()
