"""
Utilidades comunes para scrapers
"""
import os
import re
import hashlib
import requests
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
from dateutil import parser as date_parser


def normalize_text(text: str) -> str:
    """Normaliza texto eliminando espacios extras y caracteres especiales"""
    if not text:
        return ""
    # Eliminar múltiples espacios
    text = re.sub(r'\s+', ' ', text)
    # Eliminar espacios al inicio y final
    text = text.strip()
    return text


def extract_date(text: str) -> Optional[str]:
    """
    Extrae fecha de un texto en varios formatos
    Retorna en formato ISO: YYYY-MM-DD
    """
    if not text:
        return None

    # Patrones de fecha en español
    patterns = [
        r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})',  # DD/MM/YYYY o DD-MM-YYYY
        r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})',  # YYYY/MM/DD o YYYY-MM-DD
        r'(\d{1,2})\s+de\s+(\w+)\s+de\s+(\d{4})',  # DD de Mes de YYYY
    ]

    meses_es = {
        'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
        'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
        'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
    }

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                if 'de' in pattern:
                    # Formato: DD de Mes de YYYY
                    day = int(match.group(1))
                    month_name = match.group(2).lower()
                    year = int(match.group(3))
                    month = meses_es.get(month_name)
                    if month:
                        return f"{year:04d}-{month:02d}-{day:02d}"
                elif match.group(1).isdigit() and len(match.group(1)) == 4:
                    # YYYY-MM-DD
                    return f"{match.group(1)}-{int(match.group(2)):02d}-{int(match.group(3)):02d}"
                else:
                    # DD/MM/YYYY
                    day, month, year = match.groups()
                    return f"{year}-{int(month):02d}-{int(day):02d}"
            except (ValueError, AttributeError):
                continue

    # Intentar con dateutil como último recurso
    try:
        dt = date_parser.parse(text, fuzzy=True, dayfirst=True)
        return dt.strftime('%Y-%m-%d')
    except:
        return None


def download_file(url: str, output_path: str, headers: Optional[Dict] = None,
                 timeout: int = 30) -> bool:
    """
    Descarga un archivo desde una URL

    Args:
        url: URL del archivo
        output_path: Ruta donde guardar el archivo
        headers: Headers HTTP opcionales
        timeout: Timeout en segundos

    Returns:
        True si la descarga fue exitosa, False en caso contrario
    """
    try:
        ensure_dir(os.path.dirname(output_path))

        response = requests.get(url, headers=headers, timeout=timeout, stream=True)
        response.raise_for_status()

        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        return True
    except Exception as e:
        print(f"Error descargando {url}: {e}")
        return False


def calculate_hash(file_path: str) -> str:
    """
    Calcula el hash MD5 de un archivo

    Args:
        file_path: Ruta al archivo

    Returns:
        Hash MD5 en formato hexadecimal
    """
    md5_hash = hashlib.md5()

    try:
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                md5_hash.update(chunk)
        return md5_hash.hexdigest()
    except Exception as e:
        print(f"Error calculando hash de {file_path}: {e}")
        return ""


def ensure_dir(directory: str) -> None:
    """
    Asegura que un directorio existe, creándolo si es necesario

    Args:
        directory: Ruta del directorio
    """
    if directory:
        Path(directory).mkdir(parents=True, exist_ok=True)


def clean_filename(filename: str, max_length: int = 200) -> str:
    """
    Limpia un nombre de archivo removiendo caracteres no válidos

    Args:
        filename: Nombre de archivo original
        max_length: Longitud máxima del nombre

    Returns:
        Nombre de archivo limpio
    """
    # Remover caracteres no válidos
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remover espacios extras
    filename = re.sub(r'\s+', '_', filename)
    # Limitar longitud
    if len(filename) > max_length:
        name, ext = os.path.splitext(filename)
        name = name[:max_length - len(ext)]
        filename = name + ext
    return filename


def extract_numero_documento(text: str) -> Optional[str]:
    """
    Extrae número de documento de un texto
    Formatos: SC-0123/2024, SCP 0123/2024-S1, AS-123, etc.

    Args:
        text: Texto donde buscar

    Returns:
        Número de documento encontrado o None
    """
    patterns = [
        r'(SC[PA]?)\s*[-\s]*(\d+)[/-](\d{4})(?:-S\d)?',  # SCP-0123/2024-S1
        r'(AS|AUTO\s+SUPREMO)\s*[-\s]*(\d+)[/-](\d{4})',  # AS-123/2024
        r'(RES(?:OLUCI[OÓ]N)?)\s*[-\s]*(\d+)[/-](\d{4})',  # RESOLUCIÓN 123/2024
        r'(RND|RA)\s*[-\s]*(\d+)[/-](\d{4})',  # RND-123/2024
        r'([A-Z]{2,4})\s*[-\s]*(\d+)[/-](\d{4})',  # Patrón genérico
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(0).strip()

    return None


def format_timestamp() -> str:
    """
    Retorna timestamp actual en formato legible

    Returns:
        Timestamp en formato YYYY-MM-DD HH:MM:SS
    """
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def get_file_size(file_path: str) -> int:
    """
    Obtiene el tamaño de un archivo en bytes

    Args:
        file_path: Ruta al archivo

    Returns:
        Tamaño en bytes o 0 si no existe
    """
    try:
        return os.path.getsize(file_path)
    except:
        return 0
