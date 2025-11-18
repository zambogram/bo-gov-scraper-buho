"""
Scraper para Gaceta Oficial de Bolivia
FUENTE OFICIAL del Estado Plurinacional de Bolivia
"""
from typing import List, Optional, Dict, Any
from pathlib import Path
import time
import re
import logging
from bs4 import BeautifulSoup
from datetime import datetime

from ..base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class GacetaOficialScraper(BaseScraper):
    """
    Scraper para Gaceta Oficial de Bolivia
    FUENTE OFICIAL del Estado Plurinacional
    """

    def __init__(self):
        super().__init__('gaceta_oficial')
        logger.info(f"Inicializado scraper para {self.config.nombre}")

        # Headers especiales para acceso
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        })

    def listar_documentos(
        self,
        limite: Optional[int] = None,
        modo: str = "delta",
        pagina: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Scrapear leyes de Gaceta Oficial

        Args:
            limite: Número máximo de documentos
            modo: 'full' o 'delta'
            pagina: Número de página

        Returns:
            Lista de diccionarios con metadata de documentos
        """
        logger.info(f"Listando documentos de {self.site_id} - modo: {modo}, página: {pagina}")

        documentos = []

        try:
            # URL principal de normas
            url = self.config.url_search

            logger.info(f"🔍 Accediendo a Gaceta Oficial: {url}")

            # Esperar entre requests (respeto al servidor)
            time.sleep(2)

            response = self.session.get(url, timeout=30)
            logger.info(f"Status: {response.status_code}")

            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')

                # La Gaceta usa una estructura específica
                # Buscar elementos que contengan leyes/decretos

                # Estrategia 1: Buscar enlaces con fechas
                enlaces = soup.find_all('a', href=True)

                for enlace in enlaces:
                    if len(documentos) >= (limite or float('inf')):
                        break

                    href = enlace['href']
                    texto = enlace.get_text(strip=True)

                    # Filtrar solo enlaces relevantes (con fechas o números de ley)
                    if re.search(r'(LEY|DECRETO|RESOLU|20\d{2})', texto, re.I):

                        # Construir URL completa
                        if not href.startswith('http'):
                            if href.startswith('/'):
                                url_pdf = f"{self.config.url_base}{href}"
                            else:
                                url_pdf = f"{self.config.url_base}/{href}"
                        else:
                            url_pdf = href

                        # Extraer tipo de documento
                        tipo_doc = 'Documento Legal'
                        if 'ley' in texto.lower():
                            tipo_doc = 'Ley'
                        elif 'decreto' in texto.lower():
                            tipo_doc = 'Decreto Supremo'
                        elif 'resolu' in texto.lower():
                            tipo_doc = 'Resolución'

                        # Extraer número de norma
                        numero_norma = None
                        match_numero = re.search(r'N[°º]?\s*(\d+)', texto, re.I)
                        if match_numero:
                            numero_norma = match_numero.group(1)

                        # Extraer año
                        año = datetime.now().year
                        match_año = re.search(r'(20\d{2})', texto)
                        if match_año:
                            año = int(match_año.group(1))

                        # Crear ID único
                        if numero_norma:
                            id_doc = f"gaceta_{tipo_doc.lower().replace(' ', '_')}_{numero_norma}_{año}"
                        else:
                            import hashlib
                            hash_url = hashlib.md5(url_pdf.encode()).hexdigest()[:8]
                            id_doc = f"gaceta_{tipo_doc.lower().replace(' ', '_')}_{hash_url}"

                        doc = {
                            'id_documento': id_doc,
                            'tipo_documento': tipo_doc,
                            'numero_norma': numero_norma or 'S/N',
                            'anio': año,
                            'fecha': f"{año}-01-01",
                            'titulo': texto[:200],
                            'url': url_pdf,
                            'sumilla': f"{tipo_doc} de la Gaceta Oficial de Bolivia",
                            'metadata_extra': {
                                "fuente_oficial": "Gaceta Oficial de Bolivia",
                                "verificable": True,
                                "metodo_scraping": "real"
                            }
                        }

                        documentos.append(doc)

                logger.info(f"✅ Gaceta: {len(documentos)} documentos encontrados")
            else:
                logger.warning(f"⚠️ Gaceta retornó {response.status_code}")

            return documentos

        except Exception as e:
            logger.error(f"❌ Error en Gaceta: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []

    def descargar_pdf(self, url: str, ruta_destino: Path) -> bool:
        """
        Descargar PDF con rate limiting

        Args:
            url: URL del PDF
            ruta_destino: Ruta local donde guardar

        Returns:
            True si se descargó correctamente
        """
        logger.info(f"Descargando PDF desde: {url}")

        # Respetar servidor (rate limiting)
        time.sleep(1)

        try:
            response = self.session.get(
                url,
                timeout=60,
                stream=True,
                headers={'User-Agent': 'Mozilla/5.0 (compatible; BUHO-Scraper/1.0)'}
            )
            response.raise_for_status()

            ruta_destino.parent.mkdir(parents=True, exist_ok=True)

            with open(ruta_destino, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            if ruta_destino.stat().st_size == 0:
                logger.error(f"✗ Archivo descargado está vacío: {url}")
                return False

            logger.info(f"✓ PDF descargado: {ruta_destino.name} ({ruta_destino.stat().st_size} bytes)")
            return True

        except Exception as e:
            logger.error(f"✗ Error descargando PDF: {e}")
            return False
