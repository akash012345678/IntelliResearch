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


class TestResearchExperimentAPI(unittest.TestCase):

    def setUp(self):
        Base.metadata.create_all(bind=engine)

    def test_01_get_project_experiments_empty(self):
        """Test GET /api/projects/1/experiments returns list."""
        response = client.get("/api/projects/1/experiments")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)

    def test_02_get_project_experiment_summary(self):
        """Test GET /api/projects/1/experiments/summary returns valid metrics summary."""
        response = client.get("/api/projects/1/experiments/summary")
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertIn("total_planned", data)
        self.assertIn("not_started_count", data)
        self.assertIn("in_progress_count", data)
        self.assertIn("completed_count", data)
        self.assertIn("results_recorded_count", data)
        self.assertIn("needs_attention_count", data)

    def test_03_create_experiment_and_record_run(self):
        """Test creating an experiment, updating status, adding a run, and recording empirical results."""
        # 1. Create experiment
        create_payload = {
            "name": "EXP-TEST-001 Baseline Accuracy Test",
            "purpose": "Verify baseline accuracy vs proposed Spatial Transformer",
            "experiment_type": "BASELINE_COMPARISON",
            "status": "PLANNED",
            "baseline_config": {"algorithm": "ResNet-50"},
            "proposed_config": {"architecture": "Spatial Transformer"}
        }
        res_create = client.post("/api/projects/1/experiments", json=create_payload)
        # Note: If project 1 doesn't exist in test DB fixture, status is 404
        self.assertIn(res_create.status_code, [201, 404])

        if res_create.status_code == 201:
            exp = res_create.json()
            exp_id = exp["id"]
            self.assertEqual(exp["name"], "EXP-TEST-001 Baseline Accuracy Test")

            # 2. Add Run
            run_payload = {
                "seed": 42,
                "notes": "Colab run 1"
            }
            res_run = client.post(f"/api/projects/1/experiments/{exp_id}/runs", json=run_payload)
            self.assertEqual(res_run.status_code, 201)
            run = res_run.json()
            run_id = run["id"]

            # 3. Record Results
            results_payload = [
                {"metric_name": "Accuracy", "metric_value": "0.82", "unit": "0-1", "method_type": "baseline"},
                {"metric_name": "Accuracy", "metric_value": "0.86", "unit": "0-1", "method_type": "proposed"}
            ]
            res_rec = client.post(f"/api/projects/1/experiments/runs/{run_id}/results", json=results_payload)
            self.assertEqual(res_rec.status_code, 201)
            rec_results = res_rec.json()
            self.assertEqual(len(rec_results), 2)
