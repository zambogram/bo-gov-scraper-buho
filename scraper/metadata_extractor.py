"""
MÓDULO 2: METADATA EXTRACTOR
============================
Este módulo se encarga de:
1. Extraer metadatos de nombres de archivos y títulos de documentos
2. Identificar el tipo de norma (Ley, Decreto Supremo, Resolución, etc.)
3. Extraer número de norma y fecha
4. Identificar la entidad emisora (Ministerio, Presidencia, etc.)

Los documentos legales bolivianos siguen patrones como:
- "LEY N° 1234 DE 15 DE JULIO DE 2023"
- "DECRETO SUPREMO N° 5678 - 31 DE DICIEMBRE DE 2023"
- "RESOLUCIÓN MINISTERIAL N° 0123/2023"

Autor: Sistema BÚHO
"""

import re
from typing import Dict, Optional
from datetime import datetime
from dateutil import parser as date_parser


class MetadataExtractor:
    """
    Clase para extraer metadatos de documentos legales bolivianos.

    Los metadatos incluyen:
    - Tipo de norma (Ley, Decreto, Resolución, etc.)
    - Número de norma
    - Fecha de emisión
    - Entidad emisora
    """

    # Tipos de normas legales comunes en Bolivia
    TIPOS_NORMA = [
        'LEY',
        'DECRETO SUPREMO',
        'DECRETO LEY',
        'RESOLUCIÓN SUPREMA',
        'RESOLUCIÓN MINISTERIAL',
        'RESOLUCIÓN ADMINISTRATIVA',
        'RESOLUCIÓN BIMINISTERIAL',
        'DECRETO MUNICIPAL',
        'ORDENANZA MUNICIPAL',
        'LEY MUNICIPAL',
        'SENTENCIA CONSTITUCIONAL',
        'AUTO SUPREMO',
    ]

    # Meses en español
    MESES = {
        'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
        'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
        'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
    }

    def __init__(self):
        """Inicializa el extractor de metadatos."""
        pass

    def extract_tipo_norma(self, text: str) -> Optional[str]:
        """
        Extrae el tipo de norma del texto.

        Args:
            text: Texto del título o nombre del archivo

        Returns:
            Tipo de norma encontrado o None
        """
        text_upper = text.upper()

        for tipo in self.TIPOS_NORMA:
            if tipo in text_upper:
                return tipo

        return None

    def extract_numero_norma(self, text: str) -> Optional[str]:
        """
        Extrae el número de norma del texto.

        Busca patrones como:
        - N° 1234
        - Nº 5678
        - No. 0123
        - 1234/2023

        Args:
            text: Texto del título o nombre del archivo

        Returns:
            Número de norma o None
        """
        # Patrón para "N° 1234", "Nº 5678", "No. 0123"
        pattern1 = r'N[°ºo\.]\s*(\d+)'
        match = re.search(pattern1, text, re.IGNORECASE)
        if match:
            return match.group(1)

        # Patrón para "1234/2023" o "0123/23"
        pattern2 = r'(\d{3,5})[/-](\d{2,4})'
        match = re.search(pattern2, text)
        if match:
            return f"{match.group(1)}/{match.group(2)}"

        # Patrón para solo números después del tipo de norma
        pattern3 = r'(?:LEY|DECRETO|RESOLUCIÓN)\s+(\d{3,5})'
        match = re.search(pattern3, text, re.IGNORECASE)
        if match:
            return match.group(1)

        return None

    def extract_fecha(self, text: str) -> Optional[str]:
        """
        Extrae la fecha del documento.

        Busca patrones como:
        - "15 DE JULIO DE 2023"
        - "31-12-2023"
        - "2023-12-31"

        Args:
            text: Texto del título o nombre del archivo

        Returns:
            Fecha en formato ISO (YYYY-MM-DD) o None
        """
        text_lower = text.lower()

        # Patrón para "15 DE JULIO DE 2023"
        pattern_spanish = r'(\d{1,2})\s+de\s+([a-záéíóú]+)\s+de\s+(\d{4})'
        match = re.search(pattern_spanish, text_lower, re.IGNORECASE)
        if match:
            dia = int(match.group(1))
            mes_texto = match.group(2).lower()
            anio = int(match.group(3))

            if mes_texto in self.MESES:
                mes = self.MESES[mes_texto]
                try:
                    fecha = datetime(anio, mes, dia)
                    return fecha.strftime('%Y-%m-%d')
                except ValueError:
                    pass

        # Patrón para "31-12-2023" o "31/12/2023"
        pattern_numeric = r'(\d{1,2})[-/](\d{1,2})[-/](\d{4})'
        match = re.search(pattern_numeric, text)
        if match:
            dia = int(match.group(1))
            mes = int(match.group(2))
            anio = int(match.group(3))
            try:
                fecha = datetime(anio, mes, dia)
                return fecha.strftime('%Y-%m-%d')
            except ValueError:
                pass

        # Patrón para "2023-12-31" (formato ISO)
        pattern_iso = r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})'
        match = re.search(pattern_iso, text)
        if match:
            anio = int(match.group(1))
            mes = int(match.group(2))
            dia = int(match.group(3))
            try:
                fecha = datetime(anio, mes, dia)
                return fecha.strftime('%Y-%m-%d')
            except ValueError:
                pass

        return None

    def extract_entidad(self, text: str) -> Optional[str]:
        """
        Extrae la entidad emisora del documento.

        Args:
            text: Texto del título o nombre del archivo

        Returns:
            Entidad emisora o None
        """
        text_upper = text.upper()

        entidades = [
            'PRESIDENCIA',
            'MINISTERIO DE ECONOMÍA',
            'MINISTERIO DE EDUCACIÓN',
            'MINISTERIO DE SALUD',
            'MINISTERIO DE TRABAJO',
            'MINISTERIO DE GOBIERNO',
            'MINISTERIO DE JUSTICIA',
            'MINISTERIO DE DEFENSA',
            'MINISTERIO DE RELACIONES EXTERIORES',
            'ASAMBLEA LEGISLATIVA',
            'TRIBUNAL CONSTITUCIONAL',
            'ÓRGANO ELECTORAL',
        ]

        for entidad in entidades:
            if entidad in text_upper:
                return entidad

        return None

    def extract_all_metadata(self, text: str, filename: str = '') -> Dict[str, Optional[str]]:
        """
        FUNCIÓN PRINCIPAL: Extrae todos los metadatos de un documento.

        Esta es la función que debes llamar para extraer metadatos.

        Args:
            text: Texto del título del documento
            filename: Nombre del archivo (opcional, se usa como respaldo)

        Returns:
            Diccionario con todos los metadatos:
            - tipo_norma: Tipo de norma legal
            - numero_norma: Número de la norma
            - fecha_norma: Fecha de emisión (ISO format)
            - entidad_emisora: Entidad que emitió el documento
            - titulo_original: Texto original analizado
        """
        # Combinar título y nombre de archivo para tener más información
        combined_text = f"{text} {filename}"

        metadata = {
            'tipo_norma': self.extract_tipo_norma(combined_text),
            'numero_norma': self.extract_numero_norma(combined_text),
            'fecha_norma': self.extract_fecha(combined_text),
            'entidad_emisora': self.extract_entidad(combined_text),
            'titulo_original': text.strip()
        }

        return metadata

    def get_document_id(self, metadata: Dict[str, Optional[str]]) -> str:
        """
        Genera un ID único para el documento basado en sus metadatos.

        El ID tiene el formato: TIPO-NUMERO-FECHA
        Ejemplo: LEY-1234-2023-07-15

        Args:
            metadata: Diccionario de metadatos del documento

        Returns:
            ID único del documento
        """
        tipo = metadata.get('tipo_norma', 'DOCUMENTO')
        # Simplificar el tipo (primera palabra)
        tipo = tipo.split()[0] if tipo else 'DOC'

        numero = metadata.get('numero_norma', '0000')
        # Limpiar caracteres especiales del número
        numero = re.sub(r'[^0-9]', '', numero) if numero else '0000'

        fecha = metadata.get('fecha_norma', 'XXXX-XX-XX')

        document_id = f"{tipo}-{numero}-{fecha}"

        return document_id


