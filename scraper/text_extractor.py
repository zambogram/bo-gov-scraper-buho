"""
Módulo para extracción de texto de PDFs usando OCR y métodos digitales.
FASE 4 del proyecto: OCR y extracción de texto.
"""

import os
import re
import logging
from pathlib import Path
from typing import Dict, Tuple, Optional

# PDF processing
import fitz  # PyMuPDF
from pdfminer.high_level import extract_text as pdfminer_extract_text
from pdf2image import convert_from_path

# OCR
import pytesseract
from PIL import Image

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def is_scanned_pdf(pdf_path: str, threshold: int = 100) -> bool:
    """
    Detecta si un PDF es escaneado o digital.

    Estrategia:
    1. Intenta extraer texto de la primera página usando PyMuPDF
    2. Si el texto extraído tiene menos de 'threshold' caracteres → es escaneado
    3. Si tiene más texto → es digital

    Args:
        pdf_path: Ruta al archivo PDF
        threshold: Umbral mínimo de caracteres para considerar PDF digital

    Returns:
        True si el PDF es escaneado, False si es digital
    """
    try:
        doc = fitz.open(pdf_path)

        if len(doc) == 0:
            logger.warning(f"PDF vacío: {pdf_path}")
            return False

        # Extraer texto de la primera página
        first_page = doc[0]
        text = first_page.get_text()

        # Limpiar espacios en blanco
        text_cleaned = re.sub(r'\s+', '', text)

        doc.close()

        # Si tiene muy poco texto, probablemente es escaneado
        is_scanned = len(text_cleaned) < threshold

        logger.info(f"PDF: {os.path.basename(pdf_path)} - "
                   f"Caracteres: {len(text_cleaned)} - "
                   f"Tipo: {'ESCANEADO' if is_scanned else 'DIGITAL'}")

        return is_scanned

    except Exception as e:
        logger.error(f"Error al analizar PDF {pdf_path}: {e}")
        # En caso de error, asumir que es escaneado y aplicar OCR
        return True


def extract_text_scanned(pdf_path: str, lang: str = 'spa') -> str:
    """
    Extrae texto de un PDF escaneado usando OCR con Tesseract.

    Args:
        pdf_path: Ruta al archivo PDF escaneado
        lang: Idioma para OCR (default: español)

    Returns:
        Texto extraído del PDF
    """
    try:
        logger.info(f"Aplicando OCR a: {os.path.basename(pdf_path)}")

        # Convertir PDF a imágenes (una por página)
        images = convert_from_path(pdf_path)

        extracted_text = []

        for i, image in enumerate(images, 1):
            logger.info(f"  Procesando página {i}/{len(images)}")

            # Aplicar OCR a la imagen
            page_text = pytesseract.image_to_string(image, lang=lang)
            extracted_text.append(page_text)

        full_text = "\n\n--- PÁGINA {} ---\n\n".join(extracted_text)

        logger.info(f"OCR completado: {len(full_text)} caracteres extraídos")

        return full_text

    except Exception as e:
        logger.error(f"Error en OCR de {pdf_path}: {e}")
        return ""


def extract_text_digital(pdf_path: str) -> str:
    """
    Extrae texto de un PDF digital usando PyMuPDF.

    Args:
        pdf_path: Ruta al archivo PDF digital

    Returns:
        Texto extraído del PDF
    """
    try:
        logger.info(f"Extrayendo texto digital de: {os.path.basename(pdf_path)}")

        doc = fitz.open(pdf_path)
        extracted_text = []

        for page_num in range(len(doc)):
            page = doc[page_num]
            page_text = page.get_text()
            extracted_text.append(page_text)

        doc.close()

        full_text = "\n\n--- PÁGINA {} ---\n\n".join(extracted_text)

        logger.info(f"Extracción digital completada: {len(full_text)} caracteres")

        return full_text

    except Exception as e:
        logger.error(f"Error al extraer texto digital de {pdf_path}: {e}")
        # Fallback: intentar con pdfminer
        try:
            logger.info("Intentando con pdfminer como fallback...")
            text = pdfminer_extract_text(pdf_path)
            return text
        except Exception as e2:
            logger.error(f"Error con pdfminer: {e2}")
            return ""


def clean_text(raw_text: str) -> str:
    """
    Limpia y normaliza el texto extraído.

    Operaciones:
    - Elimina espacios múltiples
    - Normaliza saltos de línea
    - Elimina caracteres especiales problemáticos
    - Elimina líneas vacías múltiples

    Args:
        raw_text: Texto sin procesar

    Returns:
        Texto limpio y normalizado
    """
    if not raw_text:
        return ""

    # Eliminar caracteres de control extraños (excepto \n, \t)
    text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]', '', raw_text)

    # Normalizar espacios horizontales
    text = re.sub(r'[ \t]+', ' ', text)

    # Normalizar saltos de línea múltiples (máximo 2)
    text = re.sub(r'\n{3,}', '\n\n', text)

    # Eliminar espacios al inicio y final de cada línea
    lines = [line.strip() for line in text.split('\n')]
    text = '\n'.join(lines)

    # Eliminar espacios al inicio y final del documento
    text = text.strip()

    return text


