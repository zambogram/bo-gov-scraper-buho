"""
Módulo scraper para BÚHO
Sistema de scraping de leyes bolivianas
"""

from .multi_site_scraper import MultiSiteScraper
from .document_processor import DocumentProcessor
from .metadata import MetadataExtractor
from .pdf_splitter import PDFSplitter
from .database import LawDatabase

__all__ = [
    'MultiSiteScraper',
    'DocumentProcessor',
    'MetadataExtractor',
    'PDFSplitter',
    'LawDatabase'
]

__version__ = '1.0.0'
