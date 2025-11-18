"""
Extractor de metadata extendida para documentos legales
Clasifica área del derecho, extrae número de norma, etc.
"""
import re
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class LegalMetadataExtractor:
    """Extractor de metadata legal completa"""

    # Áreas del derecho con palabras clave
    AREAS_DERECHO = {
        'constitucional': [
            'constitucional', 'derechos fundamentales', 'garantías constitucionales',
            'amparo constitucional', 'acción de libertad', 'tribunal constitucional',
            'control de constitucionalidad'
        ],
        'civil': [
            'civil', 'contratos', 'obligaciones', 'familia', 'sucesiones',
            'propiedad', 'hipoteca', 'usufructo', 'servidumbre', 'matrimonio',
            'divorcio', 'filiación', 'tutela', 'curatela'
        ],
        'penal': [
            'penal', 'delito', 'pena', 'prisión', 'reclusión', 'homicidio',
            'robo', 'hurto', 'violación', 'estafa', 'narcotráfico', 'terrorismo',
            'secuestro', 'extorsión', 'código penal'
        ],
        'procesal_penal': [
            'proceso penal', 'procedimiento penal', 'imputado', 'fiscal',
            'defensa', 'audiencia', 'juicio oral', 'medidas cautelares'
        ],
        'procesal_civil': [
            'proceso civil', 'demanda', 'contestación', 'prueba', 'sentencia civil',
            'recurso de apelación', 'casación civil'
        ],
        'tributario': [
            'tributario', 'impuesto', 'contribución', 'tasa', 'iva', 'it', 'iue',
            'servicio de impuestos', 'sin', 'evasión fiscal', 'delito tributario',
            'aduana', 'arancel'
        ],
        'laboral': [
            'laboral', 'trabajo', 'empleador', 'trabajador', 'salario', 'sueldo',
            'jornada laboral', 'vacación', 'aguinaldo', 'desahucio', 'despido',
            'contrato de trabajo', 'seguridad social'
        ],
        'administrativo': [
            'administrativo', 'función pública', 'servidor público', 'concesión',
            'licencia administrativa', 'sanción administrativa', 'recurso jerárquico',
            'silencio administrativo'
        ],
        'comercial': [
            'comercial', 'mercantil', 'sociedad comercial', 'quiebra', 'concurso',
            'letra de cambio', 'pagaré', 'cheque', 'comerciante', 'empresa'
        ],
        'financiero': [
            'financiero', 'bancario', 'asfi', 'entidad financiera', 'banco',
            'cooperativa', 'microfinanzas', 'supervisión financiera'
        ],
        'ambiental': [
            'ambiental', 'medio ambiente', 'ecología', 'recursos naturales',
            'contaminación', 'áreas protegidas', 'biodiversidad'
        ],
        'minero': [
            'minero', 'minería', 'comibol', 'cooperativa minera', 'concesión minera',
            'regalías mineras'
        ],
        'hidrocarburos': [
            'hidrocarburos', 'petróleo', 'gas', 'ypfb', 'exploración', 'explotación'
        ],
        'electoral': [
            'electoral', 'elección', 'voto', 'padrón electoral', 'referéndum',
            'tribunal electoral', 'campaña electoral'
        ],
        'municipal': [
            'municipal', 'municipio', 'gobierno autónomo municipal', 'concejo municipal',
            'alcalde', 'impuesto municipal'
        ],
        'otros': []  # Categoría por defecto
    }

    # Tipos de normas por jerarquía
    JERARQUIA_NORMAS = {
        1: ['Constitución Política del Estado', 'CPE'],
        2: ['Ley', 'Código'],
        3: ['Decreto Supremo', 'DS'],
        4: ['Resolución Suprema', 'RS'],
        5: ['Resolución Ministerial', 'RM'],
        6: ['Resolución Bi-Ministerial', 'RBM'],
        7: ['Resolución Administrativa', 'RA'],
        8: ['Resolución Normativa', 'RND'],
        9: ['Circular', 'Instructivo'],
        10: ['Sentencia Constitucional', 'SC'],
        11: ['Auto Supremo', 'AS'],
        12: ['Resolución', 'Directriz']
    }

    def __init__(self):
        """Inicializar extractor"""
        pass

    def extraer_metadata_completa(
        self,
        texto: str,
        titulo: Optional[str] = None,
        tipo_documento: Optional[str] = None,
        sumilla: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extraer metadata completa de un documento

        Args:
            texto: Texto completo del documento
            titulo: Título del documento (si existe)
            tipo_documento: Tipo de documento (si se conoce)
            sumilla: Sumilla/resumen (si existe)

        Returns:
            Diccionario con metadata extendida
        """
        metadata = {}

        # Texto completo para análisis
        texto_analisis = f"{titulo or ''} {sumilla or ''} {texto[:5000]}"  # Primeros 5000 chars
        texto_analisis = texto_analisis.lower()

        # 1. Número de norma
        metadata['numero_norma'] = self._extraer_numero_norma(texto, titulo)

        # 2. Tipo de norma
        metadata['tipo_norma'] = self._extraer_tipo_norma(texto, titulo, tipo_documento)

        # 3. Jerarquía normativa
        metadata['jerarquia'] = self._determinar_jerarquia(metadata['tipo_norma'])

        # 4. Fecha de promulgación
        metadata['fecha_promulgacion'] = self._extraer_fecha(texto)

        # 5. Área del derecho (clasificación automática)
        metadata['areas_derecho'] = self._clasificar_area_derecho(texto_analisis)
        metadata['area_principal'] = metadata['areas_derecho'][0] if metadata['areas_derecho'] else 'otros'

        # 6. Entidad emisora
        metadata['entidad_emisora'] = self._extraer_entidad_emisora(texto, titulo)

        # 7. Estado de vigencia
        metadata['estado_vigencia'] = self._determinar_estado_vigencia(texto_analisis)

        # 8. Modificaciones/derogaciones
        metadata['modifica_normas'] = self._extraer_normas_modificadas(texto)
        metadata['deroga_normas'] = self._extraer_normas_derogadas(texto)

        # 9. Palabras clave
        metadata['palabras_clave'] = self._extraer_palabras_clave(texto_analisis, metadata['areas_derecho'])

        # 10. Sumilla generada (si no existe)
        if not sumilla:
            metadata['sumilla_generada'] = self._generar_sumilla(texto)

        # 11. Estadísticas del documento
        metadata['estadisticas'] = {
            'total_caracteres': len(texto),
            'total_palabras': len(texto.split()),
            'estimado_paginas': max(1, len(texto) // 3000)  # ~3000 chars por página
        }

        return metadata

    def _extraer_numero_norma(self, texto: str, titulo: Optional[str] = None) -> Optional[str]:
        """Extraer número de norma"""
        texto_buscar = f"{titulo or ''}\n{texto[:2000]}"

        patrones = [
            r'(?:LEY|Ley)\s+N[°º]?\s*(\d+)',
            r'(?:DECRETO\s+SUPREMO|Decreto\s+Supremo|DS)\s+N[°º]?\s*(\d+)',
            r'(?:RESOLUCIÓN|Resolución)\s+(?:SUPREMA|MINISTERIAL|ADMINISTRATIVA|NORMATIVA)?\s*N[°º]?\s*([\d/-]+)',
            r'(?:SENTENCIA|Sentencia)\s+(?:CONSTITUCIONAL)?\s*N[°º]?\s*([\d/-]+)',
            r'(?:AUTO\s+SUPREMO|Auto\s+Supremo)\s+N[°º]?\s*([\d/-]+)',
            r'N[°º]\s*(\d+(?:/\d+)?)',
        ]

        for patron in patrones:
            match = re.search(patron, texto_buscar, re.IGNORECASE)
            if match:
                return match.group(1)

        return None

    def _extraer_tipo_norma(
        self,
        texto: str,
        titulo: Optional[str] = None,
        tipo_documento: Optional[str] = None
    ) -> Optional[str]:
        """Extraer tipo de norma"""
        if tipo_documento:
            return tipo_documento

        texto_buscar = f"{titulo or ''}\n{texto[:1000]}"

        tipos = [
            'Constitución Política del Estado',
            'Ley',
            'Código',
            'Decreto Supremo',
            'Resolución Suprema',
            'Resolución Ministerial',
            'Resolución Bi-Ministerial',
            'Resolución Administrativa',
            'Resolución Normativa',
            'Sentencia Constitucional',
            'Auto Supremo',
            'Circular',
            'Directriz'
        ]

        for tipo in tipos:
            if re.search(rf'\b{re.escape(tipo)}\b', texto_buscar, re.IGNORECASE):
                return tipo

        return 'Documento Legal'

    def _determinar_jerarquia(self, tipo_norma: Optional[str]) -> int:
        """Determinar jerarquía normativa"""
        if not tipo_norma:
            return 99

        tipo_lower = tipo_norma.lower()

        for nivel, tipos in self.JERARQUIA_NORMAS.items():
            for tipo in tipos:
                if tipo.lower() in tipo_lower:
                    return nivel

        return 99  # Jerarquía desconocida

    def _extraer_fecha(self, texto: str) -> Optional[str]:
        """Extraer fecha de promulgación"""
        # Patrones de fecha
        patrones_fecha = [
            r'(\d{1,2})\s+de\s+(\w+)\s+de\s+(\d{4})',
            r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})',
            r'(\d{4})-(\d{2})-(\d{2})'
        ]

        meses = {
            'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04',
            'mayo': '05', 'junio': '06', 'julio': '07', 'agosto': '08',
            'septiembre': '09', 'octubre': '10', 'noviembre': '11', 'diciembre': '12'
        }

        texto_buscar = texto[:2000]

        for patron in patrones_fecha:
            match = re.search(patron, texto_buscar, re.IGNORECASE)
            if match:
                grupos = match.groups()
                if len(grupos) == 3:
                    # Formato: "15 de marzo de 2024"
                    if grupos[1].lower() in meses:
                        dia = grupos[0].zfill(2)
                        mes = meses[grupos[1].lower()]
                        año = grupos[2]
                        return f"{año}-{mes}-{dia}"
                    # Otros formatos
                    return '-'.join(grupos)

        return None

    def _clasificar_area_derecho(self, texto: str) -> List[str]:
        """Clasificar área(s) del derecho del documento"""
        areas_detectadas = {}

        for area, palabras_clave in self.AREAS_DERECHO.items():
            if area == 'otros':
                continue

            puntuacion = 0
            for palabra in palabras_clave:
                # Contar ocurrencias (limitado a 10 para evitar sobre-ponderación)
                ocurrencias = min(10, len(re.findall(rf'\b{re.escape(palabra)}\b', texto, re.IGNORECASE)))
                puntuacion += ocurrencias

            if puntuacion > 0:
                areas_detectadas[area] = puntuacion

        # Ordenar por puntuación
        areas_ordenadas = sorted(areas_detectadas.items(), key=lambda x: x[1], reverse=True)

        # Retornar top 3 áreas o 'otros' si no se detectó nada
        if areas_ordenadas:
            return [area for area, _ in areas_ordenadas[:3]]
        else:
            return ['otros']

    def _extraer_entidad_emisora(self, texto: str, titulo: Optional[str] = None) -> Optional[str]:
        """Extraer entidad que emite la norma"""
        texto_buscar = f"{titulo or ''}\n{texto[:1000]}"

        entidades = [
            'Asamblea Legislativa Plurinacional',
            'Tribunal Constitucional Plurinacional',
            'Tribunal Supremo de Justicia',
            'Órgano Ejecutivo',
            'Presidencia del Estado',
            'Ministerio de Economía',
            'Ministerio de Justicia',
            'ASFI',
            'Servicio de Impuestos Nacionales',
            'Contraloría General del Estado'
        ]

        for entidad in entidades:
            if re.search(rf'\b{re.escape(entidad)}\b', texto_buscar, re.IGNORECASE):
                return entidad

        return None

    def _determinar_estado_vigencia(self, texto: str) -> str:
        """Determinar estado de vigencia"""
        if re.search(r'\b(derogad[ao]|abrogad[ao])\b', texto, re.IGNORECASE):
            return 'derogada'
        elif re.search(r'\b(modificad[ao]|reformad[ao])\b', texto, re.IGNORECASE):
            return 'modificada'
        else:
            return 'vigente'

    def _extraer_normas_modificadas(self, texto: str) -> List[str]:
        """Extraer normas que son modificadas por este documento"""
        normas = []
        patron = r'(?:modifica|reforma|adiciona)[^.]*?(?:Ley|Decreto|Resolución)\s+N[°º]?\s*(\d+(?:/\d+)?)'

        matches = re.finditer(patron, texto[:5000], re.IGNORECASE)
        for match in matches:
            normas.append(match.group(1))

        return list(set(normas))[:10]  # Máximo 10

    def _extraer_normas_derogadas(self, texto: str) -> List[str]:
        """Extraer normas que son derogadas por este documento"""
        normas = []
        patron = r'(?:deroga|abroga)[^.]*?(?:Ley|Decreto|Resolución)\s+N[°º]?\s*(\d+(?:/\d+)?)'

        matches = re.finditer(patron, texto[:5000], re.IGNORECASE)
        for match in matches:
            normas.append(match.group(1))

        return list(set(normas))[:10]  # Máximo 10

    def _extraer_palabras_clave(self, texto: str, areas: List[str]) -> List[str]:
        """Extraer palabras clave del documento"""
        palabras_clave = set()

        # Agregar palabras del área detectada
        for area in areas:
            if area in self.AREAS_DERECHO:
                palabras_clave.update(self.AREAS_DERECHO[area][:5])  # Top 5 por área

        return list(palabras_clave)[:20]  # Máximo 20

    def _generar_sumilla(self, texto: str) -> str:
        """Generar sumilla automática (primeras líneas significativas)"""
        lineas = texto.split('\n')
        lineas_significativas = []

        for linea in lineas[:30]:  # Primeras 30 líneas
            linea = linea.strip()
            if len(linea) > 20 and not linea.isupper():  # Evitar encabezados
                lineas_significativas.append(linea)
                if len(' '.join(lineas_significativas)) > 200:
                    break

        sumilla = ' '.join(lineas_significativas)
        return sumilla[:300] + '...' if len(sumilla) > 300 else sumilla
