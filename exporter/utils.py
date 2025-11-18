"""
Utilidades para el exportador de Supabase
Funciones de limpieza, normalización y generación de IDs
"""

import re
import unicodedata
from typing import Any, Dict, Optional
from datetime import datetime


def limpiar_texto(texto: str) -> str:
    """
    Limpia y normaliza texto para exportación a Supabase.

    Args:
        texto: Texto a limpiar

    Returns:
        Texto limpio y normalizado
    """
    if not texto:
        return ""

    # Normalizar caracteres Unicode a su forma compatible
    texto = unicodedata.normalize('NFKC', texto)

    # Reemplazar saltos de línea múltiples por espacios
    texto = re.sub(r'\n+', ' ', texto)

    # Reemplazar tabulaciones por espacios
    texto = re.sub(r'\t+', ' ', texto)

    # Reemplazar múltiples espacios por uno solo
    texto = re.sub(r'\s+', ' ', texto)

    # Eliminar espacios al inicio y final
    texto = texto.strip()

    return texto


def limpiar_texto_multilinea(texto: str) -> str:
    """
    Limpia texto preservando saltos de línea pero normalizándolos para JSONL.

    Args:
        texto: Texto a limpiar

    Returns:
        Texto con saltos de línea normalizados
    """
    if not texto:
        return ""

    # Normalizar caracteres Unicode
    texto = unicodedata.normalize('NFKC', texto)

    # Normalizar diferentes tipos de saltos de línea a \n
    texto = texto.replace('\r\n', '\n')
    texto = texto.replace('\r', '\n')

    # Eliminar líneas vacías múltiples
    texto = re.sub(r'\n{3,}', '\n\n', texto)

    # Eliminar espacios en blanco al final de cada línea
    lineas = [linea.rstrip() for linea in texto.split('\n')]
    texto = '\n'.join(lineas)

    # Eliminar espacios al inicio y final del texto completo
    texto = texto.strip()

    return texto


