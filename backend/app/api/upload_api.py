import logging
import shutil
from pathlib import Path
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.database.session import get_db
from app.models.paper_model import ResearchPaper
from app.schemas.paper_schema import UploadSuccessResponse
from app.services.pdf_service import PDFService
from app.services.metadata_extractor import MetadataExtractor

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/upload", response_model=UploadSuccessResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload a single research paper (PDF), validate it, extract text and metadata,
    store files, and persist metadata in the database.
    """
    logger.info(f"Received upload request for file: {file.filename}")
    
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided in upload."
        )

    # 1. Size Validation (read content-length or seek file)
    try:
        # Seek to end of file to determine size
        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)
    except Exception as e:
        logger.error(f"Failed to determine file size for {file.filename}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not read file size during upload validation."
        )

    try:
        PDFService.validate_file(file.filename, file_size)
    except ValueError as ve:
        logger.warning(f"File validation failed for {file.filename}: {ve}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )

    # 2. Magic Byte Check (must start with %PDF)
    try:
        header = await file.read(4)
        await file.seek(0)
        if header != b"%PDF":
            logger.warning(f"Uploaded file {file.filename} failed PDF magic byte check.")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file format: File contents do not represent a valid PDF."
            )
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        logger.error(f"Error reading magic bytes from {file.filename}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error reading file headers."
        )

    # 3. Resolve filename collisions
    original_filename = Path(file.filename).name
    save_path = settings.ORIGINAL_PAPERS_DIR / original_filename
    counter = 1
    # If file exists, append _counter
    while save_path.exists():
        stem = Path(original_filename).stem
        ext = Path(original_filename).suffix
        save_path = settings.ORIGINAL_PAPERS_DIR / f"{stem}_{counter}{ext}"
        counter += 1
    
    unique_filename = save_path.name

    # 4. Save PDF to uploads/original_papers
    try:
        # Create directories just in case they don't exist
        settings.create_directories()
        with open(save_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        logger.info(f"Successfully saved original PDF to {save_path}")
    except Exception as e:
        logger.error(f"Failed to save PDF file {unique_filename}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save PDF to server storage."
        )

    # 5. Extract Text & Metadata using PyMuPDF Service
    try:
        extracted_data = PDFService.extract_metadata_and_text(save_path, unique_filename)
    except ValueError as ve:
        # Clean up the saved PDF file since parsing failed
        if save_path.exists():
            save_path.unlink()
        logger.warning(f"PDF extraction validation error for {unique_filename}: {ve}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        # Clean up the saved PDF file since parsing failed
        if save_path.exists():
            save_path.unlink()
        logger.error(f"Failed to extract metadata/text from {unique_filename}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Text extraction failed: {str(e)}"
        )

    # 6. Save Extracted Text to uploads/extracted_text/{paper_name}.txt
    try:
        PDFService.save_extracted_text(extracted_data["full_text"], unique_filename)
        logger.info(f"Successfully saved extracted text for {unique_filename}")
    except Exception as e:
        # Clean up the saved PDF
        if save_path.exists():
            save_path.unlink()
        logger.error(f"Failed to save extracted text file for {unique_filename}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Text extraction completed, but failed to save extracted text output file."
        )

    # 7. Persist Metadata into PostgreSQL Database
    try:
        # Extract metadata automatically using the rule-based metadata extractor
        metadata = MetadataExtractor.extract(
            title=extracted_data["title"],
            abstract=extracted_data["abstract"],
            full_text=extracted_data["full_text"]
        )

        db_paper = ResearchPaper(
            title=extracted_data["title"],
            abstract=extracted_data["abstract"],
            full_text=extracted_data["full_text"],
            filename=unique_filename,
            keywords=metadata["keywords"],
            algorithms=metadata["algorithms"],
            datasets=metadata["datasets"],
            methodologies=metadata["methodologies"],
            application_domains=metadata["application_domains"]
        )
        db.add(db_paper)
        db.commit()
        db.refresh(db_paper)
        logger.info(f"Successfully persisted paper metadata in database. ID: {db_paper.id}")
        
        return UploadSuccessResponse(
            message="Upload Successful",
            paper_id=db_paper.id,
            title=db_paper.title
        )
    except Exception as e:
        # Clean up local files on db failure
        if save_path.exists():
            save_path.unlink()
        txt_path = settings.EXTRACTED_TEXT_DIR / f"{Path(unique_filename).stem}.txt"
        if txt_path.exists():
            txt_path.unlink()
            
        logger.critical(f"Database insertion failed for paper {unique_filename}: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save paper metadata to database."
        )
