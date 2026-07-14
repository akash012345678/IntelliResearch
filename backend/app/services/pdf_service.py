import logging
import re
from pathlib import Path
from typing import Optional
import fitz  # PyMuPDF
from app.config.settings import settings

logger = logging.getLogger(__name__)

class PDFService:
    @staticmethod
    def validate_file(filename: str, file_size: int) -> None:
        """
        Validate the file extension and file size.
        Raises ValueError if validation fails.
        """
        ext = filename.split(".")[-1].lower() if "." in filename else ""
        if ext != settings.ALLOWED_EXTENSIONS:
            raise ValueError(f"Invalid file extension: .{ext}. Only PDF files are allowed.")
        
        max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
        if file_size > max_bytes:
            raise ValueError(f"File size exceeds limit of {settings.MAX_FILE_SIZE_MB}MB (current size: {file_size / (1024 * 1024):.2f}MB).")

    @classmethod
    def extract_metadata_and_text(cls, pdf_path: Path, filename: str) -> dict:
        """
        Extract text content, title, and abstract from the PDF.
        Returns a dictionary with extracted data.
        """
        try:
            doc = fitz.open(pdf_path)
        except Exception as e:
            logger.error(f"PyMuPDF failed to open PDF at {pdf_path}: {e}")
            raise ValueError("Failed to parse the PDF file. It may be corrupted.") from e

        try:
            # 1. Extract Full Text
            full_text_list = []
            for page in doc:
                full_text_list.append(page.get_text())
            full_text = "\n".join(full_text_list)

            # 2. Extract Title using heuristics
            title = cls._heuristic_extract_title(doc, filename)

            # 3. Extract Abstract using heuristics
            abstract = cls._heuristic_extract_abstract(doc)

            return {
                "title": title,
                "abstract": abstract,
                "full_text": full_text,
                "filename": filename
            }
        except Exception as e:
            logger.error(f"Error extracting metadata from PDF {filename}: {e}")
            raise RuntimeError(f"Error during metadata extraction: {str(e)}") from e
        finally:
            doc.close()

    @classmethod
    def _heuristic_extract_title(cls, doc: fitz.Document, filename: str) -> str:
        """
        Heuristic method to extract the research paper's title:
        1. Check PDF metadata first.
        2. Inspect page 1 and look for the largest font size text spans.
        3. Fallback to cleaning the filename.
        """
        # Step 1: Check Metadata
        meta_title = doc.metadata.get("title")
        if meta_title and len(meta_title.strip()) > 5:
            # Check if metadata is just a generic name or file path
            generic_patterns = ["untitled", "microsoft word", "latex templates", "pdf creator", "arxiv"]
            if not any(pattern in meta_title.lower() for pattern in generic_patterns):
                return meta_title.strip()

        # Step 2: Font-Size heuristic on Page 1
        try:
            page = doc[0]
            blocks = page.get_text("dict")["blocks"]
            spans_info = []

            for b in blocks:
                if "lines" in b:
                    for l in b["lines"]:
                        for s in l["spans"]:
                            text = s["text"].strip()
                            if len(text) > 2:  # ignore single characters or tiny noise
                                spans_info.append((s["size"], text))

            if spans_info:
                # Find maximum size
                max_size = max(s[0] for s in spans_info)
                # Filter spans that have size close to maximum (e.g. within 1pt, in case title spans lines)
                title_spans = [s[1] for s in spans_info if (max_size - s[0]) < 1.0]
                
                # Combine title spans and clean space
                heuristic_title = " ".join(title_spans)
                heuristic_title = re.sub(r'\s+', ' ', heuristic_title).strip()
                
                # Title shouldn't be overly long (e.g. > 250 chars might indicate we grabbed too much text)
                if 10 < len(heuristic_title) < 250:
                    return heuristic_title
        except Exception as e:
            logger.warning(f"Title font size heuristic failed for {filename}: {e}")

        # Step 3: Fallback to filename (cleaned)
        # Strip extension
        clean_name = filename.rsplit(".", 1)[0]
        # Replace underscores/hyphens with spaces and capitalize
        clean_name = re.sub(r'[-_]', ' ', clean_name)
        # Capitalize words
        return clean_name.strip().title()

    @classmethod
    def _heuristic_extract_abstract(cls, doc: fitz.Document) -> Optional[str]:
        """
        Heuristic method to extract abstract:
        Look for "Abstract" header on the first two pages and extract contents until the next header.
        """
        abstract_text = ""
        # Search the first 2 pages (abstract is usually on page 1, sometimes spills over or starts page 2)
        pages_to_search = min(2, len(doc))
        
        for page_idx in range(pages_to_search):
            page = doc[page_idx]
            page_text = page.get_text("text")
            
            # Use regex to find abstract (case insensitive)
            match = re.search(r'\babstract\b', page_text, re.IGNORECASE)
            if match:
                start_index = match.end()
                text_after_abstract = page_text[start_index:].strip()
                
                # Remove common header separator characters (e.g., '-', '.', '\n') at start
                text_after_abstract = re.sub(r'^[:\-\.\s\n]+', '', text_after_abstract)
                
                # Define end boundaries (commonly "Introduction", "Keywords", "1. ")
                end_markers = [
                    r'\b1\b\.?\s+\bIntroduction\b',
                    r'\bIntroduction\b',
                    r'\bKeywords\b',
                    r'\bIndex\s+Terms\b',
                    r'\bI\b\.?\s+\bIntroduction\b'
                ]
                
                earliest_end = len(text_after_abstract)
                for marker in end_markers:
                    end_match = re.search(marker, text_after_abstract, re.IGNORECASE)
                    if end_match:
                        earliest_end = min(earliest_end, end_match.start())
                
                # Take everything up to the earliest end marker
                abstract_text = text_after_abstract[:earliest_end].strip()
                
                # Clean up whitespace and line breaks
                abstract_text = re.sub(r'\s+', ' ', abstract_text)
                
                # Validate length of abstract (should be substantial, e.g. > 50 chars, but not massive)
                if len(abstract_text) > 50:
                    # Truncate if it seems to have captured too much text (e.g., > 3000 chars)
                    if len(abstract_text) > 3000:
                        abstract_text = abstract_text[:3000] + "..."
                    return abstract_text
                
        return None

    @staticmethod
    def save_extracted_text(text: str, filename: str) -> Path:
        """
        Save the raw text content to the uploads/extracted_text folder.
        """
        paper_name = Path(filename).stem
        txt_filename = f"{paper_name}.txt"
        dest_path = settings.EXTRACTED_TEXT_DIR / txt_filename
        
        try:
            with open(dest_path, "w", encoding="utf-8") as f:
                f.write(text)
            return dest_path
        except Exception as e:
            logger.error(f"Failed to write extracted text to {dest_path}: {e}")
            raise RuntimeError(f"Failed to save extracted text file: {e}") from e
