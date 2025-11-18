"""
Módulo de scrapers para sitios específicos
"""

from .base_scraper import BaseScraper
from .tcp_scraper import TCPScraper
from .tsj_scraper import TSJScraper
from .asfi_scraper import ASFIScraper
from .sin_scraper import SINScraper
from .contraloria_scraper import ContraloriaScraper

# Registro de scrapers disponibles
SCRAPERS = {
    'tcp': TCPScraper,
    'tsj': TSJScraper,
    'asfi': ASFIScraper,
    'sin': SINScraper,
    'contraloria': ContraloriaScraper,
    # 'gaceta_oficial': GacetaScraper,  # Por implementar
}


def get_scraper(site_id: str) -> BaseScraper:
    """
    Obtener instancia de scraper para un sitio

    Args:
        site_id: ID del sitio

    Returns:
        Instancia del scraper

    Raises:
        ValueError: Si el sitio no tiene scraper implementado
    """
    scraper_class = SCRAPERS.get(site_id)
    if not scraper_class:
        raise ValueError(f"Scraper no implementado para sitio: {site_id}")

    return scraper_class()


__all__ = [
    "BaseScraper",
    "TCPScraper",
    "TSJScraper",
    "ASFIScraper",
    "SINScraper",
    "ContraloriaScraper",
    "get_scraper",
    "SCRAPERS"
]
