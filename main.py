"""
SISTEMA BÚHO - PIPELINE END-TO-END
===================================
Este es el archivo principal que ejecuta el pipeline completo de procesamiento
de documentos legales de la Gaceta Oficial de Bolivia.

FLUJO COMPLETO:
1. Descarga PDFs de la Gaceta Oficial
2. Extrae metadatos (tipo, número, fecha, etc.)
3. Extrae texto (digital o con OCR)
4. Segmenta artículos del documento
5. Genera JSONs estructurados
6. Actualiza CSVs de documentos y artículos

AUTOR: Sistema BÚHO
FASE: 6 - Integración End-to-End
"""

import os
import sys
from datetime import datetime
from typing import List, Dict, Optional

# Importar todos los módulos del pipeline
from scraper.gaceta_scraper import GacetaScraper
from scraper.metadata_extractor import MetadataExtractor
from scraper.text_extractor import TextExtractor
from scraper.legal_parser import LegalParser
from scraper.csv_manager import CSVManager


def run_full_pipeline(
    url_inicial: str,
    limite_documentos: int = 5,
    forzar_reprocesar: bool = False
) -> Dict[str, any]:
    """
    FUNCIÓN PRINCIPAL DEL PIPELINE END-TO-END
    ==========================================

    Esta función ejecuta TODO el flujo de procesamiento desde una URL de la Gaceta
    hasta los CSVs y JSONs finales.

    Args:
        url_inicial: URL de la página de listado de la Gaceta Oficial
        limite_documentos: Número máximo de documentos a procesar (default: 5)
        forzar_reprocesar: Si True, reprocesa documentos ya existentes (default: False)

    Returns:
        Diccionario con resumen de la ejecución:
        - documentos_descargados: Número de PDFs descargados
        - documentos_nuevos: Número de documentos nuevos (no existían antes)
        - documentos_procesados: Número de documentos procesados exitosamente
        - total_articulos: Número total de artículos extraídos
        - errores: Lista de errores encontrados
        - rutas: Diccionario con rutas de archivos generados

    PASOS DEL PIPELINE:
    -------------------
    1. SCRAPING: Descarga PDFs de la Gaceta Oficial
    2. METADATA: Extrae metadatos de títulos y nombres
    3. TEXT EXTRACTION: Extrae texto de PDFs (digital/OCR)
    4. PARSING: Segmenta texto en artículos
    5. JSON GENERATION: Genera JSONs estructurados
    6. CSV UPDATE: Actualiza CSVs de documentos y artículos
    """

    print("\n" + "=" * 80)
    print(" " * 20 + "SISTEMA BÚHO - PIPELINE END-TO-END")
    print("=" * 80)
    print(f"\nFecha de ejecución: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"URL inicial: {url_inicial}")
    print(f"Límite de documentos: {limite_documentos}")
    print(f"Forzar reprocesar: {forzar_reprocesar}")
    print("=" * 80 + "\n")

    # Inicializar componentes del pipeline
    scraper = GacetaScraper(output_dir="data/pdfs")
    metadata_extractor = MetadataExtractor()
    text_extractor = TextExtractor(text_output_dir="data/text")
    legal_parser = LegalParser()
    csv_manager = CSVManager(csv_dir="data/csv")

    # Variables para rastrear el progreso
    documentos_procesados = 0
    documentos_nuevos = 0
    total_articulos = 0
    errores = []

    # Obtener documentos ya procesados (para evitar duplicados)
    existing_ids = csv_manager.get_existing_document_ids()
    print(f"📊 Documentos ya procesados en CSV: {len(existing_ids)}\n")

    # =========================================================================
    # PASO 1: SCRAPING - Descargar PDFs de la Gaceta
    # =========================================================================
    print("=" * 80)
    print("PASO 1/6: SCRAPING - Descargando PDFs de la Gaceta Oficial")
    print("=" * 80)

    downloaded_docs = scraper.scrape_gaceta(url_inicial, max_documents=limite_documentos)

    if not downloaded_docs:
        print("\n❌ ERROR: No se descargaron documentos. Abortando pipeline.")
        return {
            'documentos_descargados': 0,
            'documentos_nuevos': 0,
            'documentos_procesados': 0,
            'total_articulos': 0,
            'errores': ['No se descargaron documentos'],
            'rutas': {}
        }

    print(f"\n✅ PASO 1 COMPLETADO: {len(downloaded_docs)} documentos descargados\n")

    # =========================================================================
    # PROCESAR CADA DOCUMENTO
    # =========================================================================
    for i, doc_info in enumerate(downloaded_docs, 1):
        print("\n" + "=" * 80)
        print(f"PROCESANDO DOCUMENTO {i}/{len(downloaded_docs)}: {doc_info['filename']}")
        print("=" * 80)

        # ---------------------------------------------------------------------
        # PASO 2: METADATA EXTRACTION - Extraer metadatos
        # ---------------------------------------------------------------------
        print(f"\nPASO 2/6: METADATA EXTRACTION - Extrayendo metadatos")
        print("-" * 80)

        title = doc_info.get('title', '')
        filename = doc_info.get('filename', '')

        metadata = metadata_extractor.extract_all_metadata(title, filename)
        document_id = metadata_extractor.get_document_id(metadata)

        print(f"  Tipo de norma:  {metadata['tipo_norma']}")
        print(f"  Número:         {metadata['numero_norma']}")
        print(f"  Fecha:          {metadata['fecha_norma']}")
        print(f"  Document ID:    {document_id}")

        # Verificar si el documento ya fue procesado
        if document_id in existing_ids and not forzar_reprocesar:
            print(f"\n⚠️  DOCUMENTO YA PROCESADO: {document_id}")
            print(f"   Saltando... (usa forzar_reprocesar=True para reprocesar)")
            continue

        if document_id not in existing_ids:
            documentos_nuevos += 1

        # Preparar datos del documento para el CSV
        document_data = {
            'document_id': document_id,
            'tipo_norma': metadata['tipo_norma'],
            'numero_norma': metadata['numero_norma'],
            'fecha_norma': metadata['fecha_norma'],
            'entidad_emisora': metadata['entidad_emisora'],
            'titulo_original': metadata['titulo_original'],
            'url_pdf': doc_info.get('url', ''),
            'filename_pdf': doc_info.get('filename', ''),
            'filepath_pdf': doc_info.get('filepath', ''),
            'size_bytes': doc_info.get('size_bytes', 0),
            'download_date': doc_info.get('download_date', ''),
            'fecha_procesamiento': datetime.now().isoformat(),
            'procesamiento_completo': False,  # Se actualizará al final
            'error_mensaje': None
        }

        # ---------------------------------------------------------------------
        # PASO 3: TEXT EXTRACTION - Extraer texto del PDF
        # ---------------------------------------------------------------------
        print(f"\nPASO 3/6: TEXT EXTRACTION - Extrayendo texto del PDF")
        print("-" * 80)

        pdf_path = doc_info['filepath']
        text_result = text_extractor.extract_text_from_pdf(pdf_path)

        if not text_result or not text_result['exito']:
            error_msg = "Fallo en extracción de texto"
            print(f"\n❌ ERROR: {error_msg}")
            errores.append(f"{document_id}: {error_msg}")

            document_data['error_mensaje'] = error_msg
            document_data['texto_extraido'] = False
            csv_manager.add_or_update_document(document_data)
            continue

        # Actualizar datos del documento con información de texto
        document_data['texto_extraido'] = True
        document_data['metodo_extraccion'] = text_result['metodo_usado']
        document_data['filepath_txt'] = text_result['texto_path']
        document_data['paginas'] = text_result['paginas']
        document_data['caracteres_extraidos'] = text_result['caracteres']

        extracted_text = text_result['texto_extraido']

        # ---------------------------------------------------------------------
        # PASO 4: LEGAL PARSING - Segmentar artículos
        # ---------------------------------------------------------------------
        print(f"\nPASO 4/6: LEGAL PARSING - Segmentando artículos")
        print("-" * 80)

        document_structure = legal_parser.parse_document(extracted_text, document_id)

        articles = document_structure['articles']

        if not articles:
            error_msg = "No se encontraron artículos en el documento"
            print(f"\n⚠️  ADVERTENCIA: {error_msg}")
            errores.append(f"{document_id}: {error_msg}")
            # Continuar de todas formas, guardar el documento

        document_data['total_articulos'] = len(articles)

        # ---------------------------------------------------------------------
        # PASO 5: JSON GENERATION - Guardar estructura JSON
        # ---------------------------------------------------------------------
        print(f"\nPASO 5/6: JSON GENERATION - Guardando estructura JSON")
        print("-" * 80)

        json_path = legal_parser.save_to_json(document_structure, output_dir="data/parsed")

        if json_path:
            document_data['filepath_json'] = json_path
        else:
            error_msg = "Fallo al guardar JSON"
            print(f"\n⚠️  ADVERTENCIA: {error_msg}")
            errores.append(f"{document_id}: {error_msg}")

        # ---------------------------------------------------------------------
        # PASO 6: CSV UPDATE - Actualizar CSVs
        # ---------------------------------------------------------------------
        print(f"\nPASO 6/6: CSV UPDATE - Actualizando CSVs")
        print("-" * 80)

        # Marcar procesamiento como completo
        document_data['procesamiento_completo'] = True

        # Actualizar CSV de documentos
        csv_manager.add_or_update_document(document_data)

        # Agregar artículos al CSV de artículos
        if articles:
            csv_manager.add_articles_from_document(document_id, articles)
            total_articulos += len(articles)

        documentos_procesados += 1

        print(f"\n✅ DOCUMENTO COMPLETADO: {document_id}")
        print(f"   - Artículos extraídos: {len(articles)}")
        print(f"   - JSON guardado: {os.path.basename(json_path) if json_path else 'N/A'}")

    # =========================================================================
    # RESUMEN FINAL
    # =========================================================================
    print("\n\n" + "=" * 80)
    print(" " * 25 + "RESUMEN FINAL DEL PIPELINE")
    print("=" * 80)

    print(f"\n📥 DESCARGA:")
    print(f"   - PDFs descargados: {len(downloaded_docs)}")
    print(f"   - Documentos nuevos: {documentos_nuevos}")

    print(f"\n⚙️  PROCESAMIENTO:")
    print(f"   - Documentos procesados exitosamente: {documentos_procesados}")
    print(f"   - Artículos totales extraídos: {total_articulos}")
    print(f"   - Errores encontrados: {len(errores)}")

    if errores:
        print(f"\n⚠️  ERRORES:")
        for error in errores:
            print(f"   - {error}")

    print(f"\n📁 ARCHIVOS GENERADOS:")
    print(f"   - PDFs:       data/pdfs/")
    print(f"   - Textos:     data/text/")
    print(f"   - JSONs:      data/parsed/")
    print(f"   - CSVs:")
    print(f"     • Documentos: data/csv/documentos.csv")
    print(f"     • Artículos:  data/csv/articulos.csv")

    # Mostrar estadísticas de CSVs
    print(f"\n📊 ESTADÍSTICAS DE CSVs:")
    csv_manager.print_summary()

    print("=" * 80)
    print(" " * 25 + "PIPELINE COMPLETADO")
    print("=" * 80 + "\n")

    return {
        'documentos_descargados': len(downloaded_docs),
        'documentos_nuevos': documentos_nuevos,
        'documentos_procesados': documentos_procesados,
        'total_articulos': total_articulos,
        'errores': errores,
        'rutas': {
            'pdfs': 'data/pdfs/',
            'textos': 'data/text/',
            'jsons': 'data/parsed/',
            'csv_documentos': 'data/csv/documentos.csv',
            'csv_articulos': 'data/csv/articulos.csv'
        }
    }


# =============================================================================
# PUNTO DE ENTRADA PRINCIPAL
# =============================================================================
if __name__ == "__main__":
    """
    BLOQUE PRINCIPAL DE EJECUCIÓN
    =============================

    PARA EJECUTAR EL PIPELINE COMPLETO:
    -----------------------------------
    python main.py

    IMPORTANTE:
    -----------
    Antes de ejecutar, asegúrate de:
    1. Instalar dependencias: pip install -r requirements.txt
    2. Tener Tesseract instalado para OCR (si hay PDFs escaneados):
       - Ubuntu/Debian: sudo apt-get install tesseract-ocr tesseract-ocr-spa
       - macOS: brew install tesseract tesseract-lang
       - Windows: https://github.com/UB-Mannheim/tesseract/wiki

    CONFIGURACIÓN:
    -------------
    - URL_INICIAL: URL de la página de la Gaceta Oficial con listado de normas
    - LIMITE_DOCUMENTOS: Número de documentos a procesar en esta ejecución
    """

    # -------------------------------------------------------------------------
    # CONFIGURACIÓN DEL PIPELINE
    # -------------------------------------------------------------------------

    # URL de ejemplo de la Gaceta Oficial de Bolivia
    # IMPORTANTE: Debes actualizar esta URL con una URL real de listado de normas
    # Ejemplos de URLs válidas:
    # - https://www.gacetaoficialdebolivia.gob.bo/normas/buscar
    # - https://www.gacetaoficialdebolivia.gob.bo/normas/verGaceta/NNN
    URL_INICIAL = "https://www.gacetaoficialdebolivia.gob.bo/normas/buscar"

    # Número de documentos a procesar (empezar con pocos para pruebas)
    LIMITE_DOCUMENTOS = 3

    # -------------------------------------------------------------------------
    # EJECUTAR PIPELINE
    # -------------------------------------------------------------------------

    print("\n" + "🦉" * 40)
    print(" " * 30 + "SISTEMA BÚHO")
    print(" " * 20 + "Pipeline de Procesamiento Legal")
    print("🦉" * 40 + "\n")

    try:
        resultado = run_full_pipeline(
            url_inicial=URL_INICIAL,
            limite_documentos=LIMITE_DOCUMENTOS,
            forzar_reprocesar=False
        )

        # Verificar si hubo éxito
        if resultado['documentos_procesados'] > 0:
            print("\n✅ EJECUCIÓN EXITOSA")
            print(f"\n📋 Para ver los resultados:")
            print(f"   - CSV de documentos: {resultado['rutas']['csv_documentos']}")
            print(f"   - CSV de artículos:  {resultado['rutas']['csv_articulos']}")
            print(f"   - JSONs parseados:   {resultado['rutas']['jsons']}")
        else:
            print("\n⚠️  ADVERTENCIA: No se procesaron documentos")
            if resultado['errores']:
                print(f"\nErrores:")
                for error in resultado['errores']:
                    print(f"  - {error}")

    except KeyboardInterrupt:
        print("\n\n⚠️  Pipeline interrumpido por el usuario")
        sys.exit(1)

    except Exception as e:
        print(f"\n\n❌ ERROR FATAL EN EL PIPELINE:")
        print(f"   {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
