"""
Módulo scraper para BO-GOV-SCRAPER-BUHO
"""

from .models import Documento, Articulo, PipelineResult
from .pipeline import run_site_pipeline, run_all_sites_pipeline
from .sites import get_scraper, SCRAPERS
from .extractors import PDFExtractor
from .parsers import LegalParser
from .metadata_extractor import LegalMetadataExtractor
from .exporter import DataExporter, HistoricalTracker

__all__ = [
    "Documento",
    "Articulo",
    "PipelineResult",
    "run_site_pipeline",
    "run_all_sites_pipeline",
    "get_scraper",
    "SCRAPERS",
    "PDFExtractor",
    "LegalParser",
    "LegalMetadataExtractor",
    "DataExporter",
    "HistoricalTracker",
]