def limpiar_campos(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Limpia todos los campos de texto en un diccionario.

    Args:
        data: Diccionario con datos a limpiar

    Returns:
        Diccionario con campos limpios
    """
    cleaned = {}

    for key, value in data.items():
        if isinstance(value, str):
            # Para campos de contenido largo, preservar saltos de línea
            if key in ['contenido', 'raw', 'titulo', 'titulo_articulo', 'titulo_documento']:
                cleaned[key] = limpiar_texto_multilinea(value)
            else:
                cleaned[key] = limpiar_texto(value)
        elif isinstance(value, dict):
            cleaned[key] = limpiar_campos(value)
        elif isinstance(value, list):
            cleaned[key] = [limpiar_campos(item) if isinstance(item, dict) else item for item in value]
        else:
            cleaned[key] = value

    return cleaned


def normalizar_sitio(sitio: str) -> str:
    """
    Normaliza el nombre de un sitio a formato estándar.

    Args:
        sitio: Nombre del sitio

    Returns:
        Nombre normalizado (lowercase, guiones bajos)
    """
    if not sitio:
        return "desconocido"

    # Convertir a lowercase
    sitio = sitio.lower()

    # Reemplazar espacios y caracteres especiales por guiones bajos
    sitio = re.sub(r'[^\w]+', '_', sitio)

    # Eliminar guiones bajos múltiples
    sitio = re.sub(r'_+', '_', sitio)

    # Eliminar guiones bajos al inicio y final
    sitio = sitio.strip('_')

    return sitio


def generar_id_documento(
    sitio: str,
    tipo_norma: Optional[str] = None,
    numero_norma: Optional[str] = None,
    fecha_norma: Optional[str] = None
) -> str:
    """
    Genera un ID único para un documento.

    Formato: {sitio}_{tipo}_{numero}_{fecha}
    Ejemplo: gaceta_ley_1234_20231115

    Args:
        sitio: Nombre del sitio fuente
        tipo_norma: Tipo de norma (ley, decreto, resolución)
        numero_norma: Número de la norma
        fecha_norma: Fecha de la norma (YYYYMMDD o YYYY-MM-DD)

    Returns:
        ID único del documento
    """
    partes = []

    # Sitio (requerido)
    partes.append(normalizar_sitio(sitio))

    # Tipo de norma
    if tipo_norma:
        tipo_normalizado = re.sub(r'[^\w]+', '_', tipo_norma.lower())
        partes.append(tipo_normalizado)
    else:
        partes.append("doc")

    # Número de norma
    if numero_norma:
        numero_normalizado = re.sub(r'[^\w]+', '_', str(numero_norma))
        partes.append(numero_normalizado)
    else:
        # Si no hay número, usar timestamp
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        partes.append(timestamp)

    # Fecha de norma
    if fecha_norma:
        # Normalizar fecha a formato YYYYMMDD
        fecha_limpia = re.sub(r'[^\d]', '', fecha_norma)
        partes.append(fecha_limpia)

    return '_'.join(partes)


def generar_id_articulo(id_documento: str, numero_articulo: Optional[str] = None, orden: Optional[int] = None) -> str:
    """
    Genera un ID único para un artículo.

    Formato: {id_documento}_art{numero}
    Ejemplo: gaceta_ley_1234_20231115_art001

    Args:
        id_documento: ID del documento padre
        numero_articulo: Número del artículo
        orden: Orden del artículo dentro del documento

    Returns:
        ID único del artículo
    """
    if numero_articulo:
        # Extraer solo números del número de artículo
        num = re.sub(r'[^\d]', '', str(numero_articulo))
        if num:
            # Padding con ceros a la izquierda (3 dígitos)
            num_padded = num.zfill(3)
            return f"{id_documento}_art{num_padded}"

    # Si no hay número de artículo, usar el orden
    if orden is not None:
        orden_padded = str(orden).zfill(3)
        return f"{id_documento}_art{orden_padded}"

    # Último recurso: timestamp
    timestamp = datetime.now().strftime('%H%M%S%f')
    return f"{id_documento}_art{timestamp}"


def normalizar_tipo_norma(tipo: Optional[str]) -> Optional[str]:
    """
    Normaliza el tipo de norma a formato estándar.

    Args:
        tipo: Tipo de norma

    Returns:
        Tipo normalizado
    """
    if not tipo:
        return None

    tipo = tipo.lower().strip()

    # Mapeo de variantes comunes
    mapeo = {
        'ley': 'ley',
        'leyes': 'ley',
        'decreto': 'decreto',
        'decretos': 'decreto',
        'decreto supremo': 'decreto_supremo',
        'ds': 'decreto_supremo',
        'd.s.': 'decreto_supremo',
        'resolución': 'resolucion',
        'resolucion': 'resolucion',
        'resoluciones': 'resolucion',
        'sentencia': 'sentencia',
        'sentencias': 'sentencia',
        'auto': 'auto_supremo',
        'auto supremo': 'auto_supremo',
        'ordenanza': 'ordenanza',
        'reglamento': 'reglamento',
    }

    return mapeo.get(tipo, tipo.replace(' ', '_'))


def validar_documento(data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """
    Valida que un documento tenga los campos mínimos requeridos.

    Args:
        data: Diccionario con datos del documento

    Returns:
        Tupla (es_valido, mensaje_error)
    """
    campos_requeridos = ['id_documento', 'sitio']

    for campo in campos_requeridos:
        if campo not in data or not data[campo]:
            return False, f"Campo requerido faltante: {campo}"

    return True, None


def validar_articulo(data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """
    Valida que un artículo tenga los campos mínimos requeridos.

    Args:
        data: Diccionario con datos del artículo

    Returns:
        Tupla (es_valido, mensaje_error)
    """
    campos_requeridos = ['id_articulo', 'id_documento', 'contenido', 'sitio']

    for campo in campos_requeridos:
        if campo not in data or not data[campo]:
            return False, f"Campo requerido faltante: {campo}"

    return True, None


def normalizar_fecha(fecha: Optional[str]) -> Optional[str]:
    """
    Normaliza una fecha a formato YYYY-MM-DD.

    Args:
        fecha: Fecha en diferentes formatos

    Returns:
        Fecha normalizada o None
    """
    if not fecha:
        return None

    # Eliminar espacios
    fecha = fecha.strip()

    # Intentar parsear diferentes formatos
    formatos = [
        '%Y-%m-%d',
        '%d/%m/%Y',
        '%d-%m-%Y',
        '%Y%m%d',
        '%d.%m.%Y',
    ]

    for formato in formatos:
        try:
            dt = datetime.strptime(fecha, formato)
            return dt.strftime('%Y-%m-%d')
        except ValueError:
            continue

    # Si no se puede parsear, devolver la fecha original
    return fecha


def extraer_numero_articulo(texto: str) -> Optional[str]:
    """
    Extrae el número de artículo de un texto.

    Args:
        texto: Texto que contiene el número de artículo

    Returns:
        Número de artículo o None
    """
    if not texto:
        return None

    # Patrones comunes para números de artículo
    patrones = [
        r'art[íi]culo\s+(\d+)',
        r'art\.\s*(\d+)',
        r'artículo\s+(\w+)',
        r'^(\d+)[°º]?\.?\s',
        r'^\s*(\d+)\s*[-\.:]',
    ]

    for patron in patrones:
        match = re.search(patron, texto, re.IGNORECASE)
        if match:
            return match.group(1)

    return None
