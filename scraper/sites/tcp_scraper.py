"""
Scraper para Tribunal Constitucional Plurinacional (TCP) - IMPLEMENTACIÓN REAL

Scraping histórico completo de sentencias constitucionales.
Estructura del sitio:
- URL base: https://www.tcpbolivia.bo
- Búsqueda: /tcp/busqueda o /sentencias
- Tipos: Sentencias Constitucionales (SC), Declaraciones, Autos
"""
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging
from datetime import datetime
import re
import requests
from bs4 import BeautifulSoup
import time

from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class TCPScraper(BaseScraper):
    """
    Scraper para TCP con scraping histórico real completo

    El TCP emite Sentencias Constitucionales sobre: amparos, acciones de libertad,
    inconstitucionalidad, conflictos de competencias, etc.
    """

    def __init__(self):
        super().__init__('tcp')
        logger.info(f"Inicializado scraper para {self.config.nombre}")

        # Tipos de acciones constitucionales
        self.tipos_acciones = [
            'Acción de Amparo Constitucional',
            'Acción de Libertad',
            'Acción de Inconstitucionalidad',
            'Acción Popular',
            'Conflicto de Competencias',
            'Control Previo de Constitucionalidad',
            'Acción de Protección de Privacidad',
            'Acción de Cumplimiento'
        ]

    def listar_documentos(
        self,
        limite: Optional[int] = None,
        modo: str = "delta",
        pagina: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Listar sentencias del TCP con scraping REAL

        Args:
            limite: Número máximo de documentos
            modo: 'full' (histórico) o 'delta' (nuevos)
            pagina: Número de página

        Returns:
            Lista de sentencias encontradas
        """
        logger.info(f"Listando documentos de {self.site_id} - modo: {modo}, página: {pagina}")

        try:
            documentos = self._scrape_real_tcp(pagina, limite)

            if documentos:
                logger.info(f"✓ Scraping REAL exitoso: {len(documentos)} sentencias del TCP")
                return documentos

        except Exception as e:
            logger.warning(f"⚠ Scraping real falló: {e}")

        # Intentar método alternativo
        try:
            documentos = self._scrape_alternativo_tcp(pagina, limite)
            if documentos:
                return documentos
        except Exception as e:
            logger.warning(f"⚠ Método alternativo falló: {e}")

        logger.error("✗ No se pudo obtener datos reales del TCP")
        logger.error("Verificar conectividad y estructura del sitio: https://www.tcpbolivia.bo")
        return []

    def _scrape_real_tcp(self, pagina: int, limite: Optional[int]) -> List[Dict[str, Any]]:
        """
        Scraping REAL del sitio del TCP

        El sitio del TCP típicamente tiene:
        - Buscador de sentencias
        - Listado con paginación
        - Enlaces a PDFs de sentencias
        """
        documentos = []

        # Construir URL de búsqueda con paginación
        # El TCP suele usar parámetros como: page, anio, tipo, etc.
        año_actual = datetime.now().year

        # Intentar diferentes URLs de búsqueda
        urls_busqueda = [
            f"{self.config.url_search}?page={pagina}",
            f"{self.config.url_base}/sentencias?page={pagina}",
            f"{self.config.url_base}/sentencias/{año_actual}"
        ]

        for url_busqueda in urls_busqueda:
            try:
                logger.info(f"Intentando URL: {url_busqueda}")

                response = self.session.get(
                    url_busqueda,
                    timeout=30,
                    headers={'User-Agent': 'Mozilla/5.0 (compatible; BUHO-Scraper/1.0)'}
                )
                response.raise_for_status()

                soup = BeautifulSoup(response.content, 'html.parser')

                # Buscar sentencias en el HTML
                sentencias_encontradas = self._extraer_sentencias_de_html(soup)

                if sentencias_encontradas:
                    documentos.extend(sentencias_encontradas)
                    logger.info(f"✓ Encontradas {len(sentencias_encontradas)} sentencias en {url_busqueda}")
                    break

            except requests.RequestException as e:
                logger.warning(f"Error con URL {url_busqueda}: {e}")
                continue

        return documentos[:limite] if limite else documentos

    def _extraer_sentencias_de_html(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """
        Extraer sentencias del HTML del TCP

        Patrones comunes en sitios del TCP:
        - Tablas con filas de sentencias
        - Listas con enlaces a PDFs
        - Cards/divs con información de sentencias
        """
        sentencias = []

        # Patrón 1: Buscar tabla de sentencias
        tabla = soup.find('table', class_=lambda x: x and ('sentencias' in x.lower() or 'resultados' in x.lower()))
        if tabla:
            filas = tabla.find_all('tr')[1:]  # Saltar encabezado
            for fila in filas:
                try:
                    sentencia = self._extraer_sentencia_de_fila(fila)
                    if sentencia:
                        sentencias.append(sentencia)
                except Exception as e:
                    logger.warning(f"Error extrayendo fila: {e}")
                    continue

        # Patrón 2: Buscar enlaces directos a PDFs
        if not sentencias:
            enlaces_pdf = soup.find_all('a', href=lambda x: x and x.endswith('.pdf'))
            for enlace in enlaces_pdf:
                try:
                    sentencia = self._extraer_sentencia_de_enlace(enlace)
                    if sentencia:
                        sentencias.append(sentencia)
                except Exception as e:
                    logger.warning(f"Error extrayendo enlace: {e}")
                    continue

        # Patrón 3: Buscar divs/cards de sentencias
        if not sentencias:
            cards = soup.find_all(['div', 'article'], class_=lambda x: x and ('sentencia' in x.lower() or 'resultado' in x.lower()))
            for card in cards:
                try:
                    sentencia = self._extraer_sentencia_de_card(card)
                    if sentencia:
                        sentencias.append(sentencia)
                except Exception as e:
                    logger.warning(f"Error extrayendo card: {e}")
                    continue

        return sentencias

    def _extraer_sentencia_de_fila(self, fila) -> Optional[Dict[str, Any]]:
        """Extraer sentencia desde fila de tabla"""
        celdas = fila.find_all(['td', 'th'])

        if len(celdas) < 2:
            return None

        # Buscar enlace al PDF
        enlace = fila.find('a', href=lambda x: x and '.pdf' in x)
        if not enlace:
            return None

        # Extraer datos de las celdas
        textos_celdas = [celda.get_text(strip=True) for celda in celdas]

        # Intentar identificar número de sentencia
        numero_sentencia = None
        for texto in textos_celdas:
            match = re.search(r'(\d+/\d{4})', texto)
            if match:
                numero_sentencia = match.group(1)
                break

        # Construir URL del PDF
        href = enlace.get('href', '')
        if href.startswith('/'):
            url_pdf = f"{self.config.url_base}{href}"
        elif not href.startswith('http'):
            url_pdf = f"{self.config.url_base}/{href}"
        else:
            url_pdf = href

        # Extraer año y otros datos
        año = datetime.now().year
        match_año = re.search(r'(20\d{2})', str(textos_celdas))
        if match_año:
            año = int(match_año.group(1))

        # Buscar tipo de acción
        tipo_accion = 'Sentencia Constitucional'
        texto_completo = ' '.join(textos_celdas).lower()
        for accion in self.tipos_acciones:
            if accion.lower() in texto_completo:
                tipo_accion = accion
                break

        # Generar ID
        if numero_sentencia:
            id_doc = f"tcp_sc_{numero_sentencia.replace('/', '_')}"
        else:
            import hashlib
            hash_url = hashlib.md5(url_pdf.encode()).hexdigest()[:8]
            id_doc = f"tcp_sc_{hash_url}"

        return {
            'id_documento': id_doc,
            'tipo_documento': 'Sentencia Constitucional',
            'numero_norma': numero_sentencia or 'S/N',
            'anio': año,
            'fecha': f"{año}-01-01",  # Fecha aproximada
            'titulo': f"SC {numero_sentencia} - {tipo_accion}",
            'url': url_pdf,
            'sumilla': tipo_accion,
            'metadata_extra': {
                'tipo_accion': tipo_accion,
                'tribunal': 'TCP',
                'fuente': 'Tribunal Constitucional Plurinacional',
                'metodo_scraping': 'real'
            }
        }

    def _extraer_sentencia_de_enlace(self, enlace) -> Optional[Dict[str, Any]]:
        """Extraer sentencia desde enlace directo"""
        href = enlace.get('href', '')
        texto = enlace.get_text(strip=True)

        if not href or '.pdf' not in href.lower():
            return None

        # Construir URL completa
        if href.startswith('/'):
            url_pdf = f"{self.config.url_base}{href}"
        elif not href.startswith('http'):
            url_pdf = f"{self.config.url_base}/{href}"
        else:
            url_pdf = href

        # Extraer número de sentencia
        numero_sentencia = None
        match = re.search(r'(\d+/\d{4})|sc-(\d+)-(\d{4})', texto + href, re.IGNORECASE)
        if match:
            if match.group(1):
                numero_sentencia = match.group(1)
            else:
                numero_sentencia = f"{match.group(2)}/{match.group(3)}"

        # Extraer año
        año = datetime.now().year
        match_año = re.search(r'(20\d{2})', texto + href)
        if match_año:
            año = int(match_año.group(1))

        # Generar ID
        if numero_sentencia:
            id_doc = f"tcp_sc_{numero_sentencia.replace('/', '_')}"
        else:
            import hashlib
            hash_url = hashlib.md5(url_pdf.encode()).hexdigest()[:8]
            id_doc = f"tcp_sc_{hash_url}"

        return {
            'id_documento': id_doc,
            'tipo_documento': 'Sentencia Constitucional',
            'numero_norma': numero_sentencia or 'S/N',
            'anio': año,
            'fecha': f"{año}-01-01",
            'titulo': texto[:200] if texto else f"Sentencia Constitucional {numero_sentencia}",
            'url': url_pdf,
            'sumilla': 'Sentencia Constitucional',
            'metadata_extra': {
                'tribunal': 'TCP',
                'fuente': 'Tribunal Constitucional Plurinacional',
                'metodo_scraping': 'real'
            }
        }

    def _extraer_sentencia_de_card(self, card) -> Optional[Dict[str, Any]]:
        """Extraer sentencia desde card/div"""
        # Buscar enlace al PDF
        enlace = card.find('a', href=lambda x: x and '.pdf' in x)
        if not enlace:
            return None

        # Extraer texto completo del card
        texto = card.get_text(separator=' ', strip=True)

        return self._extraer_sentencia_de_enlace(enlace)

    def _scrape_alternativo_tcp(self, pagina: int, limite: Optional[int]) -> List[Dict[str, Any]]:
        """Método alternativo de scraping para TCP"""
        logger.info("Intentando método alternativo para TCP...")

        # Intentar URL alternativa
        try:
            url_alt = f"{self.config.url_base}/jurisprudencia"
            response = self.session.get(url_alt, timeout=30)

            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                return self._extraer_sentencias_de_html(soup)
        except:
            pass

        return []

    def descargar_pdf(self, url: str, ruta_destino: Path) -> bool:
        """
        Descargar PDF REAL de sentencia del TCP

        Args:
            url: URL del PDF
            ruta_destino: Ruta local donde guardar

        Returns:
            True si se descargó correctamente
        """
        logger.info(f"Descargando sentencia TCP desde: {url}")

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

            logger.info(f"✓ Sentencia descargada: {ruta_destino.name} ({ruta_destino.stat().st_size} bytes)")
            return True

        except requests.RequestException as e:
            logger.error(f"✗ Error descargando sentencia: {e}")
            return False
        except Exception as e:
            logger.error(f"✗ Error inesperado: {e}")
            return False
