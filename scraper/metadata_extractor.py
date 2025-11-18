"""
Módulo para extracción y normalización de metadatos legales
de documentos de la Gaceta Oficial de Bolivia.

Este módulo detecta automáticamente:
- Tipo de norma (Ley, Decreto Supremo, Resolución, etc.)
- Número de norma
- Fecha aproximada de publicación desde el título

Autor: BÚHO - Bolivia
Fase: 3 (Metadata Extraction)
"""

import re
from typing import Optional, Dict
from datetime import datetime


def detect_norma_type(titulo: str) -> str:
    """
    Detecta el tipo de norma a partir del título.

    Patrones soportados:
    - Ley, Leyes
    - Decreto Supremo, DS, D.S.
    - Resolución Ministerial, RM, R.M.
    - Resolución Administrativa, RA, R.A.
    - Resolución Suprema, RS, R.S.
    - Resolución Bi-ministerial, RB, R.B.
    - Decreto Ley, DL, D.L.
    - Sentencia Constitucional
    - Auto Supremo

    Args:
        titulo: Título del documento

    Returns:
        Tipo de norma detectado o "Desconocido"
    """
    titulo_upper = titulo.upper()

    # Patrones ordenados por especificidad (más específico primero)
    patterns = [
        (r'\bSENTENCIA\s+CONSTITUCIONAL\b', 'Sentencia Constitucional'),
        (r'\bAUTO\s+SUPREMO\b', 'Auto Supremo'),
        (r'\bDECRETO\s+LEY\b|\bD\.?\s*L\.?\b', 'Decreto Ley'),
        (r'\bDECRETO\s+SUPREMO\b|\bD\.?\s*S\.?\b', 'Decreto Supremo'),
        (r'\bRESOLUCI[ÓO]N\s+BI-?MINISTERIAL\b|\bR\.?\s*B\.?\b', 'Resolución Bi-Ministerial'),
        (r'\bRESOLUCI[ÓO]N\s+MINISTERIAL\b|\bR\.?\s*M\.?\b', 'Resolución Ministerial'),
        (r'\bRESOLUCI[ÓO]N\s+ADMINISTRATIVA\b|\bR\.?\s*A\.?\b', 'Resolución Administrativa'),
        (r'\bRESOLUCI[ÓO]N\s+SUPREMA\b|\bR\.?\s*S\.?\b', 'Resolución Suprema'),
        (r'\bRESOLUCI[ÓO]N\b', 'Resolución'),
        (r'\bLEY(?:ES)?\b', 'Ley'),
        (r'\bDECRETO\b', 'Decreto'),
    ]

    for pattern, tipo in patterns:
        if re.search(pattern, titulo_upper):
            return tipo

    return "Desconocido"


def extract_norma_number(titulo: str) -> Optional[str]:
    """
    Extrae el número de norma del título.

    Patrones soportados:
    - "Ley 123"
    - "Ley N° 123"
    - "Ley Nº 123"
    - "Ley No. 123"
    - "DS 456"
    - "RM 789-2023"
    - "Resolución 10/2022"
    - "Ley 123/2023"

    Args:
        titulo: Título del documento

    Returns:
        Número de norma extraído o None si no se detecta
    """
    titulo_upper = titulo.upper()

    # Patrones de extracción de números
    # Formato: (LEY|DS|RM|etc.) seguido de separador y número
    patterns = [
        # Patrón con N°, Nº, No., No
        r'(?:LEY|DECRETO|DS|D\.S\.|RM|R\.M\.|RA|R\.A\.|RS|R\.S\.|RB|R\.B\.|DL|D\.L\.|RESOLUCI[ÓO]N)\s+(?:N[°º]?\.?\s*|NO\.?\s*)?(\d+(?:[-/]\d+)*)',
        # Patrón sin prefijo explícito pero con números claros
        r'(?:LEY|DECRETO|DS|RM|RA|RS|RB|DL|RESOLUCI[ÓO]N).*?(\d{1,5}(?:[-/]\d+)?)',
    ]

    for pattern in patterns:
        match = re.search(pattern, titulo_upper)
        if match:
            numero = match.group(1)
            # Limpiar y normalizar
            numero = numero.strip()
            return numero

    return None


