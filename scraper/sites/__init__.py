"""
Scrapers específicos por sitio gubernamental
Cada scraper implementa lógica especializada para su fuente
"""

from .tcp_jurisprudencia_scraper import TCPJurisprudenciaScraper

__all__ = ['TCPJurisprudenciaScraper']
