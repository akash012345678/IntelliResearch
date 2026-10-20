from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator

class EntityDetailResponse(BaseModel):
    name: str
    category: str
    role: str
    confidence: float = 0.0
    evidence_text: Optional[str] = None
    evidence_section: Optional[str] = None
    source: Optional[str] = None

class PaperResponse(BaseModel):
    id: int
    title: str
    filename: str
    uploaded_at: datetime
    keywords: List[str] = Field(default_factory=list)
    algorithms: List[str] = Field(default_factory=list)
    datasets: List[str] = Field(default_factory=list)
    methodologies: List[str] = Field(default_factory=list)
    application_domains: List[str] = Field(default_factory=list)
    keyword_details: List[Dict[str, Any]] = Field(default_factory=list)
    algorithm_details: List[Dict[str, Any]] = Field(default_factory=list)
    dataset_details: List[Dict[str, Any]] = Field(default_factory=list)
    methodology_details: List[Dict[str, Any]] = Field(default_factory=list)

    @field_validator("keywords", "algorithms", "datasets", "methodologies", "application_domains", "keyword_details", "algorithm_details", "dataset_details", "methodology_details", mode="before")
    @classmethod
    def default_empty_list(cls, v):
        return v if v is not None else []

    class Config:
        from_attributes = True

class PaperDetailResponse(BaseModel):
    id: int
    title: str
    abstract: Optional[str] = None
    full_text: str
    filename: str
    uploaded_at: datetime
    keywords: List[str] = Field(default_factory=list)
    algorithms: List[str] = Field(default_factory=list)
    datasets: List[str] = Field(default_factory=list)
    methodologies: List[str] = Field(default_factory=list)
    application_domains: List[str] = Field(default_factory=list)
    keyword_details: List[Dict[str, Any]] = Field(default_factory=list)
    algorithm_details: List[Dict[str, Any]] = Field(default_factory=list)
    dataset_details: List[Dict[str, Any]] = Field(default_factory=list)
    methodology_details: List[Dict[str, Any]] = Field(default_factory=list)

    @field_validator("keywords", "algorithms", "datasets", "methodologies", "application_domains", "keyword_details", "algorithm_details", "dataset_details", "methodology_details", mode="before")
    @classmethod
    def default_empty_list(cls, v):
        return v if v is not None else []

    class Config:
        from_attributes = True

class UploadSuccessResponse(BaseModel):
    message: str = Field(default="Upload Successful")
    paper_id: int
    title: str
    database_status: str = Field(default="success")
    semantic_index_status: Optional[str] = Field(default="indexed")

class PaperMetadataResponse(BaseModel):
    keywords: List[str] = Field(default_factory=list)
    algorithms: List[str] = Field(default_factory=list)
    datasets: List[str] = Field(default_factory=list)
    methodologies: List[str] = Field(default_factory=list)
    application_domains: List[str] = Field(default_factory=list)
    keyword_details: List[Dict[str, Any]] = Field(default_factory=list)
    algorithm_details: List[Dict[str, Any]] = Field(default_factory=list)
    dataset_details: List[Dict[str, Any]] = Field(default_factory=list)
    methodology_details: List[Dict[str, Any]] = Field(default_factory=list)

    @field_validator("keywords", "algorithms", "datasets", "methodologies", "application_domains", "keyword_details", "algorithm_details", "dataset_details", "methodology_details", mode="before")
    @classmethod
    def default_empty_list(cls, v):
        return v if v is not None else []

    class Config:
        from_attributes = True

class SemanticSearchRequest(BaseModel):
    query: str = Field(..., description="Natural language search query")
    top_k: int = Field(default=5, description="Number of top search results to return")

    @field_validator("query")
    @classmethod
    def validate_query(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Search query cannot be empty or whitespace-only.")
        return v.strip()

    @field_validator("top_k")
    @classmethod
    def validate_top_k(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("top_k must be a positive integer.")
        if v > 20:
            raise ValueError("top_k cannot exceed maximum limit of 20.")
        return v

class SemanticSearchResultItem(BaseModel):
    paper_id: int
    title: str
    abstract: Optional[str] = None
    keywords: List[str] = Field(default_factory=list)
    algorithms: List[str] = Field(default_factory=list)
    datasets: List[str] = Field(default_factory=list)
    methodologies: List[str] = Field(default_factory=list)
    application_domains: List[str] = Field(default_factory=list)
    similarity_score: float

    @field_validator("keywords", "algorithms", "datasets", "methodologies", "application_domains", mode="before")
    @classmethod
    def default_empty_list(cls, v):
        return v if v is not None else []

    class Config:
        from_attributes = True

class SemanticSearchResponse(BaseModel):
    query: str
    total_results: int
    results: List[SemanticSearchResultItem]

class SourcePaperInfo(BaseModel):
    paper_id: int
    title: str

class RelatedPapersResponse(BaseModel):
    source_paper: SourcePaperInfo
    total_results: int
    related_papers: List[SemanticSearchResultItem]


