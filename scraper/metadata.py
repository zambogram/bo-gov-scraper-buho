"""
Extractor y Gestor de Metadatos para Documentos Legales
Extrae automáticamente metadatos completos de leyes y documentos jurídicos bolivianos
"""

import re
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import yaml


class MetadataExtractor:
    """Extractor inteligente de metadatos de documentos legales"""

    def __init__(self, schema_path: str = "config/metadata_schema.yaml"):
        """
        Inicializa el extractor de metadatos

        Args:
            schema_path: Ruta al esquema de metadatos YAML
        """
        self.schema_path = Path(schema_path)
        self.schema = self._cargar_schema()
        self.meses_es = {
            'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04',
            'mayo': '05', 'junio': '06', 'julio': '07', 'agosto': '08',
            'septiembre': '09', 'octubre': '10', 'noviembre': '11', 'diciembre': '12'
        }

    def _cargar_schema(self) -> Dict:
        """Carga el esquema de metadatos desde el archivo YAML"""
        if self.schema_path.exists():
            with open(self.schema_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        return {}

    def extraer_metadatos(self, texto: str, archivo_path: Optional[str] = None,
                         sitio_web: str = "", url_origen: str = "") -> Dict[str, Any]:
        """
        Extrae metadatos completos de un documento legal

        Args:
            texto: Texto del documento
            archivo_path: Ruta al archivo original
            sitio_web: Nombre del sitio web fuente
            url_origen: URL de donde se obtuvo el documento

        Returns:
            Diccionario con todos los metadatos extraídos
        """
        metadata = {
            'fecha_scraping': datetime.now().isoformat(),
            'sitio_web': sitio_web,
            'url_origen': url_origen,
            'estado_procesamiento': 'procesando'
        }

        # Extraer número de ley
        metadata['numero_ley'] = self._extraer_numero_ley(texto)

        # Extraer tipo de norma
        metadata['tipo_norma'] = self._extraer_tipo_norma(texto)

        # Extraer título
        metadata['titulo'] = self._extraer_titulo(texto)

        # Extraer fechas
        fechas = self._extraer_fechas(texto)
        metadata.update(fechas)

        # Extraer órgano emisor y firmante
        metadata['organo_emisor'] = self._extraer_organo_emisor(texto)
        metadata['firmante'] = self._extraer_firmante(texto)

        # Determinar área del derecho
        metadata['area_derecho'] = self._determinar_area_derecho(texto, sitio_web)

        # Determinar jerarquía normativa
        metadata['jerarquia_normativa'] = self._determinar_jerarquia(metadata['tipo_norma'])

        # Extraer palabras clave
        metadata['palabras_clave'] = self._extraer_palabras_clave(texto)

        # Extraer artículos
        metadata['articulos_principales'] = self._extraer_articulos(texto)
        metadata['total_articulos'] = len(metadata['articulos_principales'])

        # Estadísticas del texto
        metadata['total_palabras'] = len(texto.split())
        metadata['total_caracteres'] = len(texto)

        # Determinar vigencia
        metadata['vigente'] = self._determinar_vigencia(texto, fechas.get('fecha_abrogacion'))

        # Extraer relaciones con otras leyes
        relaciones = self._extraer_relaciones(texto)
        metadata.update(relaciones)

        # Generar código único
        metadata['codigo_unico'] = self._generar_codigo_unico(metadata)

        # Si hay archivo, extraer metadatos del archivo
        if archivo_path:
            file_metadata = self._extraer_metadatos_archivo(archivo_path)
            metadata.update(file_metadata)

        return metadata

    def _extraer_numero_ley(self, texto: str) -> str:
        """Extrae el número de ley del texto"""
        patrones = [
            r'Ley\s+N[°º]?\s*(\d+)',
            r'LEY\s+N[°º]?\s*(\d+)',
            r'D\.?S\.?\s+N[°º]?\s*(\d+)',
            r'Decreto\s+Supremo\s+N[°º]?\s*(\d+)',
            r'DECRETO\s+SUPREMO\s+N[°º]?\s*(\d+)',
            r'Resolución\s+(?:Ministerial|Administrativa)\s+N[°º]?\s*(\d+)',
            r'Sentencia\s+Constitucional\s+N[°º]?\s*(\d+/\d+)',
        ]

        for patron in patrones:
            match = re.search(patron, texto[:2000], re.IGNORECASE)
            if match:
                return match.group(0).strip()

        return "Sin número identificado"

    def _extraer_tipo_norma(self, texto: str) -> str:
        """Determina el tipo de norma legal"""
        texto_inicio = texto[:1000].upper()

        tipos = {
            'Constitución': ['CONSTITUCIÓN', 'CONSTITUCIONAL POLÍTICA'],
            'Ley': ['LEY N°', 'LEY N', 'LEY Nº'],
            'Decreto Supremo': ['DECRETO SUPREMO', 'D.S.', 'DS N'],
            'Decreto Ley': ['DECRETO LEY'],
            'Resolución Ministerial': ['RESOLUCIÓN MINISTERIAL', 'R.M.'],
            'Resolución Administrativa': ['RESOLUCIÓN ADMINISTRATIVA', 'R.A.'],
            'Sentencia Constitucional': ['SENTENCIA CONSTITUCIONAL'],
            'Ordenanza Municipal': ['ORDENANZA MUNICIPAL'],
            'Reglamento': ['REGLAMENTO'],
            'Código': ['CÓDIGO']
        }

        for tipo, patrones in tipos.items():
            for patron in patrones:
                if patron in texto_inicio:
                    return tipo

        return "Otro"

    def _extraer_titulo(self, texto: str) -> str:
        """Extrae el título del documento"""
        # Buscar patrones comunes de títulos
        patrones = [
            r'Ley\s+N[°º]?\s*\d+\s*[:\-]?\s*(.+?)(?:\n|$)',
            r'DECRETO\s+SUPREMO\s+N[°º]?\s*\d+\s*[:\-]?\s*(.+?)(?:\n|$)',
            r'(?:LEY|DECRETO|RESOLUCIÓN).*?\n\s*(.+?)(?:\n\n|$)',
        ]

        for patron in patrones:
            match = re.search(patron, texto[:1500], re.IGNORECASE | re.DOTALL)
            if match:
                titulo = match.group(1).strip()
                # Limpiar el título
                titulo = re.sub(r'\s+', ' ', titulo)
                if len(titulo) > 10 and len(titulo) < 300:
                    return titulo

        # Si no se encuentra, tomar las primeras líneas significativas
        lineas = [l.strip() for l in texto[:1000].split('\n') if len(l.strip()) > 20]
        if lineas:
            return lineas[0][:200]

        return "Título no identificado"

    def _extraer_fechas(self, texto: str) -> Dict[str, Optional[str]]:
        """Extrae fechas relevantes del documento"""
        fechas = {
            'fecha_promulgacion': None,
            'fecha_publicacion': None,
            'fecha_vigencia': None,
            'fecha_abrogacion': None
        }

        # Patrones de fecha en español
        patron_fecha = r'(\d{1,2})\s+de\s+(\w+)\s+de\s+(\d{4})'
        matches = re.finditer(patron_fecha, texto[:3000], re.IGNORECASE)

        fechas_encontradas = []
        for match in matches:
            dia, mes, anio = match.groups()
            mes_num = self.meses_es.get(mes.lower(), '01')
            fecha_str = f"{anio}-{mes_num}-{dia.zfill(2)}"
            fechas_encontradas.append(fecha_str)

        # Asignar fechas encontradas
        if len(fechas_encontradas) > 0:
            fechas['fecha_promulgacion'] = fechas_encontradas[0]
        if len(fechas_encontradas) > 1:
            fechas['fecha_publicacion'] = fechas_encontradas[1]

        # Buscar fecha de abrogación
        if re.search(r'abroga|derog|sin efecto', texto, re.IGNORECASE):
            if len(fechas_encontradas) > 2:
                fechas['fecha_abrogacion'] = fechas_encontradas[-1]

        return fechas

    def _extraer_organo_emisor(self, texto: str) -> str:
        """Extrae el órgano que emitió la norma"""
        organos = [
            'Asamblea Legislativa Plurinacional',
            'Congreso Nacional',
            'Poder Ejecutivo',
            'Tribunal Constitucional Plurinacional',
            'Órgano Judicial',
            'Ministerio',
            'Gobierno Municipal',
            'Gobierno Departamental'
        ]

        texto_inicio = texto[:2000]
        for organo in organos:
            if organo.lower() in texto_inicio.lower():
                return organo

        return "Órgano no identificado"

    def _extraer_firmante(self, texto: str) -> Optional[str]:
        """Extrae el nombre del firmante de la norma"""
        # Buscar patrones de firma
        patrones = [
            r'(?:Fdo\.|Firmado|Refrendado)\s*[:.]?\s*([A-ZÁÉÍÓÚ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚ][a-záéíóúñ]+)+)',
            r'Presidente(?:\s+Constitucional)?\s*[:.]?\s*([A-ZÁÉÍÓÚ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚ][a-záéíóúñ]+)+)',
        ]

        for patron in patrones:
            match = re.search(patron, texto[-2000:])
            if match:
                return match.group(1).strip()

        return None

    def _determinar_area_derecho(self, texto: str, sitio_web: str) -> str:
        """Determina el área del derecho basándose en el contenido y sitio web"""
        # Primero, intentar determinar por sitio web
        areas_sitio = {
            'Tribunal Constitucional': 'Constitucional',
            'Ministerio de Trabajo': 'Laboral',
            'Ministerio de Salud': 'Salud',
            'Ministerio de Educación': 'Educación',
            'Ministerio de Medio Ambiente': 'Ambiental',
            'Ministerio de Minería': 'Minero',
            'Ministerio de Hidrocarburos': 'Hidrocarburos',
            'INRA': 'Agrario',
            'Impuestos': 'Tributario',
            'Aduana': 'Aduanero',
            'Fiscalía': 'Penal',
            'Contraloría': 'Administrativo'
        }

        for clave, area in areas_sitio.items():
            if clave.lower() in sitio_web.lower():
                return area

        # Determinar por palabras clave en el texto
        texto_analisis = texto[:5000].lower()

        areas_palabras = {
            'Constitucional': ['constitución', 'constitucional', 'derechos fundamentales'],
            'Penal': ['penal', 'delito', 'pena', 'prisión', 'sanción penal'],
            'Laboral': ['laboral', 'trabajo', 'trabajador', 'empleador', 'salario', 'contrato de trabajo'],
            'Tributario': ['tributario', 'impuesto', 'tributo', 'fiscal'],
            'Ambiental': ['ambiental', 'medio ambiente', 'ecológico', 'recursos naturales'],
            'Minero': ['minero', 'minería', 'explotación minera', 'yacimiento'],
            'Administrativo': ['administrativo', 'administración pública', 'servidor público'],
            'Civil': ['civil', 'contrato', 'obligación', 'responsabilidad civil'],
            'Comercial': ['comercial', 'comercio', 'mercantil', 'empresa'],
        }

        for area, palabras in areas_palabras.items():
            for palabra in palabras:
                if palabra in texto_analisis:
                    return area

        return "General"

    def _determinar_jerarquia(self, tipo_norma: str) -> str:
        """Determina la jerarquía normativa según el tipo"""
        jerarquias = {
            'Constitución': 'Constitucional',
            'Ley': 'Legal',
            'Decreto Ley': 'Legal',
            'Decreto Supremo': 'Reglamentario',
            'Resolución Ministerial': 'Administrativo',
            'Resolución Administrativa': 'Administrativo',
            'Ordenanza Municipal': 'Municipal',
            'Reglamento': 'Reglamentario'
        }

        return jerarquias.get(tipo_norma, 'Legal')

    def _extraer_palabras_clave(self, texto: str, max_palabras: int = 20) -> List[str]:
        """Extrae palabras clave relevantes del documento"""
        # Palabras comunes a ignorar
        stopwords = {'el', 'la', 'de', 'que', 'y', 'a', 'en', 'un', 'ser', 'se', 'no',
                    'lo', 'como', 'más', 'por', 'pero', 'su', 'al', 'le', 'ya', 'o'}

        # Extraer palabras
        palabras = re.findall(r'\b[a-záéíóúñ]{4,}\b', texto.lower())

        # Contar frecuencias
        from collections import Counter
        conteo = Counter(p for p in palabras if p not in stopwords)

        # Retornar las más frecuentes
        return [palabra for palabra, _ in conteo.most_common(max_palabras)]

    def _extraer_articulos(self, texto: str, max_articulos: int = 50) -> List[Dict]:
        """Extrae los artículos del documento"""
        articulos = []

        # Patrón para artículos
        patron = r'Art[íi]culo\s+(\d+)[°º]?\s*[:\-.]?\s*(.*?)(?=Art[íi]culo\s+\d+|$)'

        matches = re.finditer(patron, texto, re.IGNORECASE | re.DOTALL)

        for i, match in enumerate(matches):
            if i >= max_articulos:
                break

            numero, contenido = match.groups()
            articulo = {
                'numero': int(numero),
                'contenido': contenido.strip()[:500]  # Limitar a 500 caracteres
            }
            articulos.append(articulo)

        return articulos

    def _determinar_vigencia(self, texto: str, fecha_abrogacion: Optional[str]) -> bool:
        """Determina si la norma está vigente"""
        if fecha_abrogacion:
            return False

        # Buscar indicadores de no vigencia
        indicadores = ['abroga', 'derog', 'sin efecto', 'sin vigencia']
        texto_busqueda = texto.lower()

        for indicador in indicadores:
            if indicador in texto_busqueda:
                return False

        return True

    def _extraer_relaciones(self, texto: str) -> Dict[str, List[str]]:
        """Extrae relaciones con otras leyes"""
        relaciones = {
            'modifica_a': [],
            'modificada_por': [],
            'deroga_a': [],
            'derogada_por': None,
            'reglamenta_a': None,
            'reglamentada_por': []
        }

        # Buscar leyes que modifica
        patron_modifica = r'modifica(?:ndo)?\s+(?:la\s+)?Ley\s+N?[°º]?\s*(\d+)'
        matches = re.finditer(patron_modifica, texto, re.IGNORECASE)
        relaciones['modifica_a'] = [f"Ley {m.group(1)}" for m in matches]

        # Buscar leyes que deroga
        patron_deroga = r'deroga(?:ndo)?\s+(?:la\s+)?Ley\s+N?[°º]?\s*(\d+)'
        matches = re.finditer(patron_deroga, texto, re.IGNORECASE)
        relaciones['deroga_a'] = [f"Ley {m.group(1)}" for m in matches]

        # Buscar si reglamenta una ley
        patron_reglamenta = r'reglamenta(?:ndo)?\s+(?:la\s+)?Ley\s+N?[°º]?\s*(\d+)'
        match = re.search(patron_reglamenta, texto, re.IGNORECASE)
        if match:
            relaciones['reglamenta_a'] = f"Ley {match.group(1)}"

        return relaciones

    def _generar_codigo_unico(self, metadata: Dict) -> str:
        """Genera un código único para el documento"""
        datos = f"{metadata.get('numero_ley', '')}" \
                f"{metadata.get('titulo', '')}" \
                f"{metadata.get('fecha_promulgacion', '')}"

        return hashlib.sha256(datos.encode()).hexdigest()[:32]

    def _extraer_metadatos_archivo(self, archivo_path: str) -> Dict[str, Any]:
        """Extrae metadatos del archivo físico"""
        path = Path(archivo_path)

        if not path.exists():
            return {}

        metadata = {
            'ruta_archivo_original': str(path),
            'formato_original': path.suffix.upper().replace('.', ''),
            'tamanio_bytes': path.stat().st_size
        }

        # Calcular hashes
        with open(path, 'rb') as f:
            contenido = f.read()
            metadata['hash_md5'] = hashlib.md5(contenido).hexdigest()
            metadata['hash_sha256'] = hashlib.sha256(contenido).hexdigest()

        return metadata

    def agregar_metadatos_a_pdf(self, pdf_path: str, metadata: Dict):
        """
        Agrega metadatos a un archivo PDF

        Args:
            pdf_path: Ruta al archivo PDF
            metadata: Diccionario con metadatos a agregar
        """
        try:
            from PyPDF2 import PdfReader, PdfWriter

            reader = PdfReader(pdf_path)
            writer = PdfWriter()

            # Copiar todas las páginas
            for page in reader.pages:
                writer.add_page(page)

            # Agregar metadatos
            writer.add_metadata({
                '/Title': metadata.get('titulo', ''),
                '/Author': metadata.get('firmante', metadata.get('organo_emisor', '')),
                '/Subject': f"{metadata.get('tipo_norma', '')} - {metadata.get('area_derecho', '')}",
                '/Keywords': ', '.join(metadata.get('palabras_clave', [])[:10]),
                '/Producer': 'BÚHO Scraper - Bolivia',
                '/Creator': 'bo-gov-scraper-buho'
            })

            # Guardar PDF con metadatos
            output_path = pdf_path.replace('.pdf', '_con_metadatos.pdf')
            with open(output_path, 'wb') as output_file:
                writer.write(output_file)

            print(f"Metadatos agregados a: {output_path}")
            return output_path

        except Exception as e:
            print(f"Error al agregar metadatos al PDF: {e}")
            return None


if __name__ == "__main__":
    # Ejemplo de uso
    extractor = MetadataExtractor()

    texto_ejemplo = """
    LEY N° 1178

    LEY DE ADMINISTRACIÓN Y CONTROL GUBERNAMENTALES

    La Paz, 20 de julio de 1990

    Artículo 1.- La presente Ley regula los sistemas de Administración...
    Artículo 2.- Son objetivos de esta Ley...
    """

    metadatos = extractor.extraer_metadatos(
        texto_ejemplo,
        sitio_web="Gaceta Oficial de Bolivia",
        url_origen="https://ejemplo.com/ley1178.pdf"
    )

    print("Metadatos extraídos:")
    for clave, valor in metadatos.items():
        print(f"{clave}: {valor}")
