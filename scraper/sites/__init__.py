"""
Scrapers de sitios gubernamentales bolivianos.
"""

from scraper.sites.gaceta_oficial import GacetaOficialScraper
from scraper.sites.tsj_genesis import TSJGenesisScraper
from scraper.sites.tcp import TCPScraper
from scraper.sites.asfi import ASFIScraper
from scraper.sites.sin import SINScraper


# Registro de scrapers disponibles
SCRAPER_REGISTRY = {
    "gaceta_oficial": GacetaOficialScraper,
    "tsj_genesis": TSJGenesisScraper,
    "tcp": TCPScraper,
    "asfi": ASFIScraper,
    "sin": SINScraper
}


def get_scraper_class(site_id: str):
    """
    Obtiene la clase de scraper para un sitio dado.

    Args:
        site_id: ID del sitio

    Returns:
        Clase del scraper o None si no existe
    """
    return SCRAPER_REGISTRY.get(site_id)


__all__ = [
    'GacetaOficialScraper',
    'TSJGenesisScraper',
    'TCPScraper',
    'ASFIScraper',
    'SINScraper',
    'SCRAPER_REGISTRY',
    'get_scraper_class'
]