def main():
    """
    Función de prueba del extractor de metadatos.

    NOTA PARA EL USUARIO:
    Esta es solo una función de prueba. Para usar el extractor en el pipeline
    completo, debes llamarlo desde main.py usando run_full_pipeline().
    """
    extractor = MetadataExtractor()

    # Ejemplos de títulos de documentos
    test_cases = [
        "LEY N° 1234 DE 15 DE JULIO DE 2023 - MINISTERIO DE ECONOMÍA",
        "DECRETO SUPREMO N° 5678 - 31 DE DICIEMBRE DE 2023",
        "RESOLUCIÓN MINISTERIAL N° 0123/2024 DE 10 DE ENERO DE 2024",
        "Ley 456 del 01-03-2023",
    ]

    print("\n" + "=" * 60)
    print("PRUEBA DE EXTRACCIÓN DE METADATOS")
    print("=" * 60)

    for i, test in enumerate(test_cases, 1):
        print(f"\nEjemplo {i}:")
        print(f"Título: {test}")
        print("-" * 60)

        metadata = extractor.extract_all_metadata(test)
        doc_id = extractor.get_document_id(metadata)

        print(f"Tipo de norma:    {metadata['tipo_norma']}")
        print(f"Número:           {metadata['numero_norma']}")
        print(f"Fecha:            {metadata['fecha_norma']}")
        print(f"Entidad:          {metadata['entidad_emisora']}")
        print(f"ID del documento: {doc_id}")


if __name__ == "__main__":
    main()
