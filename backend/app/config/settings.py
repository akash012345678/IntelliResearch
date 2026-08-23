import os
from typing import Optional
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

# Base directory of the backend folder
BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    PROJECT_NAME: str = "IntelliResearch API"
    API_V1_STR: str = "/api"
    
    # Database Configuration
    DATABASE_URL: str = Field(
        default="postgresql+psycopg2://postgres:postgres@localhost:5432/intelliresearch"
    )
    
    # Upload Configurations
    MAX_FILE_SIZE_MB: int = 50
    ALLOWED_EXTENSIONS: str = "pdf"
    
    # Upload Directories (absolute paths relative to app directory)
    UPLOAD_ROOT: Path = BASE_DIR / "app" / "uploads"
    ORIGINAL_PAPERS_DIR: Path = BASE_DIR / "app" / "uploads" / "original_papers"
    EXTRACTED_TEXT_DIR: Path = BASE_DIR / "app" / "uploads" / "extracted_text"
    EMBEDDINGS_DIR: Path = BASE_DIR / "app" / "uploads" / "embeddings"

    # LLM Settings (Optional)
    LLM_PROVIDER: Optional[str] = Field(default=None)
    LLM_API_KEY: Optional[str] = Field(default=None)
    LLM_MODEL: Optional[str] = Field(default=None)


    model_config = SettingsConfigDict(

        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def create_directories(self) -> None:
        """Create required directories for file uploads if they do not exist."""
        self.ORIGINAL_PAPERS_DIR.mkdir(parents=True, exist_ok=True)
        self.EXTRACTED_TEXT_DIR.mkdir(parents=True, exist_ok=True)
        self.EMBEDDINGS_DIR.mkdir(parents=True, exist_ok=True)

settings = Settings()
