import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.settings import settings
from app.database.session import init_db
from app.utils.logging import setup_logging
from app.api.upload_api import router as upload_router
from app.api.paper_api import router as paper_router

# 1. Setup global logging
setup_logging()
logger = logging.getLogger("app.main")

# 2. Configure app lifecycles (Startup / Shutdown)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    logger.info("Initializing IntelliResearch Application backend...")
    
    # Create file upload directories if they don't exist
    try:
        settings.create_directories()
        logger.info("Local upload directories verified and created.")
    except Exception as e:
        logger.critical(f"Failed to create upload directories: {e}")
        raise e

    # Create DB tables
    try:
        init_db()
        logger.info("Database schemas initialized successfully.")
    except Exception as e:
        logger.critical(f"Failed to initialize database tables: {e}")
        logger.critical("Check if your PostgreSQL service is running and DATABASE_URL is correct.")
        # We don't fail hard here so the developer can update env variables, but startup will be degraded.

    yield
    # Shutdown actions
    logger.info("IntelliResearch Application backend shutting down.")

# 3. Create FastAPI App instance
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend API for IntelliResearch gap discovery and recommendation system.",
    version="1.0.0",
    lifespan=lifespan
)

# 4. CORS Middleware Configuration
# Allows requests from frontend server (typically http://localhost:5173 for Vite React)
origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
    # Wildcards can be enabled in dev, but explicit is cleaner.
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all HTTP headers
)

# 5. Include API Routers
app.include_router(upload_router, prefix=settings.API_V1_STR, tags=["Upload"])
app.include_router(paper_router, prefix=settings.API_V1_STR, tags=["Papers"])

# 6. Basic Root Health Check
@app.get("/", tags=["Health"])
def read_root():
    return {
        "status": "healthy",
        "app": settings.PROJECT_NAME,
        "version": "1.0.0"
    }
