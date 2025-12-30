"""
PDF Utilities Module

Handles PDF text extraction and filename processing.

Responsibilities:
    - Extract text from PDF files
    - Convert filenames to readable titles
    - PDF validation
"""

import re
from pathlib import Path
from typing import Optional

from .config import config

# Check for PyPDF2 availability
try:
    from PyPDF2 import PdfReader
    HAS_PYPDF2 = True
except ImportError:
    HAS_PYPDF2 = False


def is_pdf_support_available() -> bool:
    """Check if PDF text extraction is available."""
    return HAS_PYPDF2


def extract_text(pdf_path: Path, max_pages: Optional[int] = None) -> str:
    """
    Extract text from the first few pages of a PDF.

    Args:
        pdf_path: Path to the PDF file
        max_pages: Maximum number of pages to extract (default from config)

    Returns:
        Extracted text, or empty string if extraction fails
    """
    if not HAS_PYPDF2:
        return ""

    if max_pages is None:
        max_pages = config.app.max_pdf_pages

    try:
        reader = PdfReader(str(pdf_path))
        text = ""
        for i, page in enumerate(reader.pages[:max_pages]):
            page_text = page.extract_text()
            if page_text:
                text += page_text
        return text[:3000]  # Limit total length
    except Exception as e:
        print(f"  Warning: Could not extract PDF text: {e}")
        return ""


def filename_to_title(filename: str) -> str:
    """
    Convert a PDF filename to a readable title.

    Args:
        filename: PDF filename (e.g., "paper-title_v2.pdf")

    Returns:
        Readable title (e.g., "paper title v2")
    """
    # Remove extension
    title = filename.replace(".pdf", "").replace(".PDF", "")

    # Replace separators with spaces
    title = title.replace("-", " ").replace("_", " ")

    # Normalize whitespace
    title = re.sub(r'\s+', ' ', title).strip()

    return title


def title_to_filename(title: str, max_length: Optional[int] = None) -> str:
    """
    Convert a title to a valid filename.

    Args:
        title: Paper title
        max_length: Maximum filename length (default from config)

    Returns:
        Valid filename with .pdf extension
    """
    if max_length is None:
        max_length = config.app.max_filename_length

    # Remove invalid filename characters
    clean_title = re.sub(r'[<>:"/\\|?*]', '', title)

    # Truncate and strip
    clean_title = clean_title[:max_length].strip()

    return f"{clean_title}.pdf"


def get_pdf_page_count(pdf_path: Path) -> int:
    """
    Get the number of pages in a PDF.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        Number of pages, or 0 if cannot be determined
    """
    if not HAS_PYPDF2:
        return 0

    try:
        reader = PdfReader(str(pdf_path))
        return len(reader.pages)
    except Exception:
        return 0


def is_valid_pdf(pdf_path: Path) -> bool:
    """
    Check if a file is a valid PDF.

    Args:
        pdf_path: Path to check

    Returns:
        True if valid PDF, False otherwise
    """
    if not pdf_path.exists():
        return False

    if not pdf_path.suffix.lower() == ".pdf":
        return False

    if not HAS_PYPDF2:
        return True  # Assume valid if we can't check

    try:
        reader = PdfReader(str(pdf_path))
        # Try to access pages to validate
        _ = len(reader.pages)
        return True
    except Exception:
        return False