def save_text(pdf_path: str, text: str, output_dir: str = 'data/text') -> str:
    """
    Guarda el texto extraído en un archivo .txt.

    Args:
        pdf_path: Ruta original del PDF
        text: Texto extraído
        output_dir: Directorio donde guardar el texto

    Returns:
        Ruta del archivo .txt creado
    """
    # Crear directorio si no existe
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Generar nombre del archivo .txt basado en el PDF
    pdf_basename = os.path.basename(pdf_path)
    txt_filename = os.path.splitext(pdf_basename)[0] + '.txt'
    txt_path = os.path.join(output_dir, txt_filename)

    # Guardar texto
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write(text)

    logger.info(f"Texto guardado en: {txt_path}")

    return txt_path


def get_pdf_page_count(pdf_path: str) -> int:
    """
    Obtiene el número de páginas de un PDF.

    Args:
        pdf_path: Ruta al archivo PDF

    Returns:
        Número de páginas
    """
    try:
        doc = fitz.open(pdf_path)
        page_count = len(doc)
        doc.close()
        return page_count
    except Exception as e:
        logger.error(f"Error al contar páginas de {pdf_path}: {e}")
        return 0


def process_pdf(pdf_path: str, output_dir: str = 'data/text') -> Dict:
    """
    Procesa un PDF: detecta tipo, extrae texto, limpia y guarda.

    Función principal que orquesta todo el pipeline de extracción.

    Args:
        pdf_path: Ruta al archivo PDF
        output_dir: Directorio donde guardar el texto

    Returns:
        Diccionario con resultados:
        {
            'pdf_path': str,
            'is_scanned': bool,
            'ocr_usado': bool,
            'paginas': int,
            'caracteres_extraidos': int,
            'texto_extraido': bool,
            'txt_path': str,
            'error': str (opcional)
        }
    """
    result = {
        'pdf_path': pdf_path,
        'is_scanned': False,
        'ocr_usado': False,
        'paginas': 0,
        'caracteres_extraidos': 0,
        'texto_extraido': False,
        'txt_path': '',
        'error': ''
    }

    try:
        # Verificar que el archivo existe
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF no encontrado: {pdf_path}")

        # Obtener número de páginas
        result['paginas'] = get_pdf_page_count(pdf_path)

        # Detectar si es escaneado o digital
        is_scanned = is_scanned_pdf(pdf_path)
        result['is_scanned'] = is_scanned

        # Extraer texto según el tipo
        if is_scanned:
            raw_text = extract_text_scanned(pdf_path)
            result['ocr_usado'] = True
        else:
            raw_text = extract_text_digital(pdf_path)
            result['ocr_usado'] = False

        # Limpiar texto
        clean_txt = clean_text(raw_text)
        result['caracteres_extraidos'] = len(clean_txt)

        # Guardar texto
        if clean_txt:
            txt_path = save_text(pdf_path, clean_txt, output_dir)
            result['txt_path'] = txt_path
            result['texto_extraido'] = True
        else:
            logger.warning(f"No se extrajo texto de: {pdf_path}")
            result['texto_extraido'] = False

    except Exception as e:
        logger.error(f"Error procesando {pdf_path}: {e}")
        result['error'] = str(e)

    return result


def process_multiple_pdfs(pdf_list: list, output_dir: str = 'data/text') -> list:
    """
    Procesa múltiples PDFs y retorna resultados.

    Args:
        pdf_list: Lista de rutas a archivos PDF
        output_dir: Directorio donde guardar los textos

    Returns:
        Lista de diccionarios con resultados de cada PDF
    """
    results = []

    for i, pdf_path in enumerate(pdf_list, 1):
        logger.info(f"\n{'='*60}")
        logger.info(f"Procesando PDF {i}/{len(pdf_list)}: {os.path.basename(pdf_path)}")
        logger.info(f"{'='*60}")

        result = process_pdf(pdf_path, output_dir)
        results.append(result)

    return results


def print_summary(results: list):
    """
    Imprime un resumen de los resultados de procesamiento.

    Args:
        results: Lista de resultados de process_pdf()
    """
    print("\n" + "="*70)
    print("RESUMEN DE EXTRACCIÓN DE TEXTO")
    print("="*70)

    for i, result in enumerate(results, 1):
        print(f"\n{i}. {os.path.basename(result['pdf_path'])}")
        print(f"   Tipo: {'ESCANEADO' if result['is_scanned'] else 'DIGITAL'}")
        print(f"   OCR usado: {'SÍ' if result['ocr_usado'] else 'NO'}")
        print(f"   Páginas: {result['paginas']}")
        print(f"   Caracteres extraídos: {result['caracteres_extraidos']:,}")
        print(f"   Texto extraído: {'SÍ' if result['texto_extraido'] else 'NO'}")

        if result['texto_extraido']:
            print(f"   Archivo generado: {result['txt_path']}")

        if result.get('error'):
            print(f"   ⚠️  Error: {result['error']}")

    print("\n" + "="*70)

    # Estadísticas generales
    total = len(results)
    escaneados = sum(1 for r in results if r['is_scanned'])
    digitales = total - escaneados
    con_ocr = sum(1 for r in results if r['ocr_usado'])
    exitosos = sum(1 for r in results if r['texto_extraido'])

    print(f"\nEstadísticas:")
    print(f"  Total PDFs procesados: {total}")
    print(f"  PDFs digitales: {digitales}")
    print(f"  PDFs escaneados: {escaneados}")
    print(f"  OCR aplicado: {con_ocr}")
    print(f"  Extracciones exitosas: {exitosos}/{total}")
    print("="*70 + "\n")
