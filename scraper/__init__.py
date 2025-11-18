"""
BÚHO - Scraper Sistema de Documentos Gubernamentales de Bolivia
FASE 9 - Sites Reales + Parsers Avanzados + Delta-Update
"""

from .sites import (
    TCPScraper,
    TSJScraper,
    ContraloriaScraper,
    ASFIScraper,
    SINScraper,
)

from .core import (
    BaseScraper,
    PDFParser,
    DeltaUpdateManager,
)

__version__ = "9.0.0"

__all__ = [
    'TCPScraper',
    'TSJScraper',
    'ContraloriaScraper',
    'ASFIScraper',
    'SINScraper',
    'BaseScraper',
    'PDFParser',
    'DeltaUpdateManager',
]

# Mapa de scrapers disponibles
SCRAPERS = {
    'tcp': TCPScraper,
    'tsj': TSJScraper,
    'contraloria': ContraloriaScraper,
    'asfi': ASFIScraper,
    'sin': SINScraper,
}

# Nombres completos de sitios
SITE_NAMES = {
    'tcp': 'Tribunal Constitucional Plurinacional',
    'tsj': 'Tribunal Supremo de Justicia',
    'contraloria': 'Contraloría General del Estado',
    'asfi': 'Autoridad de Supervisión del Sistema Financiero',
    'sin': 'Servicio de Impuestos Nacionales',
}


def get_scraper(site_name: str, outputs_dir: str = "outputs"):
    """
    Factory function para obtener un scraper

    Args:
        site_name: Nombre del sitio (tcp, tsj, etc.)
        outputs_dir: Directorio de salidas

    Returns:
        Instancia del scraper

    Raises:
        ValueError: Si el sitio no existe
    """
    if site_name not in SCRAPERS:
        raise ValueError(f"Sitio '{site_name}' no reconocido. Opciones: {list(SCRAPERS.keys())}")

    return SCRAPERS[site_name](outputs_dir=outputs_dir)


def list_sites():
    """
    Lista todos los sitios disponibles

    Returns:
        Dict con sitios y sus nombres completos
    """
    return SITE_NAMES.copy()
