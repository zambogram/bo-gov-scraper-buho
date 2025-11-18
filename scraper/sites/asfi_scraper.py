"""
Scraper para ASFI (Autoridad de Supervisión del Sistema Financiero)
FUENTE OFICIAL de normativa financiera de Bolivia

COBERTURA COMPLETA:
- /pb/normativa-nacional: Leyes del sistema financiero
- /pb/reglamentos-vigentes: Reglamentos internos de ASFI
- /la/normativa-internacional: Normativa internacional
- /pb/reglamentos-internos-fondos-inversion: Reglamentos de fondos
"""
from typing import List, Optional, Dict, Any
from pathlib import Path
import time
import re
import logging
from bs4 import BeautifulSoup
from datetime import datetime

from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class ASFIScraper(BaseScraper):
    """
    Scraper para ASFI de Bolivia
    FUENTE OFICIAL de normativa del sistema financiero

    Cubre múltiples fuentes de datos:
    - Normativa Nacional (Leyes)
    - Reglamentos Vigentes
    - Normativa Internacional
    - Reglamentos de Fondos de Inversión
    """

    def __init__(self):
        super().__init__('asfi')
        logger.info(f"Inicializado scraper para {self.config.nombre}")

        # Obtener fuentes de normativa desde config
        self.fuentes_normativa = self.config.metadatos.get('fuentes_normativa', [])

        if not self.fuentes_normativa:
            # Fallback: definir fuentes por defecto
            self.fuentes_normativa = [
                {
                    'nombre': 'Normativa Nacional (Leyes)',
                    'url': '/pb/normativa-nacional',
                    'tipo_default': 'Ley'
                },
                {
                    'nombre': 'Reglamentos Vigentes',
                    'url': '/pb/reglamentos-vigentes',
                    'tipo_default': 'Reglamento'
                },
            ]

        logger.info(f"📚 Fuentes configuradas: {len(self.fuentes_normativa)}")

    def listar_documentos(
        self,
        limite: Optional[int] = None,
        modo: str = "delta",
        pagina: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Scrapear normativa de ASFI desde TODAS las fuentes disponibles

        Args:
            limite: Número máximo de documentos totales
            modo: 'full' o 'delta'
            pagina: No se usa (ASFI no tiene paginación)

        Returns:
            Lista de diccionarios con metadata de documentos (deduplicados)
        """
        logger.info(f"Listando documentos de {self.site_id} - modo: {modo}")
        logger.info(f"📚 Fuentes configuradas: {len(self.fuentes_normativa)}")

        # Conjunto para deduplicación (usamos URL del PDF como clave)
        documentos_unicos: Dict[str, Dict[str, Any]] = {}

        # Procesar cada fuente
        for fuente in self.fuentes_normativa:
            if limite and len(documentos_unicos) >= limite:
                logger.info(f"⚠️ Límite alcanzado ({limite}), omitiendo fuente {fuente['nombre']}")
                break

            logger.info(f"\n{'='*60}")
            logger.info(f"📋 Procesando fuente: {fuente['nombre']}")
            logger.info(f"{'='*60}")

            docs_desde_fuente = self._listar_desde_fuente(
                fuente=fuente,
                limite_fuente=limite - len(documentos_unicos) if limite else None
            )

            # Agregar documentos con deduplicación
            nuevos = 0
            duplicados = 0

            for doc in docs_desde_fuente:
                url_pdf = doc['url']

                if url_pdf not in documentos_unicos:
                    documentos_unicos[url_pdf] = doc
                    nuevos += 1
                else:
                    duplicados += 1
                    logger.debug(f"   ⊙ Duplicado: {url_pdf} (ya incluido)")

            logger.info(f"✅ Fuente {fuente['nombre']}: {nuevos} nuevos, {duplicados} duplicados")

        # Convertir a lista
        documentos = list(documentos_unicos.values())

        logger.info(f"\n{'='*60}")
        logger.info(f"✅ TOTAL: {len(documentos)} documentos únicos recolectados")
        logger.info(f"{'='*60}")

        return documentos

    def _listar_desde_fuente(
        self,
        fuente: Dict[str, Any],
        limite_fuente: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Listar documentos desde una fuente específica de ASFI

        Args:
            fuente: Diccionario con info de la fuente (nombre, url, tipo_default)
            limite_fuente: Límite de documentos para esta fuente

        Returns:
            Lista de documentos de esta fuente
        """
        documentos = []
        url = f"{self.config.url_base}{fuente['url']}"

        logger.info(f"   📄 URL: {url}")

        try:
            # Esperar entre requests
            time.sleep(self.delay)

            response = self.session.get(url, timeout=30, verify=False)

            if response.status_code != 200:
                logger.warning(f"   ⚠️ Status {response.status_code}, saltando fuente")
                return []

            soup = BeautifulSoup(response.content, 'html.parser')

            # Buscar tabla con normativa
            tabla = soup.find('table')

            if not tabla:
                logger.warning(f"   ⚠️ No se encontró tabla en la página")
                # Intentar buscar enlaces PDF directamente
                enlaces_pdf = soup.find_all('a', href=lambda x: x and '.pdf' in x.lower())
                logger.info(f"      Enlaces PDF directos: {len(enlaces_pdf)}")

                for enlace in enlaces_pdf:
                    if limite_fuente and len(documentos) >= limite_fuente:
                        break

                    doc = self._extraer_documento_de_enlace(enlace, fuente)
                    if doc:
                        documentos.append(doc)

                return documentos

            # Procesar filas de la tabla
            filas = tabla.find_all('tr')
            logger.info(f"      Filas de tabla encontradas: {len(filas)}")

            # Saltar encabezado (primera fila)
            filas_datos = filas[1:] if len(filas) > 1 else filas

            docs_en_fuente = 0
            for fila in filas_datos:
                if limite_fuente and len(documentos) >= limite_fuente:
                    logger.info(f"   ⚠️ Límite de fuente alcanzado ({limite_fuente})")
                    break

                doc = self._extraer_documento_de_fila(fila, fuente)

                if doc:
                    documentos.append(doc)
                    docs_en_fuente += 1

            logger.info(f"      ✓ {docs_en_fuente} documentos extraídos")

        except Exception as e:
            logger.error(f"   ❌ Error procesando fuente: {e}")

        logger.info(f"   📊 Total desde {fuente['nombre']}: {len(documentos)} documentos")
        return documentos

    def _extraer_documento_de_fila(
        self,
        fila: BeautifulSoup,
        fuente: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Extraer información de una fila de tabla

        Args:
            fila: BeautifulSoup element de la fila <tr>
            fuente: Información de la fuente (para tipo_default)

        Returns:
            Diccionario con metadata del documento o None si no se puede extraer
        """
        try:
            # Buscar enlace PDF en la fila
            enlace_pdf = fila.find('a', href=lambda x: x and '.pdf' in x.lower())

            if not enlace_pdf:
                logger.debug(f"      ⊗ Fila sin enlace PDF, omitiendo")
                return None

            # Obtener todas las celdas de la fila
            celdas = fila.find_all(['td', 'th'])

            if len(celdas) == 0:
                logger.debug(f"      ⊗ Fila sin celdas, omitiendo")
                return None

            # Extraer texto de todas las celdas (concatenado)
            textos_celdas = [celda.get_text(strip=True) for celda in celdas]
            texto_completo = ' | '.join(textos_celdas)

            # URL del PDF
            href = enlace_pdf.get('href', '')
            if href.startswith('http'):
                url_pdf = href
            elif href.startswith('/'):
                url_pdf = f"{self.config.url_base}{href}"
            else:
                url_pdf = f"{self.config.url_base}/{href}"

            # Extraer título (generalmente primera celda con texto significativo)
            titulo = textos_celdas[0] if textos_celdas else enlace_pdf.get_text(strip=True)

            # Si el título es muy corto, usar el texto completo
            if len(titulo) < 10 and len(textos_celdas) > 1:
                titulo = ' - '.join(textos_celdas[:2])

            # Extraer tipo de documento
            tipo_doc = fuente.get('tipo_default', 'Normativa')

            # Refinar tipo si encontramos palabras clave
            texto_lower = texto_completo.lower()
            if 'ley n' in texto_lower or 'ley nº' in texto_lower or 'ley no' in texto_lower:
                tipo_doc = 'Ley'
            elif 'reglamento' in texto_lower:
                tipo_doc = 'Reglamento'
            elif 'resolución administrativa' in texto_lower or 'ra n' in texto_lower:
                tipo_doc = 'Resolución Administrativa'
            elif 'circular' in texto_lower:
                tipo_doc = 'Circular'

            # Extraer número de norma
            numero_norma = None

            # Patrones comunes: "Ley N° 1670", "Ley Nº 1516", "RA 123/2024"
            match_ley = re.search(r'Ley\s+N[°º]?\s*(\d{3,4})', texto_completo, re.I)
            match_res = re.search(r'(?:RA|Resolución)\s+N[°º]?\s*(\d+/\d{4}|\d+)', texto_completo, re.I)
            match_generico = re.search(r'N[°º]\s*(\d{3,4})', texto_completo, re.I)

            if match_ley:
                numero_norma = match_ley.group(1)
            elif match_res:
                numero_norma = match_res.group(1)
            elif match_generico:
                numero_norma = match_generico.group(1)

            # Extraer fecha
            fecha = None

            # Patrón: "05 de noviembre de 2025", "10 de julio de 2023"
            match_fecha = re.search(
                r'(\d{1,2})\s+de\s+(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\s+de\s+(\d{4})',
                texto_completo,
                re.I
            )

            if match_fecha:
                meses = {
                    'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04',
                    'mayo': '05', 'junio': '06', 'julio': '07', 'agosto': '08',
                    'septiembre': '09', 'octubre': '10', 'noviembre': '11', 'diciembre': '12'
                }
                dia = match_fecha.group(1).zfill(2)
                mes = meses.get(match_fecha.group(2).lower(), '01')
                anio = match_fecha.group(3)
                fecha = f'{anio}-{mes}-{dia}'
            else:
                # Intentar extraer solo año
                match_anio = re.search(r'(20\d{2})', texto_completo)
                if match_anio:
                    fecha = f"{match_anio.group(1)}-01-01"

            # Si no hay fecha, usar fecha actual
            if not fecha:
                fecha = datetime.now().strftime('%Y-%m-%d')

            # Extraer año
            año = int(fecha.split('-')[0]) if fecha else datetime.now().year

            # Generar ID único
            if numero_norma:
                id_doc = f"asfi_{tipo_doc.lower().replace(' ', '_')}_{numero_norma.replace('/', '_')}"
            else:
                # Usar hash del URL como ID
                import hashlib
                hash_url = hashlib.md5(url_pdf.encode()).hexdigest()[:8]
                id_doc = f"asfi_{tipo_doc.lower().replace(' ', '_')}_{hash_url}"

            # Construir sumilla (descripción breve)
            sumilla = titulo[:300] if len(titulo) > 20 else f"{tipo_doc} - ASFI"

            # Construir documento
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
                    "fuente_oficial": "ASFI",
                    "verificable": True,
                    "metodo_scraping": "real",
                    "fuente_listado": fuente['nombre'],
                    "categoria_interna": fuente['url'].split('/')[-1]  # Ej: "normativa-nacional"
                }
            }

            logger.debug(f"      ✓ {tipo_doc} N° {numero_norma} - {titulo[:40]}")
            return doc

        except Exception as e:
            logger.warning(f"      ⚠️ Error extrayendo fila: {e}")
            return None

    def _extraer_documento_de_enlace(
        self,
        enlace: BeautifulSoup,
        fuente: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Extraer documento desde un enlace PDF directo (sin tabla)

        Args:
            enlace: BeautifulSoup element del enlace <a>
            fuente: Información de la fuente

        Returns:
            Diccionario con metadata o None
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

            # Tipo por defecto
            tipo_doc = fuente.get('tipo_default', 'Normativa')

            # Extraer número si está disponible
            numero_norma = None
            match = re.search(r'(\d{3,4})', texto + href)
            if match:
                numero_norma = match.group(1)

            # Extraer año
            año = datetime.now().year
            match_año = re.search(r'(20\d{2})', texto + href)
            if match_año:
                año = int(match_año.group(1))

            # ID único
            if numero_norma:
                id_doc = f"asfi_{tipo_doc.lower().replace(' ', '_')}_{numero_norma}"
            else:
                import hashlib
                hash_url = hashlib.md5(url_pdf.encode()).hexdigest()[:8]
                id_doc = f"asfi_{tipo_doc.lower().replace(' ', '_')}_{hash_url}"

            return {
                'id_documento': id_doc,
                'tipo_documento': tipo_doc,
                'numero_norma': numero_norma or 'S/N',
                'anio': año,
                'fecha': f"{año}-01-01",
                'titulo': texto[:200] if texto else f"{tipo_doc} ASFI",
                'url': url_pdf,
                'sumilla': f"{tipo_doc} - Supervisión del Sistema Financiero",
                'metadata_extra': {
                    "fuente_oficial": "ASFI",
                    "verificable": True,
                    "metodo_scraping": "real",
                    "fuente_listado": fuente['nombre']
                }
            }

        except Exception as e:
            logger.warning(f"      ⚠️ Error extrayendo enlace: {e}")
            return None

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

        # Usar el método de la clase base que ya tiene validación
        return self._download_file(url, ruta_destino, timeout=60, validar_pdf=True)
