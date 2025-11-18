"""
Scraper para Gaceta Constitucional Plurinacional del TCP
FUENTE OFICIAL de jurisprudencia constitucional compilada

Scrapea los tomos anuales de la Gaceta Constitucional desde 2018 hasta el año actual.
"""
from typing import List, Optional, Dict, Any
from pathlib import Path
import re
import logging
from datetime import datetime
from bs4 import BeautifulSoup

from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class TCPGacetaScraper(BaseScraper):
    """
    Scraper para Gaceta Constitucional Plurinacional del TCP

    Scrapea tomos compilados de jurisprudencia constitucional por año.
    URL base: https://tcpbolivia.bo/gaceta{año}/
    """

    # Años disponibles de la Gaceta (desde 2018 hasta actual)
    AÑO_INICIO = 2018

    def __init__(self):
        super().__init__('tcp_gaceta')
        logger.info(f"Inicializado scraper para {self.config.nombre}")

        # Calcular año actual
        self.año_actual = datetime.now().year

        logger.info(f"📚 Rango de años: {self.AÑO_INICIO} - {self.año_actual}")

    def listar_documentos(
        self,
        limite: Optional[int] = None,
        modo: str = "delta",
        pagina: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Listar tomos de la Gaceta Constitucional por año

        Args:
            limite: Número máximo de documentos
            modo: 'full' o 'delta'
            pagina: No se usa (sin paginación)

        Returns:
            Lista de diccionarios con metadata de tomos
        """
        logger.info(f"Listando Gacetas Constitucionales del TCP - modo: {modo}")

        documentos = []

        # Iterar por años (desde el más reciente al más antiguo)
        for año in range(self.año_actual, self.AÑO_INICIO - 1, -1):
            if limite and len(documentos) >= limite:
                logger.info(f"⚠️ Límite alcanzado ({limite}), deteniendo")
                break

            logger.info(f"\n{'='*60}")
            logger.info(f"📅 Procesando Gaceta {año}")
            logger.info(f"{'='*60}")

            docs_año = self._listar_gaceta_año(año)

            # Agregar documentos encontrados
            for doc in docs_año:
                if limite and len(documentos) >= limite:
                    break
                documentos.append(doc)

            logger.info(f"   ✓ {len(docs_año)} tomos encontrados para {año}")

        logger.info(f"\n{'='*60}")
        logger.info(f"✅ TOTAL: {len(documentos)} tomos de Gaceta Constitucional")
        logger.info(f"{'='*60}")

        return documentos

    def _listar_gaceta_año(self, año: int) -> List[Dict[str, Any]]:
        """
        Listar tomos de la Gaceta para un año específico

        Args:
            año: Año de la gaceta (ej: 2018, 2019, etc.)

        Returns:
            Lista de documentos (tomos) encontrados
        """
        url = f"{self.config.url_base}/gaceta{año}/"

        logger.info(f"   📄 URL: {url}")

        documentos = []

        try:
            response = self.session.get(url, timeout=30, verify=False)

            if response.status_code != 200:
                logger.warning(f"   ⚠️ Status {response.status_code}, saltando año {año}")
                return []

            soup = BeautifulSoup(response.content, 'html.parser')

            # Buscar todos los enlaces a PDFs
            enlaces_pdf = soup.find_all('a', href=lambda x: x and '.pdf' in x.lower())

            logger.info(f"      Enlaces PDF encontrados: {len(enlaces_pdf)}")

            for enlace in enlaces_pdf:
                doc = self._extraer_tomo(enlace, año)
                if doc:
                    documentos.append(doc)

        except Exception as e:
            logger.error(f"   ❌ Error procesando año {año}: {e}")

        return documentos

    def _extraer_tomo(self, enlace, año: int) -> Optional[Dict[str, Any]]:
        """
        Extraer metadata de un tomo de la Gaceta

        Args:
            enlace: BeautifulSoup element del enlace <a>
            año: Año de la gaceta

        Returns:
            Diccionario con metadata del tomo o None
        """
        try:
            href = enlace.get('href', '')
            texto = enlace.get_text(strip=True)

            if not href:
                return None

            # Construir URL completa
            if href.startswith('http'):
                url_pdf = href
            elif href.startswith('/'):
                url_pdf = f"{self.config.url_base}{href}"
            else:
                url_pdf = f"{self.config.url_base}/{href}"

            # Extraer nombre del archivo desde la URL
            nombre_archivo = url_pdf.split('/')[-1]

            # Detectar tipo de documento
            tipo_doc = "Gaceta Constitucional Plurinacional"
            tomo = None

            # Patrones: TomoI2018.pdf, TomoII2018.pdf, guia2018.pdf
            if 'tomo' in nombre_archivo.lower():
                # Extraer número de tomo (I, II, III, IV, V, etc.)
                match_tomo = re.search(r'tomo\s*([IVX]+|[0-9]+)', nombre_archivo, re.I)
                if match_tomo:
                    tomo = match_tomo.group(1).upper()
                    tipo_doc = f"Gaceta Constitucional - Tomo {tomo}"
            elif 'guia' in nombre_archivo.lower():
                tipo_doc = "Gaceta Constitucional - Guía de Uso"
                tomo = "GUIA"
            elif 'primer' in nombre_archivo.lower() or '1er' in nombre_archivo.lower():
                tipo_doc = "Gaceta Constitucional - Primer Semestre"
                tomo = "1ER_SEM"
            elif 'segundo' in nombre_archivo.lower() or '2do' in nombre_archivo.lower():
                tipo_doc = "Gaceta Constitucional - Segundo Semestre"
                tomo = "2DO_SEM"

            # Generar ID único
            if tomo:
                id_doc = f"tcp_gaceta_{año}_tomo_{tomo.lower()}"
            else:
                # Usar hash del URL como fallback
                import hashlib
                hash_url = hashlib.md5(url_pdf.encode()).hexdigest()[:8]
                id_doc = f"tcp_gaceta_{año}_{hash_url}"

            # Construir título
            if tomo and tomo != "GUIA":
                titulo = f"Gaceta Constitucional Plurinacional {año} - Tomo {tomo}"
            elif tomo == "GUIA":
                titulo = f"Guía de Uso - Gaceta Constitucional {año}"
            else:
                titulo = f"Gaceta Constitucional Plurinacional {año}"

            # Sumilla
            sumilla = f"Compilación oficial de jurisprudencia constitucional del Tribunal Constitucional Plurinacional - Gestión {año}"
            if tomo and tomo != "GUIA":
                sumilla += f" (Tomo {tomo})"

            doc = {
                'id_documento': id_doc,
                'tipo_documento': tipo_doc,
                'numero_norma': f"{año}-{tomo}" if tomo else str(año),
                'anio': año,
                'fecha': f"{año}-01-01",  # Fecha aproximada (inicio del año)
                'titulo': titulo,
                'url': url_pdf,
                'sumilla': sumilla,
                'metadata_extra': {
                    "fuente_oficial": "TCP",
                    "tipo_publicacion": "Gaceta Constitucional Plurinacional",
                    "año_gaceta": año,
                    "tomo": tomo,
                    "verificable": True,
                    "metodo_scraping": "real",
                    "tribunal": "Tribunal Constitucional Plurinacional"
                }
            }

            logger.debug(f"      ✓ {tipo_doc} - {año} - {url_pdf.split('/')[-1]}")
            return doc

        except Exception as e:
            logger.warning(f"      ⚠️ Error extrayendo tomo: {e}")
            return None

    def descargar_pdf(self, url: str, ruta_destino: Path) -> bool:
        """
        Descargar PDF de tomo de la Gaceta con validación

        Args:
            url: URL del PDF
            ruta_destino: Ruta local donde guardar

        Returns:
            True si se descargó correctamente un PDF válido
        """
        logger.info(f"Descargando tomo de Gaceta desde: {url}")

        # Usar el método de la clase base que ya tiene validación
        return self._download_file(url, ruta_destino, timeout=120, validar_pdf=True)
