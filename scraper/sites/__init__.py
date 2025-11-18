"""
Módulo de scrapers para sitios específicos
"""

from .base_scraper import BaseScraper
from .tcp_scraper import TCPScraper
from .tsj_scraper import TSJScraper
from .asfi_scraper import ASFIScraper
from .sin_scraper import SINScraper
from .contraloria_scraper import ContraloriaScraper
from .gaceta_scraper import GacetaScraper
from .att_scraper import ATTScraper
from .mintrabajo_scraper import MinTrabajoScraper

# Importar scrapers avanzados (con Selenium)
try:
    from .advanced.gaceta_oficial_scraper import GacetaOficialScraper
    ADVANCED_AVAILABLE = True
except ImportError:
    ADVANCED_AVAILABLE = False

# Registro de scrapers disponibles
# Prioridad a scrapers avanzados si están disponibles
SCRAPERS = {
    'tcp': TCPScraper,
    'tsj': TSJScraper,
    'asfi': ASFIScraper,
    'sin': SINScraper,
    'contraloria': ContraloriaScraper,
    'gaceta_oficial': GacetaOficialScraper if ADVANCED_AVAILABLE else GacetaScraper,
    'att': ATTScraper,
    'mintrabajo': MinTrabajoScraper,
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
    "GacetaScraper",
    "ATTScraper",
    "MinTrabajoScraper",
    "get_scraper",
    "SCRAPERS"
]
