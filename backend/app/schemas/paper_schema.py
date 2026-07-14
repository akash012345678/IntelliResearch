from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator

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

    @field_validator("keywords", "algorithms", "datasets", "methodologies", "application_domains", mode="before")
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

    @field_validator("keywords", "algorithms", "datasets", "methodologies", "application_domains", mode="before")
    @classmethod
    def default_empty_list(cls, v):
        return v if v is not None else []

    class Config:
        from_attributes = True

class UploadSuccessResponse(BaseModel):
    message: str = Field(default="Upload Successful")
    paper_id: int
    title: str

class PaperMetadataResponse(BaseModel):
    keywords: List[str] = Field(default_factory=list)
    algorithms: List[str] = Field(default_factory=list)
    datasets: List[str] = Field(default_factory=list)
    methodologies: List[str] = Field(default_factory=list)
    application_domains: List[str] = Field(default_factory=list)

    @field_validator("keywords", "algorithms", "datasets", "methodologies", "application_domains", mode="before")
    @classmethod
    def default_empty_list(cls, v):
        return v if v is not None else []

    class Config:
        from_attributes = True
