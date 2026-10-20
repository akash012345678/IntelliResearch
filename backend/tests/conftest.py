import os
import pytest

# Force tests to use isolated test database BEFORE app or settings are imported
TEST_DB_FILE = os.path.join(os.path.dirname(__file__), "test_runner_temp.db")
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_FILE}"

from sqlalchemy import create_engine
from app.database.session import Base, init_db, engine, SessionLocal
from app.main import app

@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    # Initialize clean test schema
    init_db(target_engine=engine)
    
    yield

    # Clean up test database file after test suite finishes
    engine.dispose()
    if os.path.exists(TEST_DB_FILE):
        try:
            os.remove(TEST_DB_FILE)
        except Exception:
            pass

@pytest.fixture
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
