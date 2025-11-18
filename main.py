#!/usr/bin/env python3
"""
FASE 4: OCR y Extracción de Texto de PDFs
Script principal para procesar PDFs del scraper de gobierno boliviano.
"""

import os
import sys
import glob
import pandas as pd
from pathlib import Path

from scraper.text_extractor import (
    process_pdf,
    process_multiple_pdfs,
    print_summary
)


def get_sample_pdfs(pdf_dir: str = 'data/pdfs', max_pdfs: int = 5):
    """
    Obtiene una lista de PDFs de muestra para procesar.

    Args:
        pdf_dir: Directorio donde buscar PDFs
        max_pdfs: Número máximo de PDFs a procesar

    Returns:
        Lista de rutas a PDFs
    """
    pdf_pattern = os.path.join(pdf_dir, '*.pdf')
    pdf_files = glob.glob(pdf_pattern)

    if not pdf_files:
        print(f"⚠️  No se encontraron PDFs en {pdf_dir}")
        print(f"\nPor favor, coloca algunos PDFs en el directorio '{pdf_dir}' para probar.")
        return []

    # Limitar al número máximo
    pdf_files = pdf_files[:max_pdfs]

    return pdf_files


def update_csv_with_results(csv_path: str, results: list):
    """
    Actualiza el CSV de metadatos con información de extracción de texto.

    Agrega/actualiza las columnas:
    - texto_extraido (sí/no)
    - ocr_usado (sí/no)
    - paginas (cantidad)
    - caracteres_extraidos
    - ruta_texto

    Args:
        csv_path: Ruta al CSV de metadatos
        results: Lista de resultados de process_pdf()
    """
    # Verificar si el CSV existe
    if not os.path.exists(csv_path):
        print(f"⚠️  CSV no encontrado: {csv_path}")
        print("Creando nuevo CSV con los resultados...")

        # Crear DataFrame desde los resultados
        df_data = []
        for result in results:
            df_data.append({
                'pdf_filename': os.path.basename(result['pdf_path']),
                'pdf_path': result['pdf_path'],
                'texto_extraido': 'sí' if result['texto_extraido'] else 'no',
                'ocr_usado': 'sí' if result['ocr_usado'] else 'no',
                'paginas': result['paginas'],
                'caracteres_extraidos': result['caracteres_extraidos'],
                'ruta_texto': result.get('txt_path', ''),
                'tipo_pdf': 'escaneado' if result['is_scanned'] else 'digital',
                'error': result.get('error', '')
            })

        df = pd.DataFrame(df_data)
        df.to_csv(csv_path, index=False, encoding='utf-8')
        print(f"✅ CSV creado: {csv_path}")

    else:
        # Cargar CSV existente
        df = pd.read_csv(csv_path)

        # Crear un diccionario de resultados por nombre de archivo
        results_dict = {
            os.path.basename(r['pdf_path']): r
            for r in results
        }

        # Agregar columnas si no existen
        if 'texto_extraido' not in df.columns:
            df['texto_extraido'] = ''
        if 'ocr_usado' not in df.columns:
            df['ocr_usado'] = ''
        if 'paginas' not in df.columns:
            df['paginas'] = 0
        if 'caracteres_extraidos' not in df.columns:
            df['caracteres_extraidos'] = 0
        if 'ruta_texto' not in df.columns:
            df['ruta_texto'] = ''
        if 'tipo_pdf' not in df.columns:
            df['tipo_pdf'] = ''

        # Actualizar filas con los resultados
        for idx, row in df.iterrows():
            pdf_filename = os.path.basename(row.get('pdf_path', ''))

            if pdf_filename in results_dict:
                result = results_dict[pdf_filename]

                df.at[idx, 'texto_extraido'] = 'sí' if result['texto_extraido'] else 'no'
                df.at[idx, 'ocr_usado'] = 'sí' if result['ocr_usado'] else 'no'
                df.at[idx, 'paginas'] = result['paginas']
                df.at[idx, 'caracteres_extraidos'] = result['caracteres_extraidos']
                df.at[idx, 'ruta_texto'] = result.get('txt_path', '')
                df.at[idx, 'tipo_pdf'] = 'escaneado' if result['is_scanned'] else 'digital'

        # Guardar CSV actualizado
        df.to_csv(csv_path, index=False, encoding='utf-8')
        print(f"✅ CSV actualizado: {csv_path}")


def main():
    """
    Función principal para probar la extracción de texto.
    """
    print("\n" + "="*70)
    print("FASE 4: OCR Y EXTRACCIÓN DE TEXTO DE PDFs")
    print("Sistema de procesamiento de documentos del Estado Boliviano")
    print("="*70 + "\n")

    # Configuración
    PDF_DIR = 'data/pdfs'
    TEXT_DIR = 'data/text'
    CSV_PATH = 'data/csv/documentos_metadata.csv'
    MAX_PDFS = 5

    # Crear directorios si no existen
    Path(PDF_DIR).mkdir(parents=True, exist_ok=True)
    Path(TEXT_DIR).mkdir(parents=True, exist_ok=True)
    Path('data/csv').mkdir(parents=True, exist_ok=True)

    # Obtener PDFs de muestra
    print(f"Buscando PDFs en: {PDF_DIR}")
    pdf_files = get_sample_pdfs(PDF_DIR, MAX_PDFS)

    if not pdf_files:
        print("\n" + "="*70)
        print("INSTRUCCIONES PARA PROBAR EL SISTEMA:")
        print("="*70)
        print(f"1. Coloca algunos PDFs (3-5) en el directorio: {PDF_DIR}/")
        print(f"2. Ejecuta nuevamente: python main.py")
        print(f"3. El sistema detectará automáticamente si son escaneados o digitales")
        print(f"4. Los textos extraídos se guardarán en: {TEXT_DIR}/")
        print(f"5. El CSV con metadatos se guardará en: {CSV_PATH}")
        print("="*70 + "\n")
        return

    print(f"✅ Encontrados {len(pdf_files)} PDFs para procesar\n")

    # Procesar PDFs
    results = process_multiple_pdfs(pdf_files, TEXT_DIR)

    # Mostrar resumen
    print_summary(results)

    # Actualizar CSV
    print(f"\nActualizando CSV de metadatos...")
    update_csv_with_results(CSV_PATH, results)

    print("\n✅ Proceso completado exitosamente!\n")


if __name__ == '__main__':
    main()
