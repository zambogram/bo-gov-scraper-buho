"""
Scraper para Gaceta Oficial de Bolivia
FUENTE OFICIAL del Estado Plurinacional de Bolivia

COBERTURA COMPLETA:
- /normas/listadonor/10: Leyes
- /normas/listadonor/11: Decretos Supremos
- /normas/listadonor/16: Otras normas
- /normas/listadonordes/0: Todas las normas
Con paginación automática y deduplicación
"""
from typing import List, Optional, Dict, Any, Set
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

    Cubre múltiples fuentes de datos:
    - Leyes (código 10)
    - Decretos Supremos (código 11)
    - Otras normas (código 16)
    - Listado general (listadonordes/0)
    """

    # Fuentes de datos disponibles
    FUENTES_NORMAS = [
        {'codigo': 10, 'nombre': 'Leyes', 'url_template': '/normas/listadonor/10'},
        {'codigo': 11, 'nombre': 'Decretos Supremos', 'url_template': '/normas/listadonor/11'},
        {'codigo': 16, 'nombre': 'Otras Normas', 'url_template': '/normas/listadonor/16'},
        {'codigo': 0, 'nombre': 'Listado General', 'url_template': '/normas/listadonordes/0'},
    ]

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
        Scrapear leyes de Gaceta Oficial desde TODAS las fuentes disponibles

        Args:
            limite: Número máximo de documentos totales
            modo: 'full' o 'delta'
            pagina: Número de página inicial (para cada fuente)

        Returns:
            Lista de diccionarios con metadata de documentos (deduplicados)
        """
        logger.info(f"Listando documentos de {self.site_id} - modo: {modo}")
        logger.info(f"📚 Fuentes configuradas: {len(self.FUENTES_NORMAS)}")

        # Conjunto para deduplicación (usamos PDF ID como clave)
        documentos_unicos: Dict[str, Dict[str, Any]] = {}

        # Procesar cada fuente
        for fuente in self.FUENTES_NORMAS:
            if limite and len(documentos_unicos) >= limite:
                logger.info(f"⚠️ Límite alcanzado ({limite}), omitiendo fuente {fuente['nombre']}")
                break

            logger.info(f"\n{'='*60}")
            logger.info(f"📋 Procesando fuente: {fuente['nombre']} (código {fuente['codigo']})")
            logger.info(f"{'='*60}")

            docs_desde_fuente = self._listar_desde_fuente(
                fuente=fuente,
                limite_fuente=limite - len(documentos_unicos) if limite else None,
                max_paginas=10  # Límite de seguridad
            )

            # Agregar documentos con deduplicación
            nuevos = 0
            duplicados = 0

            for doc in docs_desde_fuente:
                pdf_id = doc['metadata_extra']['pdf_id']

                if pdf_id not in documentos_unicos:
                    documentos_unicos[pdf_id] = doc
                    nuevos += 1
                else:
                    duplicados += 1
                    logger.debug(f"   ⊙ Duplicado: PDF ID {pdf_id} (ya incluido)")

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
        limite_fuente: Optional[int] = None,
        max_paginas: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Listar documentos desde una fuente específica con paginación

        Args:
            fuente: Diccionario con info de la fuente (codigo, nombre, url_template)
            limite_fuente: Límite de documentos para esta fuente
            max_paginas: Máximo de páginas a scrapear

        Returns:
            Lista de documentos de esta fuente
        """
        documentos = []
        pagina = 1

        while pagina <= max_paginas:
            # Construir URL con paginación
            if pagina == 1:
                url = f"{self.config.url_base}{fuente['url_template']}"
            else:
                url = f"{self.config.url_base}{fuente['url_template']}/page:{pagina}"

            logger.info(f"   📄 Página {pagina}: {url}")

            try:
                # Esperar entre requests
                time.sleep(2)

                response = self.session.get(url, timeout=60)

                if response.status_code != 200:
                    logger.warning(f"   ⚠️ Status {response.status_code}, deteniendo paginación")
                    break

                soup = BeautifulSoup(response.content, 'html.parser')

                # Buscar cards con información de normas
                cards_con_info = []
                all_cards = soup.find_all('div', class_=re.compile(r'card'))

                for card in all_cards:
                    # Verificar que tenga card-body (los cards con info real lo tienen)
                    if card.find('div', class_='card-body'):
                        cards_con_info.append(card)

                logger.info(f"      Cards con información: {len(cards_con_info)}")

                if len(cards_con_info) == 0:
                    logger.info(f"   ✓ No hay más documentos en página {pagina}")
                    break

                # Procesar cada card
                docs_en_pagina = 0
                for card in cards_con_info:
                    if limite_fuente and len(documentos) >= limite_fuente:
                        logger.info(f"   ⚠️ Límite de fuente alcanzado ({limite_fuente})")
                        return documentos

                    doc = self._extraer_documento_de_card(card, fuente['nombre'])

                    if doc:
                        documentos.append(doc)
                        docs_en_pagina += 1

                logger.info(f"      ✓ {docs_en_pagina} documentos extraídos")

                # Si no encontramos documentos, terminamos
                if docs_en_pagina == 0:
                    logger.info(f"   ✓ No hay más documentos útiles")
                    break

                pagina += 1

            except Exception as e:
                logger.error(f"   ❌ Error en página {pagina}: {e}")
                break

        logger.info(f"   📊 Total desde {fuente['nombre']}: {len(documentos)} documentos")
        return documentos

    def _extraer_documento_de_card(self, card: BeautifulSoup, fuente_nombre: str) -> Optional[Dict[str, Any]]:
        """
        Extraer información de un card individual

        Args:
            card: BeautifulSoup element del card
            fuente_nombre: Nombre de la fuente (para metadata)

        Returns:
            Diccionario con metadata del documento o None si no se puede extraer
        """
        try:
            # 1. Buscar enlace de descarga PDF
            pdf_link = card.find_parent().find('a', href=lambda x: x and '/normas/descargarNrms/' in x) if card.parent else None

            # Si no está en el padre, buscar en hermanos
            if not pdf_link:
                parent = card.parent
                if parent:
                    for sibling in parent.find_all('a', href=lambda x: x and '/normas/descargarNrms/' in x):
                        pdf_link = sibling
                        break

            if not pdf_link:
                logger.debug(f"      ⊗ Card sin enlace PDF, omitiendo")
                return None

            # 2. Extraer ID del PDF
            pdf_id = pdf_link['href'].split('/')[-1]
            url_pdf = f"{self.config.url_base}{pdf_link['href']}"

            # 3. Extraer información del card-body
            card_body = card.find('div', class_='card-body')
            if not card_body:
                logger.debug(f"      ⊗ Card sin body, omitiendo")
                return None

            texto_completo = card_body.get_text(separator=' | ', strip=True)

            # 4. Extraer tipo y número de norma desde el <h6>
            h6 = card_body.find('h6')
            tipo_doc = 'Documento Legal'
            numero_norma = None
            titulo = "Documento"

            if h6:
                titulo_h6 = h6.get_text(strip=True)
                titulo = titulo_h6  # Usar como título base

                match_ley = re.search(r'Ley N[°º]?\s*(\d+)', titulo_h6, re.I)
                match_decreto = re.search(r'Decreto Supremo N[°º]?\s*(\d+)', titulo_h6, re.I)
                match_resolucion = re.search(r'Resolución.*?N[°º]?\s*(\d+)', titulo_h6, re.I)

                if match_ley:
                    tipo_doc = 'Ley'
                    numero_norma = match_ley.group(1)
                elif match_decreto:
                    tipo_doc = 'Decreto Supremo'
                    numero_norma = match_decreto.group(1)
                elif match_resolucion:
                    tipo_doc = 'Resolución'
                    numero_norma = match_resolucion.group(1)

            # 5. Extraer fecha de publicación
            fecha = None
            match_fecha = re.search(r'Fecha de Publicación:\s*(\d{4}-\d{2}-\d{2})', texto_completo)
            if match_fecha:
                fecha = match_fecha.group(1)
            else:
                # Formato alternativo: "07 DE NOVIEMBRE DE 2025"
                match_fecha2 = re.search(r'(\d{1,2})\s+DE\s+([A-Z]+)\s+DE\s+(\d{4})', texto_completo, re.I)
                if match_fecha2:
                    meses = {
                        'ENERO': '01', 'FEBRERO': '02', 'MARZO': '03', 'ABRIL': '04',
                        'MAYO': '05', 'JUNIO': '06', 'JULIO': '07', 'AGOSTO': '08',
                        'SEPTIEMBRE': '09', 'OCTUBRE': '10', 'NOVIEMBRE': '11', 'DICIEMBRE': '12'
                    }
                    dia = match_fecha2.group(1).zfill(2)
                    mes = meses.get(match_fecha2.group(2).upper(), '01')
                    anio = match_fecha2.group(3)
                    fecha = f'{anio}-{mes}-{dia}'

            # Si no hay fecha, usar fecha actual
            if not fecha:
                fecha = datetime.now().strftime('%Y-%m-%d')

            # Extraer año
            año = int(fecha.split('-')[0]) if fecha else datetime.now().year

            # 6. Extraer sumilla/contenido
            sumilla = None
            contentpane = card_body.find('div', class_='contentpaneopen')
            if contentpane:
                sumilla_texto = contentpane.get_text(strip=True)
                # Remover la fecha del inicio si está
                sumilla_texto = re.sub(r'^\d{1,2}\s+DE\s+[A-Z]+\s+DE\s+\d{4}\s*\.-\s*', '', sumilla_texto, flags=re.I)
                sumilla = sumilla_texto[:300]  # Limitar longitud

            if not sumilla:
                # Buscar cualquier párrafo con contenido
                paragraphs = card_body.find_all('p')
                for p in paragraphs:
                    text = p.get_text(strip=True)
                    if len(text) > 20 and 'Publicado en edición' not in text:
                        sumilla = text[:300]
                        break

            if not sumilla:
                sumilla = f"{tipo_doc} de la Gaceta Oficial de Bolivia"

            # 7. Crear ID único
            if numero_norma:
                id_doc = f"gaceta_{tipo_doc.lower().replace(' ', '_')}_{numero_norma}_{año}"
            else:
                id_doc = f"gaceta_{tipo_doc.lower().replace(' ', '_')}_{pdf_id}"

            # 8. Construir documento
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
                    "pdf_id": pdf_id,
                    "fuente_listado": fuente_nombre
                }
            }

            logger.debug(f"      ✓ {tipo_doc} N° {numero_norma} - PDF {pdf_id}")
            return doc

        except Exception as e:
            logger.warning(f"      ⚠️ Error extrayendo card: {e}")
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
