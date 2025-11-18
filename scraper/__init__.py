"""
Scrapers for Bolivian government websites
"""
from scraper.base_scraper import BaseScraper
from scraper.tcp_scraper import TCPScraper
from scraper.tsj_scraper import TSJScraper
from scraper.asfi_scraper import ASFIScraper
from scraper.sin_scraper import SINScraper
from scraper.contraloria_scraper import ContraloriaScraper

SCRAPERS = {
    'tcp': TCPScraper,
    'tsj': TSJScraper,
    'asfi': ASFIScraper,
    'sin': SINScraper,
    'contraloria': ContraloriaScraper
}

def get_scraper(name: str) -> BaseScraper:
    """Get scraper instance by name"""
    if name not in SCRAPERS:
        raise ValueError(f"Unknown scraper: {name}. Available: {list(SCRAPERS.keys())}")
    return SCRAPERS[name]()

__all__ = ['BaseScraper', 'SCRAPERS', 'get_scraper']
