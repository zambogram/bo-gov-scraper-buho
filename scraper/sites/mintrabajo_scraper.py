"""Scraper MinTrabajo - SCRAPING REAL de resoluciones ministeriales laborales"""
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging
from datetime import datetime
import re
import requests
from bs4 import BeautifulSoup
from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)

class MinTrabajoScraper(BaseScraper):
    def __init__(self):
        super().__init__('mintrabajo')
        logger.info(f"Inicializado scraper para {self.config.nombre}")

    def listar_documentos(self, limite: Optional[int] = None, modo: str = "delta", pagina: int = 1) -> List[Dict[str, Any]]:
        logger.info(f"Listando documentos de {self.site_id} - modo: {modo}, página: {pagina}")
        try:
            docs = self._scrape_real(pagina, limite)
            if docs:
                logger.info(f"✓ Scraping REAL: {len(docs)} resoluciones MinTrabajo")
                return docs
        except Exception as e:
            logger.warning(f"⚠ Scraping falló: {e}")
        logger.error("✗ No se pudo obtener datos de MinTrabajo")
        return []

    def _scrape_real(self, pagina: int, limite: Optional[int]) -> List[Dict[str, Any]]:
        docs = []
        url = f"{self.config.url_search}?pag={pagina}"
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            for enlace in soup.find_all('a', href=lambda x: x and '.pdf' in str(x).lower())[:limite or 100]:
                doc = self._extraer_doc(enlace)
                if doc:
                    docs.append(doc)
        except Exception as e:
            logger.error(f"Error: {e}")
        return docs[:limite] if limite else docs

    def _extraer_doc(self, enlace) -> Optional[Dict[str, Any]]:
        href = enlace.get('href', '')
        texto = enlace.get_text(strip=True)
        if not href:
            return None
        url_pdf = href if href.startswith('http') else f"{self.config.url_base}{href}" if href.startswith('/') else f"{self.config.url_base}/{href}"
        numero = None
        match = re.search(r'(\d+/\d{4})|RM\s*(\d+)', texto + href, re.IGNORECASE)
        if match:
            numero = match.group(1) or match.group(2)
        año = datetime.now().year
        match_año = re.search(r'(20\d{2})', texto + href)
        if match_año:
            año = int(match_año.group(1))
        tipo = 'Resolución Ministerial'
        if 'bi-ministerial' in texto.lower():
            tipo = 'Resolución Bi-Ministerial'
        elif 'reglamento' in texto.lower():
            tipo = 'Reglamento Laboral'
        id_doc = f"mintrabajo_rm_{numero.replace('/', '_') if numero else hash(url_pdf) % 100000}"
        return {
            'id_documento': id_doc,
            'tipo_documento': tipo,
            'numero_norma': numero or 'S/N',
            'anio': año,
            'fecha': f"{año}-01-01",
            'titulo': texto[:200] if texto else f"{tipo} MinTrabajo {numero}",
            'url': url_pdf,
            'sumilla': f"{tipo} - Normativa laboral y previsión social",
            'metadata_extra': {'entidad': 'MinTrabajo', 'area': 'laboral', 'metodo_scraping': 'real'}
        }

    def descargar_pdf(self, url: str, ruta_destino: Path) -> bool:
        try:
            response = self.session.get(url, timeout=60, stream=True)
            response.raise_for_status()
            ruta_destino.parent.mkdir(parents=True, exist_ok=True)
            with open(ruta_destino, 'wb') as f:
                for chunk in response.iter_content(8192):
                    if chunk:
                        f.write(chunk)
            return ruta_destino.stat().st_size > 0
        except Exception as e:
            logger.error(f"✗ Error: {e}")
            return False
