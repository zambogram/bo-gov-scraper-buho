"""
MÓDULO 3: TEXT EXTRACTOR
========================
Este módulo se encarga de:
1. Determinar si un PDF es digital (con texto) o escaneado (imagen)
2. Extraer texto de PDFs digitales usando pdfplumber
3. Extraer texto de PDFs escaneados usando OCR (Tesseract)
4. Guardar el texto extraído en archivos .txt
5. Retornar metadatos sobre la extracción (páginas, caracteres, si usó OCR)

El proceso es:
- Primero intenta extracción digital (rápido)
- Si el PDF tiene poco texto (<100 caracteres), asume que es escaneado
- Usa OCR para PDFs escaneados (lento pero necesario)

Autor: Sistema BÚHO
"""

import os
from typing import Dict, Optional, Tuple
import pdfplumber
from pdf2image import convert_from_path
import pytesseract
from PIL import Image
import re


class TextExtractor:
    """
    Clase para extraer texto de PDFs usando métodos digitales o OCR.

    Funciona con:
    - PDFs digitales (texto seleccionable)
    - PDFs escaneados (imágenes que requieren OCR)
    """

    def __init__(self, text_output_dir: str = "data/text"):
        """
        Inicializa el extractor de texto.

        Args:
            text_output_dir: Carpeta donde se guardarán los archivos .txt
        """
        self.text_output_dir = text_output_dir
        os.makedirs(text_output_dir, exist_ok=True)

        # Umbral para determinar si un PDF es escaneado
        # Si tiene menos de esta cantidad de caracteres, asumimos que es escaneado
        self.DIGITAL_TEXT_THRESHOLD = 100

    def is_pdf_digital(self, pdf_path: str) -> Tuple[bool, int]:
        """
        Determina si un PDF es digital (tiene texto) o escaneado (es imagen).

        Args:
            pdf_path: Ruta al archivo PDF

        Returns:
            Tupla (es_digital, caracteres_encontrados)
        """
        try:
            with pdfplumber.open(pdf_path) as pdf:
                # Tomar las primeras 3 páginas como muestra
                sample_pages = min(3, len(pdf.pages))
                total_chars = 0

                for i in range(sample_pages):
                    page = pdf.pages[i]
                    text = page.extract_text() or ''
                    total_chars += len(text.strip())

                # Si hay suficiente texto, es digital
                is_digital = total_chars > self.DIGITAL_TEXT_THRESHOLD

                return is_digital, total_chars

        except Exception as e:
            print(f"    ⚠ Error al verificar tipo de PDF: {str(e)}")
            # En caso de error, asumimos que es escaneado y necesita OCR
            return False, 0

    def extract_text_digital(self, pdf_path: str) -> Optional[str]:
        """
        Extrae texto de un PDF digital usando pdfplumber.

        Este método es RÁPIDO pero solo funciona con PDFs que tienen texto.

        Args:
            pdf_path: Ruta al archivo PDF

        Returns:
            Texto extraído o None si falla
        """
        try:
            print(f"    → Extrayendo texto digital de: {os.path.basename(pdf_path)}")

            text_parts = []

            with pdfplumber.open(pdf_path) as pdf:
                total_pages = len(pdf.pages)
                print(f"      Total de páginas: {total_pages}")

                for i, page in enumerate(pdf.pages, 1):
                    page_text = page.extract_text() or ''
                    text_parts.append(page_text)

                    if i % 10 == 0:
                        print(f"      Procesadas {i}/{total_pages} páginas...")

            full_text = '\n\n'.join(text_parts)
            print(f"    ✓ Texto digital extraído: {len(full_text)} caracteres")

            return full_text

        except Exception as e:
            print(f"    ✗ Error en extracción digital: {str(e)}")
            return None

    def extract_text_ocr(self, pdf_path: str) -> Optional[str]:
        """
        Extrae texto de un PDF escaneado usando OCR (Tesseract).

        Este método es LENTO pero funciona con PDFs que son imágenes.

        IMPORTANTE: Requiere que Tesseract esté instalado en el sistema.
        - Ubuntu/Debian: sudo apt-get install tesseract-ocr tesseract-ocr-spa
        - macOS: brew install tesseract tesseract-lang
        - Windows: Descargar desde https://github.com/UB-Mannheim/tesseract/wiki

        Args:
            pdf_path: Ruta al archivo PDF

        Returns:
            Texto extraído o None si falla
        """
        try:
            print(f"    → Extrayendo texto con OCR de: {os.path.basename(pdf_path)}")
            print(f"      ⚠ ADVERTENCIA: OCR es lento, puede tomar varios minutos...")

            # Convertir PDF a imágenes
            print(f"      → Convirtiendo PDF a imágenes...")
            images = convert_from_path(pdf_path)
            total_pages = len(images)
            print(f"      Total de páginas: {total_pages}")

            text_parts = []

            for i, image in enumerate(images, 1):
                # Aplicar OCR a cada imagen
                page_text = pytesseract.image_to_string(image, lang='spa')
                text_parts.append(page_text)

                if i % 5 == 0:
                    print(f"      Procesadas {i}/{total_pages} páginas con OCR...")

            full_text = '\n\n'.join(text_parts)
            print(f"    ✓ Texto OCR extraído: {len(full_text)} caracteres")

            return full_text

        except Exception as e:
            print(f"    ✗ Error en OCR: {str(e)}")
            print(f"      Posible causa: Tesseract no está instalado.")
            print(f"      Instalar con: sudo apt-get install tesseract-ocr tesseract-ocr-spa")
            return None

    def save_text_to_file(self, text: str, pdf_filename: str) -> Optional[str]:
        """
        Guarda el texto extraído en un archivo .txt.

        Args:
            text: Texto a guardar
            pdf_filename: Nombre del PDF original (para generar el nombre del .txt)

        Returns:
            Ruta del archivo .txt guardado o None si falla
        """
        try:
            # Generar nombre del archivo .txt
            txt_filename = os.path.splitext(pdf_filename)[0] + '.txt'
            txt_path = os.path.join(self.text_output_dir, txt_filename)

            # Guardar texto
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(text)

            print(f"    ✓ Texto guardado en: {txt_filename}")
            return txt_path

        except Exception as e:
            print(f"    ✗ Error al guardar texto: {str(e)}")
            return None

    def extract_text_from_pdf(self, pdf_path: str) -> Optional[Dict[str, any]]:
        """
        FUNCIÓN PRINCIPAL: Extrae texto de un PDF (digital o escaneado).

        Esta es la función que debes llamar para extraer texto.
        Decide automáticamente si usar extracción digital o OCR.

        Args:
            pdf_path: Ruta al archivo PDF

        Returns:
            Diccionario con información de la extracción:
            - texto_extraido: Texto completo extraído
            - texto_path: Ruta del archivo .txt guardado
            - metodo_usado: 'digital' o 'ocr'
            - paginas: Número de páginas del PDF
            - caracteres: Número de caracteres extraídos
            - pdf_original: Ruta del PDF original
            - exito: True si la extracción fue exitosa

            None si la extracción falla completamente
        """
        print(f"\n  {'='*56}")
        print(f"  EXTRAYENDO TEXTO DE: {os.path.basename(pdf_path)}")
        print(f"  {'='*56}")

        # Verificar que el archivo existe
        if not os.path.exists(pdf_path):
            print(f"    ✗ El archivo no existe: {pdf_path}")
            return None

        # Paso 1: Determinar si es digital o escaneado
        print(f"  PASO 1: Verificando tipo de PDF...")
        is_digital, sample_chars = self.is_pdf_digital(pdf_path)

        if is_digital:
            print(f"    ✓ PDF digital detectado ({sample_chars} caracteres en muestra)")
            metodo = 'digital'
            texto = self.extract_text_digital(pdf_path)
        else:
            print(f"    ⚠ PDF escaneado detectado (solo {sample_chars} caracteres)")
            print(f"    → Se usará OCR (esto puede tomar varios minutos)")
            metodo = 'ocr'
            texto = self.extract_text_ocr(pdf_path)

        # Verificar si la extracción fue exitosa
        if not texto or len(texto.strip()) < 50:
            print(f"    ✗ No se pudo extraer texto suficiente del PDF")
            return {
                'texto_extraido': texto or '',
                'texto_path': None,
                'metodo_usado': metodo,
                'paginas': 0,
                'caracteres': len(texto) if texto else 0,
                'pdf_original': pdf_path,
                'exito': False
            }

        # Paso 2: Guardar texto en archivo
        print(f"\n  PASO 2: Guardando texto extraído...")
        pdf_filename = os.path.basename(pdf_path)
        texto_path = self.save_text_to_file(texto, pdf_filename)

        # Calcular estadísticas
        num_paginas = texto.count('\n\n') + 1  # Estimación aproximada
        num_caracteres = len(texto)

        print(f"\n  {'='*56}")
        print(f"  RESUMEN DE EXTRACCIÓN:")
        print(f"  - Método usado: {metodo.upper()}")
        print(f"  - Páginas estimadas: {num_paginas}")
        print(f"  - Caracteres extraídos: {num_caracteres:,}")
        print(f"  - Archivo guardado: {os.path.basename(texto_path) if texto_path else 'N/A'}")
        print(f"  {'='*56}\n")

        return {
            'texto_extraido': texto,
            'texto_path': texto_path,
            'metodo_usado': metodo,
            'paginas': num_paginas,
            'caracteres': num_caracteres,
            'pdf_original': pdf_path,
            'exito': True
        }


def main():
    """
    Función de prueba del extractor de texto.

    NOTA PARA EL USUARIO:
    Esta es solo una función de prueba. Para usar el extractor en el pipeline
    completo, debes llamarlo desde main.py usando run_full_pipeline().
    """
    import sys

    if len(sys.argv) < 2:
        print("Uso: python text_extractor.py <ruta_al_pdf>")
        print("\nEjemplo:")
        print("  python text_extractor.py data/pdfs/documento.pdf")
        sys.exit(1)

    pdf_path = sys.argv[1]

    extractor = TextExtractor()
    result = extractor.extract_text_from_pdf(pdf_path)

    if result and result['exito']:
        print(f"\n✓ Extracción exitosa!")
        print(f"  Archivo de texto: {result['texto_path']}")
    else:
        print(f"\n✗ La extracción falló.")


if __name__ == "__main__":
    main()
