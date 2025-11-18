"""
Parser para dividir documentos legales en artículos y secciones
"""
import re
from typing import List, Dict, Tuple, Optional
import logging

from scraper.models import Articulo

logger = logging.getLogger(__name__)


class LegalParser:
    """Parser para documentos legales bolivianos"""

    # Patrones para identificar artículos
    PATRONES_ARTICULO = [
        r'^(?:ART[IÍ]CULO|ART\.|ARTICULO)\s+(\d+)[°º]?\.?\s*[-–—]?\s*(.*?)$',
        r'^Art[íi]culo\s+(\d+)[°º]?\.?\s*[-–—]?\s*(.*?)$',
        r'^(\d+)[°º]?\.?\s*[-–—]\s*(.*?)$',  # Más general
    ]

    # Patrones para secciones, capítulos, títulos
    PATRONES_ESTRUCTURA = [
        (r'^(CAPÍTULO|CAPITULO|CAP\.)\s+([IVX]+|\d+)\.?\s*[-–—]?\s*(.*?)$', 'capitulo'),
        (r'^(TÍTULO|TITULO|TÍT\.)\s+([IVX]+|\d+)\.?\s*[-–—]?\s*(.*?)$', 'titulo'),
        (r'^(SECCIÓN|SECCION|SECC\.)\s+([IVX]+|\d+)\.?\s*[-–—]?\s*(.*?)$', 'seccion'),
        (r'^(DISPOSICI[OÓ]N|DISPOSICION)\s+(FINAL|TRANSITORIA|ADICIONAL)\s*(.*?)$', 'disposicion'),
    ]

    def __init__(self):
        """Inicializar parser"""
        self.contador_articulos = 0

    def parsear_documento(self, id_documento: str, texto: str) -> List[Articulo]:
        """
        Parsear documento completo en artículos

        Args:
            id_documento: ID del documento
            texto: Texto completo del documento

        Returns:
            Lista de artículos encontrados
        """
        if not texto or not texto.strip():
            logger.warning(f"Texto vacío para documento {id_documento}")
            return []

        self.contador_articulos = 0
        articulos = []

        # Dividir en líneas
        lineas = texto.split('\n')

        # Estados para el parser
        articulo_actual = None
        contenido_actual = []
        tipo_actual = 'articulo'
        numero_actual = None
        titulo_actual = None

        for linea in lineas:
            linea = linea.strip()

            if not linea:
                continue

            # Verificar si es un artículo
            es_articulo, numero, titulo = self._es_articulo(linea)

            if es_articulo:
                # Guardar artículo anterior si existe
                if articulo_actual is not None:
                    articulo_actual.contenido = '\n'.join(contenido_actual).strip()
                    articulos.append(articulo_actual)

                # Crear nuevo artículo
                self.contador_articulos += 1
                articulo_actual = Articulo(
                    id_articulo=f"{id_documento}_art_{self.contador_articulos}",
                    id_documento=id_documento,
                    numero=numero,
                    titulo=titulo if titulo else None,
                    tipo_unidad='articulo'
                )
                contenido_actual = []
                continue

            # Verificar si es una estructura (capítulo, sección, etc.)
            es_estructura, tipo_estructura, numero_est, titulo_est = self._es_estructura(linea)

            if es_estructura:
                # Guardar artículo/sección anterior si existe
                if articulo_actual is not None:
                    articulo_actual.contenido = '\n'.join(contenido_actual).strip()
                    articulos.append(articulo_actual)

                # Crear nueva sección
                self.contador_articulos += 1
                articulo_actual = Articulo(
                    id_articulo=f"{id_documento}_{tipo_estructura}_{self.contador_articulos}",
                    id_documento=id_documento,
                    numero=numero_est,
                    titulo=titulo_est if titulo_est else None,
                    tipo_unidad=tipo_estructura
                )
                contenido_actual = []
                continue

            # Agregar línea al contenido actual
            if articulo_actual is not None:
                contenido_actual.append(linea)

        # Guardar último artículo
        if articulo_actual is not None:
            articulo_actual.contenido = '\n'.join(contenido_actual).strip()
            articulos.append(articulo_actual)

        # Si no se encontraron artículos, crear uno con todo el texto
        if not articulos:
            logger.info(f"No se encontraron artículos, creando artículo único para {id_documento}")
            articulos.append(Articulo(
                id_articulo=f"{id_documento}_art_1",
                id_documento=id_documento,
                numero="1",
                titulo="Documento completo",
                contenido=texto.strip(),
                tipo_unidad='documento'
            ))

        logger.info(f"Parseados {len(articulos)} artículos/secciones para {id_documento}")
        return articulos

    def _es_articulo(self, linea: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Verificar si una línea es un artículo

        Returns:
            (es_articulo, numero, titulo)
        """
        for patron in self.PATRONES_ARTICULO:
            match = re.match(patron, linea, re.IGNORECASE)
            if match:
                grupos = match.groups()
                numero = grupos[0] if len(grupos) > 0 else None
                titulo = grupos[1].strip() if len(grupos) > 1 and grupos[1] else None
                return True, numero, titulo

        return False, None, None

    def _es_estructura(self, linea: str) -> Tuple[bool, Optional[str], Optional[str], Optional[str]]:
        """
        Verificar si una línea es una estructura (capítulo, sección, etc.)

        Returns:
            (es_estructura, tipo, numero, titulo)
        """
        for patron, tipo in self.PATRONES_ESTRUCTURA:
            match = re.match(patron, linea, re.IGNORECASE)
            if match:
                grupos = match.groups()
                numero = grupos[1] if len(grupos) > 1 else None
                titulo = grupos[2].strip() if len(grupos) > 2 and grupos[2] else None
                return True, tipo, numero, titulo

        return False, None, None, None

    def extraer_metadata_inicial(self, texto: str) -> Dict[str, str]:
        """
        Extraer metadata del inicio del documento

        Args:
            texto: Texto del documento

        Returns:
            Diccionario con metadata extraída
        """
        metadata = {}
        lineas = texto.split('\n')[:50]  # Solo primeras 50 líneas

        # Buscar número de norma
        for linea in lineas:
            # Ley Nº, Decreto Supremo Nº, etc.
            match_ley = re.search(r'(LEY|DECRETO\s+SUPREMO|RESOLUCI[OÓ]N)\s+N[°º]?\s*(\d+)', linea, re.IGNORECASE)
            if match_ley:
                metadata['tipo_norma'] = match_ley.group(1).strip()
                metadata['numero_norma'] = match_ley.group(2).strip()

            # Fecha
            match_fecha = re.search(r'(\d{1,2})\s+de\s+(\w+)\s+de\s+(\d{4})', linea, re.IGNORECASE)
            if match_fecha:
                metadata['fecha_texto'] = match_fecha.group(0)

        return metadata
