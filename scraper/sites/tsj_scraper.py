"""
Scraper para Tribunal Supremo de Justicia (TSJ) - SCRAPING REAL
Autos Supremos: Civil, Penal, Laboral, Contencioso, Familiar
"""
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging
from datetime import datetime
import re
import requests
from bs4 import BeautifulSoup

from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class TSJScraper(BaseScraper):
    """Scraper para TSJ con scraping histórico real"""

    def __init__(self):
        super().__init__('tsj')
        logger.info(f"Inicializado scraper para {self.config.nombre}")
        self.materias = ['Civil', 'Penal', 'Laboral', 'Contencioso Administrativo', 'Familiar']

    def listar_documentos(self, limite: Optional[int] = None, modo: str = "delta", pagina: int = 1) -> List[Dict[str, Any]]:
        """Listar autos supremos con scraping REAL"""
        logger.info(f"Listando documentos de {self.site_id} - modo: {modo}, página: {pagina}")
        
        try:
            documentos = self._scrape_real_tsj(pagina, limite)
            if documentos:
                logger.info(f"✓ Scraping REAL: {len(documentos)} autos supremos")
                return documentos
        except Exception as e:
            logger.warning(f"⚠ Scraping real falló: {e}")
        
        logger.error("✗ No se pudo obtener datos reales del TSJ")
        return []

    def _scrape_real_tsj(self, pagina: int, limite: Optional[int]) -> List[Dict[str, Any]]:
        """Scraping REAL del TSJ"""
        documentos = []
        urls = [f"{self.config.url_search}?page={pagina}", f"{self.config.url_base}/jurisprudencia?page={pagina}"]
        
        for url in urls:
            try:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Buscar enlaces a PDFs
                enlaces = soup.find_all('a', href=lambda x: x and '.pdf' in x.lower())
                for enlace in enlaces[:limite if limite else 100]:
                    doc = self._extraer_auto(enlace)
                    if doc:
                        documentos.append(doc)
                
                if documentos:
                    break
            except:
                continue
        
        return documentos[:limite] if limite else documentos

    def _extraer_auto(self, enlace) -> Optional[Dict[str, Any]]:
        """Extraer auto supremo"""
        href = enlace.get('href', '')
        texto = enlace.get_text(strip=True)
        
        if not href:
            return None
        
        url_pdf = href if href.startswith('http') else f"{self.config.url_base}{href}" if href.startswith('/') else f"{self.config.url_base}/{href}"
        
        # Extraer número
        numero = None
        match = re.search(r'(\d+/\d{4})|as-(\d+)-(\d{4})', texto + href, re.IGNORECASE)
        if match:
            numero = match.group(1) if match.group(1) else f"{match.group(2)}/{match.group(3)}"
        
        # Extraer año
        año = datetime.now().year
        match_año = re.search(r'(20\d{2})', texto + href)
        if match_año:
            año = int(match_año.group(1))
        
        # Detectar materia
        materia = 'Civil'
        for m in self.materias:
            if m.lower() in texto.lower():
                materia = m
                break
        
        id_doc = f"tsj_as_{numero.replace('/', '_')}" if numero else f"tsj_as_{hash(url_pdf) % 100000}"
        
        return {
            'id_documento': id_doc,
            'tipo_documento': 'Auto Supremo',
            'numero_norma': numero or 'S/N',
            'anio': año,
            'fecha': f"{año}-01-01",
            'titulo': texto[:200] if texto else f"Auto Supremo {numero}",
            'url': url_pdf,
            'sumilla': f"Auto Supremo - Materia {materia}",
            'metadata_extra': {'materia': materia, 'tribunal': 'TSJ', 'metodo_scraping': 'real'}
        }

    def descargar_pdf(self, url: str, ruta_destino: Path) -> bool:
        """Descargar PDF REAL"""
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
            logger.error(f"✗ Error descargando: {e}")
            return False
