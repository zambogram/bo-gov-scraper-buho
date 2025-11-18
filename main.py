"""
BO GOV SCRAPER - BUHO
Scraper de documentos legales del Estado Plurinacional de Bolivia

Este es el archivo principal que coordina todas las fases del proyecto.
"""

import os
import sys
from pathlib import Path

# Agregar el directorio actual al path para importar módulos locales
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scraper.legal_parser import (
    load_metadata,
    load_text,
    segment_articles,
    build_document_structure,
    save_document_json,
    append_articles_to_csv,
    process_document
)


def test_fase5():
    """
    Modo de prueba para FASE 5: Parser Legal por Artículos

    Este modo procesa 1-2 documentos de ejemplo y muestra:
    - Cuántos artículos se detectaron
    - Un ejemplo de artículo (número + primeros 200 caracteres)
    - La ruta del JSON generado
    - La ruta del CSV de artículos
    """
    print("=" * 80)
    print("FASE 5: PARSER LEGAL POR ARTÍCULOS - MODO DE PRUEBA")
    print("=" * 80)
    print()

    # Configuración de rutas
    csv_metadatos = "data/csv/metadatos.csv"
    text_dir = "data/text"
    output_json_dir = "data/parsed"
    csv_articulos_path = "data/csv/articulos.csv"

    # Verificar que existan los archivos necesarios
    if not os.path.exists(csv_metadatos):
        print(f"❌ ERROR: No se encontró el archivo de metadatos: {csv_metadatos}")
        print("   Por favor, asegúrate de que exista el CSV con los metadatos de los documentos.")
        return

    if not os.path.exists(text_dir):
        print(f"❌ ERROR: No se encontró el directorio de textos: {text_dir}")
        return

    # Cargar metadatos
    print("📋 Cargando metadatos...")
    try:
        df_metadata = load_metadata(csv_metadatos)
        print(f"   ✓ {len(df_metadata)} documentos encontrados en metadatos\n")
    except Exception as e:
        print(f"   ❌ Error al cargar metadatos: {str(e)}")
        return

    # Filtrar solo documentos con texto extraído
    docs_con_texto = df_metadata[df_metadata['texto_extraido'] == 'sí']

    if len(docs_con_texto) == 0:
        print("⚠️  No hay documentos con texto extraído para procesar.")
        return

    print(f"📝 Documentos con texto extraído: {len(docs_con_texto)}")
    print()

    # Procesar los primeros 2 documentos (o todos si hay menos de 2)
    max_docs = min(2, len(docs_con_texto))
    docs_procesados = 0
    docs_fallidos = 0

    for idx, (_, row) in enumerate(docs_con_texto.head(max_docs).iterrows(), 1):
        id_doc = row['id_documento']
        text_path = os.path.join(text_dir, f"{id_doc}.txt")

        print(f"{'=' * 80}")
        print(f"DOCUMENTO {idx}/{max_docs}: {id_doc}")
        print(f"{'=' * 80}")
        print(f"Tipo: {row['tipo_norma']}")
        print(f"Número: {row['numero_norma']}")
        print(f"Fecha: {row['fecha_publicacion_aproximada']}")
        print(f"Título: {row['titulo']}")
        print()

        # Verificar que existe el archivo de texto
        if not os.path.exists(text_path):
            print(f"⚠️  Advertencia: No se encontró el archivo {text_path}")
            print(f"   Saltando este documento...\n")
            docs_fallidos += 1
            continue

        # Procesar el documento
        try:
            doc_structure = process_document(
                text_path=text_path,
                metadata_row=row,
                output_json_dir=output_json_dir,
                csv_articulos_path=csv_articulos_path
            )

            if doc_structure:
                stats = doc_structure['statistics']
                articles = doc_structure['articles']

                print(f"✅ Procesamiento exitoso!")
                print(f"   📊 Total de artículos detectados: {stats['total_articles']}")
                print(f"   📝 Artículos con título: {stats['articles_with_title']}")
                print(f"   📄 Total de caracteres: {stats['total_characters']:,}")
                print()

                # Mostrar un ejemplo de artículo
                if len(articles) > 0:
                    ejemplo = articles[0]
                    print(f"   📖 Ejemplo - Artículo {ejemplo['articulo_numero']}:")
                    if ejemplo['titulo_articulo']:
                        print(f"      Título: {ejemplo['titulo_articulo']}")
                    texto_preview = ejemplo['texto'][:200].replace('\n', ' ')
                    print(f"      Texto: {texto_preview}...")
                    print()

                # Rutas de archivos generados
                json_path = os.path.join(output_json_dir, f"{id_doc}.json")
                print(f"   💾 JSON generado: {json_path}")
                print(f"   💾 CSV de artículos: {csv_articulos_path}")
                print()

                docs_procesados += 1
            else:
                print(f"❌ Error al procesar el documento\n")
                docs_fallidos += 1

        except Exception as e:
            print(f"❌ Error al procesar el documento: {str(e)}\n")
            docs_fallidos += 1

    # Resumen final
    print("=" * 80)
    print("RESUMEN DE PROCESAMIENTO")
    print("=" * 80)
    print(f"✅ Documentos procesados exitosamente: {docs_procesados}")
    print(f"❌ Documentos con errores: {docs_fallidos}")
    print(f"📂 Directorio de JSONs: {output_json_dir}")
    print(f"📊 CSV de artículos: {csv_articulos_path}")
    print()

    # Mostrar estadísticas del CSV de artículos
    if os.path.exists(csv_articulos_path):
        import pandas as pd
        df_articulos = pd.read_csv(csv_articulos_path)
        print(f"📈 Total de artículos en el CSV: {len(df_articulos)}")
        print(f"📋 Columnas del CSV: {', '.join(df_articulos.columns)}")

    print()
    print("=" * 80)
    print("PRUEBA COMPLETADA")
    print("=" * 80)


def main():
    """
    Función principal del programa.
    """
    print()
    print("╔════════════════════════════════════════════════════════════════════════════╗")
    print("║                    BO GOV SCRAPER - BUHO                                   ║")
    print("║          Scraper de documentos legales de Bolivia                          ║")
    print("╚════════════════════════════════════════════════════════════════════════════╝")
    print()

    # Por ahora, ejecutar el modo de prueba de FASE 5
    test_fase5()


if __name__ == "__main__":
    main()
