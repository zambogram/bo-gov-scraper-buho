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

                # Buscar todos los cards que contienen documentos
                cards = soup.find_all('div', class_=re.compile(r'card'))

                logger.info(f"📋 Cards encontrados: {len(cards)}")

                # Procesar cada card
                for card in cards:
                    if limite and len(documentos) >= limite:
                        break

                    # Buscar enlace de descarga PDF
                    pdf_link = card.find('a', href=lambda x: x and '/normas/descargarNrms/' in x)

                    if not pdf_link:
                        continue

                    # Extraer ID del documento
                    pdf_id = pdf_link['href'].split('/')[-1]

                    # Construir URL completa del PDF
                    url_pdf = f"{self.config.url_base}{pdf_link['href']}"

                    # Extraer texto del card
                    texto_card = card.get_text(separator=' | ', strip=True)

                    # Extraer tipo y número de norma
                    tipo_doc = 'Documento Legal'
                    numero_norma = None

                    match_ley = re.search(r'Ley N[°º]?\s*(\d+)', texto_card, re.I)
                    match_decreto = re.search(r'Decreto Supremo N[°º]?\s*(\d+)', texto_card, re.I)
                    match_resolucion = re.search(r'Resolución.*?N[°º]?\s*(\d+)', texto_card, re.I)

                    if match_ley:
                        tipo_doc = 'Ley'
                        numero_norma = match_ley.group(1)
                    elif match_decreto:
                        tipo_doc = 'Decreto Supremo'
                        numero_norma = match_decreto.group(1)
                    elif match_resolucion:
                        tipo_doc = 'Resolución'
                        numero_norma = match_resolucion.group(1)

                    # Extraer fecha de publicación
                    fecha = None
                    match_fecha = re.search(r'Fecha de Publicación:\s*(\d{4}-\d{2}-\d{2})', texto_card)
                    if match_fecha:
                        fecha = match_fecha.group(1)
                    else:
                        # Formato alternativo: "07 DE NOVIEMBRE DE 2025"
                        match_fecha2 = re.search(r'(\d{2}) DE ([A-Z]+) DE (\d{4})', texto_card)
                        if match_fecha2:
                            meses = {
                                'ENERO': '01', 'FEBRERO': '02', 'MARZO': '03', 'ABRIL': '04',
                                'MAYO': '05', 'JUNIO': '06', 'JULIO': '07', 'AGOSTO': '08',
                                'SEPTIEMBRE': '09', 'OCTUBRE': '10', 'NOVIEMBRE': '11', 'DICIEMBRE': '12'
                            }
                            dia = match_fecha2.group(1).zfill(2)
                            mes = meses.get(match_fecha2.group(2), '01')
                            anio = match_fecha2.group(3)
                            fecha = f'{anio}-{mes}-{dia}'

                    # Si no hay fecha, usar fecha actual
                    if not fecha:
                        fecha = datetime.now().strftime('%Y-%m-%d')

                    # Extraer año
                    año = int(fecha.split('-')[0]) if fecha else datetime.now().year

                    # Extraer sumilla/título
                    sumilla = None
                    match_sumilla = re.search(r'(\d{4})\s*\.-\s*\|?\s*(.+?)\s*\|?\s*Ver Norma', texto_card, re.DOTALL)
                    if match_sumilla:
                        sumilla = match_sumilla.group(2).strip()
                        # Limpiar saltos de línea y espacios múltiples
                        sumilla = re.sub(r'\s+', ' ', sumilla)
                        sumilla = sumilla[:300]  # Limitar longitud

                    if not sumilla:
                        sumilla = f"{tipo_doc} de la Gaceta Oficial de Bolivia"

                    # Crear ID único
                    if numero_norma:
                        id_doc = f"gaceta_{tipo_doc.lower().replace(' ', '_')}_{numero_norma}_{año}"
                    else:
                        id_doc = f"gaceta_{tipo_doc.lower().replace(' ', '_')}_{pdf_id}"

                    # Crear título
                    if numero_norma:
                        titulo = f"{tipo_doc} N° {numero_norma}"
                    else:
                        titulo = tipo_doc

                    doc = {
                        'id_documento': id_doc,
                        'tipo_documento': tipo_doc,
                        'numero_norma': numero_norma or 'S/N',
                        'anio': año,
                        'fecha': fecha,
                        'titulo': titulo,
                        'url': url_pdf,
                        'sumilla': sumilla,
                        'metadata_extra': {
                            "fuente_oficial": "Gaceta Oficial de Bolivia",
                            "verificable": True,
                            "metodo_scraping": "real",
                            "pdf_id": pdf_id
                        }
                    }

                    documentos.append(doc)
                    logger.debug(f"  ✓ {tipo_doc} N° {numero_norma} ({fecha})")

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
        Descargar PDF con validación y rate limiting

        Args:
            url: URL del PDF
            ruta_destino: Ruta local donde guardar

        Returns:
            True si se descargó correctamente un PDF válido
        """
        logger.info(f"Descargando PDF desde: {url}")

        # Respetar servidor (rate limiting)
        time.sleep(1)

        try:
            ruta_destino.parent.mkdir(parents=True, exist_ok=True)

            # Descargar
            response = self.session.get(url, timeout=60, stream=True)
            response.raise_for_status()

            # Verificar Content-Type
            content_type = response.headers.get('Content-Type', '')
            if 'text/html' in content_type:
                logger.warning(f"⚠️ La URL retorna HTML, no PDF: {url}")
                logger.warning(f"   Content-Type: {content_type}")
                return False

            # Leer contenido completo
            content = b''
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    content += chunk

            # Validar que sea PDF
            if not self._validar_pdf(content, url):
                return False

            # Guardar
            with open(ruta_destino, 'wb') as f:
                f.write(content)

            logger.info(f"✓ PDF descargado y validado: {ruta_destino.name} ({len(content)} bytes)")
            return True

        except Exception as e:
            logger.error(f"✗ Error descargando PDF: {e}")
            return False
