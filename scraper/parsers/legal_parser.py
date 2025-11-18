"""
Parser Profesional para documentos legales bolivianos

Soporta:
- Leyes/Decretos: Artículos, Parágrafos, Incisos, Numerales, Capítulos, Disposiciones
- Sentencias TCP/TSJ: VISTOS, RESULTANDO, CONSIDERANDO, POR TANTO, Parte Resolutiva
- Resoluciones: CONSIDERANDO, RESUELVE, Artículos

Autor: Sistema BUHO
Fecha: 2025-11-18
"""
import re
from typing import List, Dict, Tuple, Optional
import logging

from scraper.models import Articulo
from scraper.metadata_extractor import LegalMetadataExtractor

logger = logging.getLogger(__name__)


class LegalParserProfesional:
    """
    Parser profesional para documentos legales bolivianos

    Detecta y segmenta:
    1. Estructura normativa: Títulos, Capítulos, Secciones
    2. Artículos y sub-unidades: Artículos, Parágrafos, Incisos, Numerales
    3. Estructura de sentencias: VISTOS, CONSIDERANDO, etc.
    4. Estructura de resoluciones: CONSIDERANDO, RESUELVE
    5. Disposiciones especiales: Finales, Transitorias, Adicionales, Abrogatorias
    """

    # =========================================================================
    # PATRONES PARA LEYES/DECRETOS
    # =========================================================================

    # Artículos
    PATRONES_ARTICULO = [
        r'^(?:ART[IÍ]CULO|ART\.|ARTICULO)\s+(\d+)[°º]?\.?\s*[-–—]?\s*(.*?)$',
        r'^Art[íi]culo\s+(\d+)[°º]?\.?\s*[-–—]?\s*(.*?)$',
        r'^(\d+)[°º]?\.?\s*[-–—]\s*(.*?)$',  # Solo número
    ]

    # Parágrafos
    PATRONES_PARAGRAFO = [
        r'^(?:PAR[AÁ]GRAFO|PARÁGRAFO|PARAGRAFO)\s+([IVX]+|\d+|[ÚU]NICO)[°º]?\.?\s*[-–—]?\s*(.*?)$',
        r'^(?:§|¶)\s*([IVX]+|\d+|[ÚU]NICO)\.?\s*[-–—]?\s*(.*?)$',
    ]

    # Incisos
    PATRONES_INCISO = [
        r'^(?:INCISO|INC\.)\s+([a-z]|\d+)[).]?\s*[-–—]?\s*(.*?)$',
        r'^([a-z])[).]\s+(.*?)$',  # a) texto
        r'^(\d+)[).]\s+(.*?)$',     # 1) texto
    ]

    # Numerales
    PATRONES_NUMERAL = [
        r'^(?:NUMERAL|NUM\.)\s+(\d+)[°º]?\.?\s*[-–—]?\s*(.*?)$',
        r'^(\d+)°\.?\s+(.*?)$',  # 1° texto
    ]

    # Estructura (Títulos, Capítulos, Secciones)
    PATRONES_ESTRUCTURA = [
        (r'^(T[IÍ]TULO|TITULO|TÍT\.)\s+([IVX]+|\d+)\.?\s*[-–—]?\s*(.*?)$', 'titulo'),
        (r'^(CAP[IÍ]TULO|CAPITULO|CAP\.)\s+([IVX]+|\d+)\.?\s*[-–—]?\s*(.*?)$', 'capitulo'),
        (r'^(SECCI[OÓ]N|SECCION|SECC\.)\s+([IVX]+|\d+)\.?\s*[-–—]?\s*(.*?)$', 'seccion'),
    ]

    # Disposiciones especiales
    PATRONES_DISPOSICION = [
        (r'^DISPOSICI[OÓ]N\s+(FINAL|ADICIONAL|TRANSITORIA|ABROGATORIA|DEROGATORIA)\s*(.*?)$', 'disposicion'),
        (r'^DISPOSICIONES\s+(FINALES|ADICIONALES|TRANSITORIAS|ABROGATORIAS|DEROGATORIAS)\s*$', 'disposiciones'),
    ]

    # =========================================================================
    # PATRONES PARA SENTENCIAS (TCP/TSJ)
    # =========================================================================

    PATRONES_SENTENCIA = [
        (r'^VISTOS?\s*:?\s*(.*?)$', 'vistos'),
        (r'^(?:RESULTANDO|ANTECEDENTES?)\s*:?\s*(.*?)$', 'resultando'),
        (r'^CONSIDERANDO\s*:?\s*(.*?)$', 'considerando'),
        (r'^(?:FUNDAMENTOS?|FUNDAMENTO\s+JUR[IÍ]DICO)\s*:?\s*(.*?)$', 'fundamento'),
        (r'^(?:POR\s+TANTO|PARTE\s+RESOLUTIVA|RESUELVE?)\s*:?\s*(.*?)$', 'por_tanto'),
        (r'^(?:FALLA|SE\s+RESUELVE)\s*:?\s*(.*?)$', 'parte_resolutiva'),
    ]

    # =========================================================================
    # PATRONES PARA RESOLUCIONES ADMINISTRATIVAS
    # =========================================================================

    PATRONES_RESOLUCION = [
        (r'^CONSIDERANDO\s*:?\s*(.*?)$', 'considerando'),
        (r'^RESUELVE\s*:?\s*(.*?)$', 'resuelve'),
    ]

    def __init__(self, tipo_documento: Optional[str] = None, site_id: Optional[str] = None):
        """
        Inicializar parser

        Args:
            tipo_documento: Tipo de documento para usar estrategia específica
            site_id: ID del sitio para aplicar lógica específica
        """
        self.tipo_documento = tipo_documento
        self.site_id = site_id
        self.contador_unidades = 0
        self.articulo_actual_numero = None  # Para tracking de jerarquía
        self.paragrafo_actual_numero = None
        self.metadata_extractor = LegalMetadataExtractor()  # Para metadata de unidades

    def parsear_documento(
        self,
        id_documento: str,
        texto: str,
        tipo_documento: Optional[str] = None,
        site_id: Optional[str] = None
    ) -> List[Articulo]:
        """
        Parsear documento completo en unidades jurídicas

        Args:
            id_documento: ID del documento
            texto: Texto completo del documento
            tipo_documento: Tipo de documento (override del constructor)
            site_id: ID del sitio (override del constructor)

        Returns:
            Lista de unidades (artículos, parágrafos, etc.) encontradas
        """
        if not texto or not texto.strip():
            logger.warning(f"Texto vacío para documento {id_documento}")
            return []

        # Override tipo_documento y site_id si se pasan
        if tipo_documento:
            self.tipo_documento = tipo_documento
        if site_id:
            self.site_id = site_id

        self.contador_unidades = 0
        self.articulo_actual_numero = None
        self.paragrafo_actual_numero = None

        # Determinar estrategia de parsing
        if self._es_sentencia():
            return self._parsear_sentencia(id_documento, texto)
        elif self._es_resolucion_administrativa():
            return self._parsear_resolucion(id_documento, texto)
        else:
            # Por defecto: parsear como ley/decreto (artículos, parágrafos, etc.)
            return self._parsear_ley_decreto(id_documento, texto)

    def _es_sentencia(self) -> bool:
        """Determinar si es una sentencia"""
        if not self.tipo_documento:
            return False

        tipo_lower = self.tipo_documento.lower()
        return any(keyword in tipo_lower for keyword in [
            'sentencia', 'auto supremo', 'auto constitucional'
        ])

    def _es_resolucion_administrativa(self) -> bool:
        """Determinar si es resolución administrativa"""
        if not self.tipo_documento:
            return False

        tipo_lower = self.tipo_documento.lower()
        return any(keyword in tipo_lower for keyword in [
            'resolución administrativa', 'resolución ministerial',
            'resolución normativa', 'resolución suprema'
        ]) and 'sentencia' not in tipo_lower

    def _parsear_ley_decreto(self, id_documento: str, texto: str) -> List[Articulo]:
        """
        Parsear ley o decreto con estructura completa:
        - Títulos, Capítulos, Secciones
        - Artículos
        - Parágrafos
        - Incisos
        - Numerales
        - Disposiciones
        """
        unidades = []
        lineas = texto.split('\n')

        unidad_actual = None
        contenido_actual = []
        orden = 0

        for linea in lineas:
            linea = linea.strip()
            if not linea:
                continue

            # 1. Verificar estructura (Título, Capítulo, Sección)
            es_estructura, tipo_est, numero_est, titulo_est = self._detectar_estructura(linea)
            if es_estructura:
                # Guardar unidad anterior
                if unidad_actual:
                    unidad_actual.contenido = '\n'.join(contenido_actual).strip()
                    unidades.append(unidad_actual)

                # Crear nueva estructura
                orden += 1
                unidad_actual = self._crear_unidad(
                    id_documento, tipo_est, numero_est, titulo_est, orden, nivel=0
                )
                contenido_actual = []
                continue

            # 2. Verificar disposición especial
            es_disp, tipo_disp, titulo_disp = self._detectar_disposicion(linea)
            if es_disp:
                if unidad_actual:
                    unidad_actual.contenido = '\n'.join(contenido_actual).strip()
                    unidades.append(unidad_actual)

                orden += 1
                unidad_actual = self._crear_unidad(
                    id_documento, tipo_disp, None, titulo_disp, orden, nivel=1
                )
                contenido_actual = []
                continue

            # 3. Verificar artículo
            es_art, numero_art, titulo_art = self._detectar_articulo(linea)
            if es_art:
                if unidad_actual:
                    unidad_actual.contenido = '\n'.join(contenido_actual).strip()
                    unidades.append(unidad_actual)

                orden += 1
                self.articulo_actual_numero = numero_art
                self.paragrafo_actual_numero = None

                unidad_actual = self._crear_unidad(
                    id_documento, 'articulo', numero_art, titulo_art, orden, nivel=1
                )
                unidad_actual.numero_articulo = numero_art
                contenido_actual = []
                continue

            # 4. Verificar parágrafo
            es_par, numero_par, titulo_par = self._detectar_paragrafo(linea)
            if es_par:
                if unidad_actual:
                    unidad_actual.contenido = '\n'.join(contenido_actual).strip()
                    unidades.append(unidad_actual)

                orden += 1
                self.paragrafo_actual_numero = numero_par

                unidad_actual = self._crear_unidad(
                    id_documento, 'paragrafo', numero_par, titulo_par, orden, nivel=2
                )
                unidad_actual.numero_articulo = self.articulo_actual_numero
                unidad_actual.numero_paragrafo = numero_par
                contenido_actual = []
                continue

            # 5. Verificar inciso
            es_inc, numero_inc, titulo_inc = self._detectar_inciso(linea)
            if es_inc:
                if unidad_actual:
                    unidad_actual.contenido = '\n'.join(contenido_actual).strip()
                    unidades.append(unidad_actual)

                orden += 1
                unidad_actual = self._crear_unidad(
                    id_documento, 'inciso', numero_inc, titulo_inc, orden, nivel=3
                )
                unidad_actual.numero_articulo = self.articulo_actual_numero
                unidad_actual.numero_paragrafo = self.paragrafo_actual_numero
                unidad_actual.numero_inciso = numero_inc
                contenido_actual = []
                continue

            # 6. Verificar numeral
            es_num, numero_num, titulo_num = self._detectar_numeral(linea)
            if es_num:
                if unidad_actual:
                    unidad_actual.contenido = '\n'.join(contenido_actual).strip()
                    unidades.append(unidad_actual)

                orden += 1
                unidad_actual = self._crear_unidad(
                    id_documento, 'numeral', numero_num, titulo_num, orden, nivel=4
                )
                unidad_actual.numero_articulo = self.articulo_actual_numero
                unidad_actual.numero_numeral = numero_num
                contenido_actual = []
                continue

            # Si llegamos aquí, es contenido de la unidad actual
            if unidad_actual:
                contenido_actual.append(linea)

        # Guardar última unidad
        if unidad_actual:
            unidad_actual.contenido = '\n'.join(contenido_actual).strip()
            unidades.append(unidad_actual)

        # Si no se encontraron unidades, crear una con todo el texto
        if not unidades:
            logger.info(f"No se encontraron unidades estructuradas, creando unidad única")
            unidades.append(self._crear_unidad(
                id_documento, 'documento', '1', 'Documento completo', 1, nivel=0
            ))
            unidades[0].contenido = texto.strip()

        # Enriquecer con metadata semántica
        unidades = self._enriquecer_metadata_unidades(unidades)

        logger.info(f"Parseados {len(unidades)} unidades para {id_documento}")
        return unidades

    def _parsear_sentencia(self, id_documento: str, texto: str) -> List[Articulo]:
        """
        Parsear sentencia (TCP/TSJ) con bloques:
        - VISTOS
        - RESULTANDO/ANTECEDENTES
        - CONSIDERANDO (puede haber múltiples con I., II., III.)
        - FUNDAMENTOS
        - POR TANTO / PARTE RESOLUTIVA
        """
        unidades = []
        lineas = texto.split('\n')

        unidad_actual = None
        contenido_actual = []
        orden = 0
        bloque_actual = None

        for linea in lineas:
            linea = linea.strip()
            if not linea:
                continue

            # Detectar bloques de sentencia
            es_bloque, tipo_bloque, titulo_bloque = self._detectar_bloque_sentencia(linea)

            if es_bloque:
                # Guardar bloque anterior
                if unidad_actual:
                    unidad_actual.contenido = '\n'.join(contenido_actual).strip()
                    unidades.append(unidad_actual)

                # Crear nuevo bloque
                orden += 1
                bloque_actual = tipo_bloque
                unidad_actual = self._crear_unidad(
                    id_documento, tipo_bloque, str(orden), titulo_bloque, orden, nivel=1
                )
                contenido_actual = []
                continue

            # Agregar contenido al bloque actual
            if unidad_actual:
                contenido_actual.append(linea)

        # Guardar último bloque
        if unidad_actual:
            unidad_actual.contenido = '\n'.join(contenido_actual).strip()
            unidades.append(unidad_actual)

        if not unidades:
            logger.warning(f"No se detectaron bloques de sentencia, creando unidad única")
            unidades.append(self._crear_unidad(
                id_documento, 'documento', '1', 'Sentencia completa', 1, nivel=0
            ))
            unidades[0].contenido = texto.strip()

        # Enriquecer con metadata semántica
        unidades = self._enriquecer_metadata_unidades(unidades, area_documento='constitucional')

        logger.info(f"Parseados {len(unidades)} bloques de sentencia para {id_documento}")
        return unidades

    def _parsear_resolucion(self, id_documento: str, texto: str) -> List[Articulo]:
        """
        Parsear resolución administrativa:
        - CONSIDERANDO (múltiples)
        - RESUELVE
        - Artículos (dentro de RESUELVE)
        """
        unidades = []
        lineas = texto.split('\n')

        unidad_actual = None
        contenido_actual = []
        orden = 0
        en_resuelve = False

        for linea in lineas:
            linea = linea.strip()
            if not linea:
                continue

            # Detectar CONSIDERANDO
            if re.match(r'^CONSIDERANDO\s*:?', linea, re.IGNORECASE):
                if unidad_actual:
                    unidad_actual.contenido = '\n'.join(contenido_actual).strip()
                    unidades.append(unidad_actual)

                orden += 1
                unidad_actual = self._crear_unidad(
                    id_documento, 'considerando', str(orden), 'Considerando', orden, nivel=1
                )
                contenido_actual = []
                en_resuelve = False
                continue

            # Detectar RESUELVE
            if re.match(r'^RESUELVE\s*:?', linea, re.IGNORECASE):
                if unidad_actual:
                    unidad_actual.contenido = '\n'.join(contenido_actual).strip()
                    unidades.append(unidad_actual)

                orden += 1
                unidad_actual = self._crear_unidad(
                    id_documento, 'resuelve', str(orden), 'Resuelve', orden, nivel=1
                )
                contenido_actual = []
                en_resuelve = True
                continue

            # Dentro de RESUELVE, detectar artículos
            if en_resuelve:
                es_art, numero_art, titulo_art = self._detectar_articulo(linea)
                if es_art:
                    if unidad_actual and unidad_actual.tipo_unidad == 'articulo':
                        unidad_actual.contenido = '\n'.join(contenido_actual).strip()
                        unidades.append(unidad_actual)

                    orden += 1
                    unidad_actual = self._crear_unidad(
                        id_documento, 'articulo', numero_art, titulo_art, orden, nivel=2
                    )
                    contenido_actual = []
                    continue

            # Agregar contenido
            if unidad_actual:
                contenido_actual.append(linea)

        # Guardar última unidad
        if unidad_actual:
            unidad_actual.contenido = '\n'.join(contenido_actual).strip()
            unidades.append(unidad_actual)

        if not unidades:
            logger.warning(f"No se detectó estructura de resolución, creando unidad única")
            unidades.append(self._crear_unidad(
                id_documento, 'documento', '1', 'Resolución completa', 1, nivel=0
            ))
            unidades[0].contenido = texto.strip()

        # Enriquecer con metadata semántica
        unidades = self._enriquecer_metadata_unidades(unidades, area_documento='administrativo')

        logger.info(f"Parseados {len(unidades)} bloques de resolución para {id_documento}")
        return unidades

    # =========================================================================
    # MÉTODOS AUXILIARES DE DETECCIÓN
    # =========================================================================

    def _detectar_articulo(self, linea: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """Detectar si línea es artículo"""
        for patron in self.PATRONES_ARTICULO:
            match = re.match(patron, linea, re.IGNORECASE)
            if match:
                numero = match.group(1) if len(match.groups()) > 0 else None
                titulo = match.group(2).strip() if len(match.groups()) > 1 and match.group(2) else None
                return True, numero, titulo
        return False, None, None

    def _detectar_paragrafo(self, linea: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """Detectar si línea es parágrafo"""
        for patron in self.PATRONES_PARAGRAFO:
            match = re.match(patron, linea, re.IGNORECASE)
            if match:
                numero = match.group(1) if len(match.groups()) > 0 else None
                titulo = match.group(2).strip() if len(match.groups()) > 1 and match.group(2) else None
                return True, numero, titulo
        return False, None, None

    def _detectar_inciso(self, linea: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """Detectar si línea es inciso"""
        for patron in self.PATRONES_INCISO:
            match = re.match(patron, linea, re.IGNORECASE)
            if match:
                numero = match.group(1) if len(match.groups()) > 0 else None
                titulo = match.group(2).strip() if len(match.groups()) > 1 and match.group(2) else None
                return True, numero, titulo
        return False, None, None

    def _detectar_numeral(self, linea: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """Detectar si línea es numeral"""
        for patron in self.PATRONES_NUMERAL:
            match = re.match(patron, linea, re.IGNORECASE)
            if match:
                numero = match.group(1) if len(match.groups()) > 0 else None
                titulo = match.group(2).strip() if len(match.groups()) > 1 and match.group(2) else None
                return True, numero, titulo
        return False, None, None

    def _detectar_estructura(self, linea: str) -> Tuple[bool, Optional[str], Optional[str], Optional[str]]:
        """Detectar si línea es estructura (Título, Capítulo, Sección)"""
        for patron, tipo in self.PATRONES_ESTRUCTURA:
            match = re.match(patron, linea, re.IGNORECASE)
            if match:
                numero = match.group(2) if len(match.groups()) > 1 else None
                titulo = match.group(3).strip() if len(match.groups()) > 2 and match.group(3) else None
                return True, tipo, numero, titulo
        return False, None, None, None

    def _detectar_disposicion(self, linea: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """Detectar si línea es disposición"""
        for patron, tipo in self.PATRONES_DISPOSICION:
            match = re.match(patron, linea, re.IGNORECASE)
            if match:
                titulo = match.group(0).strip()
                return True, tipo, titulo
        return False, None, None

    def _detectar_bloque_sentencia(self, linea: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """Detectar bloques de sentencia"""
        for patron, tipo in self.PATRONES_SENTENCIA:
            if re.match(patron, linea, re.IGNORECASE):
                return True, tipo, linea.strip()
        return False, None, None

    def _crear_unidad(
        self,
        id_documento: str,
        tipo_unidad: str,
        numero: Optional[str],
        titulo: Optional[str],
        orden: int,
        nivel: int
    ) -> Articulo:
        """Crear una unidad (Artículo) con todos los campos"""
        self.contador_unidades += 1

        # Generar ID estable
        if numero:
            id_articulo = f"{id_documento}_{tipo_unidad}_{numero}"
        else:
            id_articulo = f"{id_documento}_{tipo_unidad}_{self.contador_unidades}"

        return Articulo(
            id_articulo=id_articulo,
            id_documento=id_documento,
            numero=numero,
            titulo=titulo,
            contenido="",  # Se llenará después
            tipo_unidad=tipo_unidad,
            orden_en_documento=orden,
            nivel_jerarquico=nivel
        )

    def _enriquecer_metadata_unidades(
        self,
        unidades: List[Articulo],
        area_documento: Optional[str] = None
    ) -> List[Articulo]:
        """
        Enriquecer unidades con metadata semántica (palabras clave y área)

        Args:
            unidades: Lista de unidades parseadas
            area_documento: Área principal del documento (para contexto)

        Returns:
            Lista de unidades enriquecidas
        """
        for unidad in unidades:
            # Solo procesar si tiene contenido suficiente
            if unidad.contenido and len(unidad.contenido) > 20:
                try:
                    # Extraer metadata de la unidad
                    metadata_unidad = self.metadata_extractor.extraer_metadata_unidad(
                        contenido_unidad=unidad.contenido,
                        tipo_unidad=unidad.tipo_unidad,
                        area_documento=area_documento
                    )

                    # Actualizar campos
                    unidad.palabras_clave_unidad = metadata_unidad.get('palabras_clave_unidad', [])
                    unidad.area_principal_unidad = metadata_unidad.get('area_principal_unidad')

                except Exception as e:
                    logger.warning(f"Error enriqueciendo metadata de unidad {unidad.id_articulo}: {e}")
                    # Continuar con valores por defecto (vacío/None)

        return unidades


# Mantener compatibilidad con versión anterior
LegalParser = LegalParserProfesional
