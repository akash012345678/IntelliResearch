import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.config.settings import settings

logger = logging.getLogger(__name__)

# Configure SQLAlchemy connection arguments for SQLite if needed
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

try:
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args=connect_args,
        pool_pre_ping=True  # Avoid connection drop issues
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
except Exception as e:
    logger.critical(f"Failed to create SQLAlchemy engine with URL {settings.DATABASE_URL}: {e}")
    raise e

Base = declarative_base()

def get_db():
    """Dependency generator for database sessions used in FastAPI routes."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db() -> None:
    """Initialize the database by creating all defined tables if they do not exist."""
    # Ensure tables are created. Import models first so SQLAlchemy knows about them.
    from app.models.paper_model import ResearchPaper  # noqa: F401
    Base.metadata.create_all(bind=engine)

    # Run automatic migrations to add new columns if they are missing
    from sqlalchemy import inspect, text
    inspector = inspect(engine)
    try:
        columns = [col["name"] for col in inspector.get_columns("research_papers")]
        new_cols = ["keywords", "algorithms", "datasets", "methodologies", "application_domains"]
        db_type = engine.dialect.name

        with engine.begin() as conn:
            for col in new_cols:
                if col not in columns:
                    logger.info(f"Adding missing column '{col}' to 'research_papers' table...")
                    if db_type == "sqlite":
                        conn.execute(text(f"ALTER TABLE research_papers ADD COLUMN {col} TEXT DEFAULT '[]'"))
                    else:
                        conn.execute(text(f"ALTER TABLE research_papers ADD COLUMN {col} JSON DEFAULT '[]'"))
                    logger.info(f"Successfully added column '{col}' to 'research_papers'.")
    except Exception as e:
        logger.error(f"Failed to check or execute database migrations: {e}")
