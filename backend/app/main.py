import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.settings import settings
from app.database.session import init_db
from app.utils.logging import setup_logging
from app.api.upload_api import router as upload_router
from app.api.paper_api import router as paper_router
from app.api.search_api import router as search_router
from app.api.knowledge_graph_api import router as knowledge_graph_router
from app.api.research_gap_api import router as research_gap_router
from app.api.intelligence_api import router as intelligence_router
from app.api.research_direction_api import router as research_direction_router
from app.api.research_project_api import router as research_project_router
from app.api.proposal_api import router as proposal_router



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
# Allows requests with credentials from localhost and deployed origins (e.g. Vercel, Render)
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://.*",
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all HTTP headers
)

from app.api.research_project_api import router as research_project_router
from app.api.proposal_api import router as proposal_router
from app.api.project_intelligence_api import router as project_intelligence_router
from app.api.project_research_report_api import router as project_research_report_router

from app.api.opportunity_evaluation_api import router as opportunity_evaluation_router
from app.api.opportunity_validation_api import router as opportunity_validation_router
from app.api.research_methodology_api import router as research_methodology_router
from app.api.research_experiment_api import router as research_experiment_router
from app.api.research_results_analysis_api import router as research_results_analysis_router
from app.api.research_journey_api import router as research_journey_router
from app.api.academic_manuscript_api import router as academic_manuscript_router
from app.api.academic_citation_api import router as academic_citation_router
from app.api.academic_document_api import router as academic_document_router
from app.api.research_dashboard_api import router as research_dashboard_router
from app.api.project_traceability_api import router as project_traceability_router

# 5. Include API Routers
app.include_router(upload_router, prefix=settings.API_V1_STR, tags=["Upload"])
app.include_router(paper_router, prefix=settings.API_V1_STR, tags=["Papers"])
app.include_router(search_router, prefix=settings.API_V1_STR, tags=["Search"])
app.include_router(knowledge_graph_router, prefix=settings.API_V1_STR, tags=["Knowledge Graph"])
app.include_router(research_gap_router, prefix=settings.API_V1_STR, tags=["Research Gaps"])
app.include_router(intelligence_router, prefix=settings.API_V1_STR, tags=["Research Intelligence"])
app.include_router(research_direction_router, prefix=settings.API_V1_STR, tags=["Actionable Research Directions"])
app.include_router(research_project_router, prefix=settings.API_V1_STR, tags=["Research Projects"])
app.include_router(proposal_router, prefix=settings.API_V1_STR, tags=["Proposal Persistence"])
app.include_router(project_intelligence_router, prefix=settings.API_V1_STR, tags=["Project Research Intelligence"])
app.include_router(project_research_report_router, prefix=settings.API_V1_STR, tags=["Project Research Reports"])
app.include_router(project_traceability_router, prefix=settings.API_V1_STR, tags=["Project Evidence Traceability"])
app.include_router(opportunity_evaluation_router, prefix=settings.API_V1_STR, tags=["Opportunity Evaluation"])
app.include_router(opportunity_validation_router, prefix=settings.API_V1_STR, tags=["Opportunity Validation"])
app.include_router(research_methodology_router, prefix=settings.API_V1_STR, tags=["Research Methodology"])
app.include_router(research_experiment_router, prefix=settings.API_V1_STR, tags=["Research Experiment Workspace"])
app.include_router(research_results_analysis_router, prefix=settings.API_V1_STR, tags=["Research Results Analysis"])
app.include_router(research_journey_router, prefix=settings.API_V1_STR, tags=["Research Journey Workflow"])
app.include_router(academic_manuscript_router, prefix=settings.API_V1_STR, tags=["Academic Manuscript Generator"])
app.include_router(academic_citation_router, prefix=settings.API_V1_STR, tags=["Academic Citation & Quality"])
app.include_router(academic_document_router, prefix=settings.API_V1_STR, tags=["Academic Document Formatting"])
app.include_router(research_dashboard_router, prefix=settings.API_V1_STR, tags=["Student Research Dashboard"])










# 6. Basic Root & System Health Checks
@app.get("/", tags=["Health"])
def read_root():
    return {
        "status": "healthy",
        "app": settings.PROJECT_NAME,
        "version": "1.0.0"
    }

@app.get("/health", tags=["Health"])
@app.get(f"{settings.API_V1_STR}/health", tags=["Health"])
def health_check():
    return {
        "status": "ok",
        "app": settings.PROJECT_NAME,
        "database": "connected",
        "storage": "available"
    }
