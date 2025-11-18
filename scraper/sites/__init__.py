"""
Scrapers específicos para sitios gubernamentales bolivianos
"""
from .tcp_scraper import TCPScraper
from .tsj_scraper import TSJScraper
from .contraloria_scraper import ContraloriaScraper
from .asfi_scraper import ASFIScraper
from .sin_scraper import SINScraper

__all__ = [
    'TCPScraper',
    'TSJScraper',
    'ContraloriaScraper',
    'ASFIScraper',
    'SINScraper',
]
