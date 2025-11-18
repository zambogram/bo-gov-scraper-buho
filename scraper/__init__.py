"""
Módulo de scraping para BÚHO.

Este paquete contiene todos los componentes necesarios para:
- Gestionar el catálogo de sitios
- Scrapear sitios estatales bolivianos
- Procesar documentos (PDF → texto)
- Extraer metadatos
- Segmentar en artículos/secciones
"""

__version__ = "1.0.0"
__author__ = "BÚHO LegalTech"

# Exportar componentes principales
from .catalog import CatalogManager, SiteInfo, load_catalog, get_site_info, list_all_sites

__all__ = [
    "CatalogManager",
    "SiteInfo",
    "load_catalog",
    "get_site_info",
    "list_all_sites",
]