def extract_date_from_title(titulo: str) -> Optional[str]:
    """
    Extrae la fecha de publicación del título si está disponible.

    Patrones soportados:
    - "de 2023"
    - "del 15 de enero de 2023"
    - "15/01/2023"
    - "2023-01-15"
    - "enero 2023"
    - "01/2023"

    Args:
        titulo: Título del documento

    Returns:
        Fecha en formato ISO (YYYY-MM-DD o YYYY-MM o YYYY) o None
    """
    titulo_lower = titulo.lower()

    # Mapa de meses en español
    meses = {
        'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04',
        'mayo': '05', 'junio': '06', 'julio': '07', 'agosto': '08',
        'septiembre': '09', 'octubre': '10', 'noviembre': '11', 'diciembre': '12'
    }

    # Patrón 1: Fecha completa "15 de enero de 2023"
    for mes_nombre, mes_num in meses.items():
        pattern = rf'(\d{{1,2}})\s+de\s+{mes_nombre}\s+de\s+(\d{{4}})'
        match = re.search(pattern, titulo_lower)
        if match:
            dia = match.group(1).zfill(2)
            anio = match.group(2)
            return f"{anio}-{mes_num}-{dia}"

    # Patrón 2: Mes y año "enero de 2023" o "enero 2023"
    for mes_nombre, mes_num in meses.items():
        pattern = rf'{mes_nombre}\s+(?:de\s+)?(\d{{4}})'
        match = re.search(pattern, titulo_lower)
        if match:
            anio = match.group(1)
            return f"{anio}-{mes_num}"

    # Patrón 3: Formato DD/MM/YYYY o DD-MM-YYYY
    match = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', titulo)
    if match:
        dia = match.group(1).zfill(2)
        mes = match.group(2).zfill(2)
        anio = match.group(3)
        return f"{anio}-{mes}-{dia}"

    # Patrón 4: Formato ISO YYYY-MM-DD
    match = re.search(r'(\d{4})-(\d{2})-(\d{2})', titulo)
    if match:
        return match.group(0)

    # Patrón 5: MM/YYYY
    match = re.search(r'(\d{2})/(\d{4})', titulo)
    if match:
        mes = match.group(1)
        anio = match.group(2)
        return f"{anio}-{mes}"

    # Patrón 6: Solo año "de 2023" o "del 2023"
    match = re.search(r'(?:del?\s+)?(\d{4})', titulo_lower)
    if match:
        anio = match.group(1)
        # Validar que sea un año razonable (1900-2100)
        if 1900 <= int(anio) <= 2100:
            return anio

    return None


def extract_all_metadata(titulo: str, url_pdf: str) -> Dict[str, Optional[str]]:
    """
    Extrae todos los metadatos disponibles de un documento.

    Args:
        titulo: Título del documento
        url_pdf: URL del PDF

    Returns:
        Diccionario con todos los metadatos extraídos:
        {
            'tipo_norma': str,
            'numero_norma': str | None,
            'fecha_publicacion_aproximada': str | None,
            'titulo_original': str,
            'url_pdf': str
        }
    """
    metadata = {
        'tipo_norma': detect_norma_type(titulo),
        'numero_norma': extract_norma_number(titulo),
        'fecha_publicacion_aproximada': extract_date_from_title(titulo),
        'titulo_original': titulo,
        'url_pdf': url_pdf
    }

    return metadata


def format_metadata_for_display(metadata: Dict) -> str:
    """
    Formatea los metadatos para mostrar en consola de forma legible.

    Args:
        metadata: Diccionario de metadatos

    Returns:
        String formateado para imprimir
    """
    lines = []
    lines.append(f"  Tipo: {metadata.get('tipo_norma', 'N/A')}")
    lines.append(f"  Número: {metadata.get('numero_norma', 'N/A')}")
    lines.append(f"  Fecha: {metadata.get('fecha_publicacion_aproximada', 'N/A')}")
    lines.append(f"  Título: {metadata.get('titulo_original', 'N/A')[:80]}...")

    return "\n".join(lines)


# Función de prueba para desarrollo
if __name__ == "__main__":
    # Casos de prueba
    test_cases = [
        "Ley N° 123 de 2023",
        "Decreto Supremo 456",
        "DS 456-2023 del 15 de enero de 2023",
        "Resolución Ministerial 789-2023",
        "RM 789/2022",
        "Resolución Administrativa 10/2022",
        "Ley 1234 del 25 de diciembre de 2020",
        "Sentencia Constitucional 045/2021",
        "Auto Supremo 123",
    ]

    print("="*80)
    print("PRUEBAS DE EXTRACCIÓN DE METADATOS")
    print("="*80)

    for titulo in test_cases:
        print(f"\nTítulo: {titulo}")
        metadata = extract_all_metadata(titulo, "http://example.com/test.pdf")
        print(format_metadata_for_display(metadata))
