"""
Core modules for BÚHO scraper system
"""
from .base_scraper import BaseScraper
from .pdf_parser import PDFParser
from .delta_manager import DeltaUpdateManager
from .utils import (
    normalize_text,
    extract_date,
    download_file,
    calculate_hash,
    ensure_dir
)

__all__ = [
    'BaseScraper',
    'PDFParser',
    'DeltaUpdateManager',
    'normalize_text',
    'extract_date',
    'download_file',
    'calculate_hash',
    'ensure_dir'
]
