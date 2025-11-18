"""
Pipeline completo de scraping de la Gaceta Oficial de Bolivia
"""
import os
import sys
from datetime import datetime
import pandas as pd

# Agregar el directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scraper import scrape_metadata, download_pdfs, parse_pdfs


def run_full_pipeline(
    url: str = "https://www.gacetaoficialdebolivia.gob.bo/normas/buscar",
    max_docs: int = 3,
    forzar_reprocesar: bool = False,
    output_dir: str = "data"
):
    """
    Ejecuta el pipeline completo de scraping

    Args:
        url: URL de búsqueda de la Gaceta Oficial
        max_docs: Número máximo de documentos a procesar
        forzar_reprocesar: Forzar re-procesamiento de documentos ya descargados
        output_dir: Directorio base para salidas

    Returns:
        Tuple (documentos_df, articulos_df)
    """
    print("=" * 80)
    print("PIPELINE COMPLETO - GACETA OFICIAL DE BOLIVIA")
    print("=" * 80)
    print(f"\nParámetros:")
    print(f"  • URL: {url}")
    print(f"  • Límite de documentos: {max_docs}")
    print(f"  • Forzar reprocesar: {forzar_reprocesar}")
    print(f"  • Directorio de salida: {output_dir}")
    print()

    # Crear directorios
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(f"{output_dir}/pdfs", exist_ok=True)
    os.makedirs(f"{output_dir}/parsed", exist_ok=True)

    # Rutas de salida
    documentos_csv = os.path.join(output_dir, "documentos.csv")
    articulos_csv = os.path.join(output_dir, "articulos.csv")

    # PASO 1: Scraping de metadatos
    print("\n" + "=" * 80)
    print("PASO 1/3: SCRAPING DE METADATOS")
    print("=" * 80)

    documentos_df = scrape_metadata(url=url, max_docs=max_docs)

    if documentos_df.empty:
        print("✗ No se obtuvieron documentos. Abortando pipeline.")
        return None, None

    print(f"\n✓ Metadatos obtenidos: {len(documentos_df)} documentos")
    print("\nPrimeros documentos:")
    print(documentos_df[['id_documento', 'titulo', 'tipo_norma', 'fecha_publicacion']].head())

    # PASO 2: Descarga de PDFs
    print("\n" + "=" * 80)
    print("PASO 2/3: DESCARGA DE PDFs")
    print("=" * 80)

    documentos_df = download_pdfs(
        documentos=documentos_df,
        output_dir=f"{output_dir}/pdfs",
        force_redownload=forzar_reprocesar
    )

    # Filtrar solo los documentos descargados exitosamente
    docs_descargados = documentos_df[
        documentos_df['download_status'].isin(['ok', 'cached', 'ejemplo'])
    ]

    if docs_descargados.empty:
        print("✗ No se descargaron PDFs. Abortando pipeline.")
        return documentos_df, None

    print(f"\n✓ PDFs disponibles: {len(docs_descargados)}")

    # PASO 3: Parsing de documentos
    print("\n" + "=" * 80)
    print("PASO 3/3: PARSING DE DOCUMENTOS")
    print("=" * 80)

    documentos_df, articulos_df = parse_pdfs(
        documentos=docs_descargados,
        output_dir=f"{output_dir}/parsed"
    )

    # PASO 4: Guardar resultados
    print("\n" + "=" * 80)
    print("GUARDANDO RESULTADOS")
    print("=" * 80)

    # Guardar documentos
    documentos_df.to_csv(documentos_csv, index=False, encoding='utf-8-sig')
    print(f"\n✓ Documentos guardados en: {documentos_csv}")
    print(f"  Total: {len(documentos_df)} documentos")

    # Guardar artículos
    if not articulos_df.empty:
        articulos_df.to_csv(articulos_csv, index=False, encoding='utf-8-sig')
        print(f"\n✓ Artículos guardados en: {articulos_csv}")
        print(f"  Total: {len(articulos_df)} artículos")
    else:
        print("\n⚠ No se extrajeron artículos")

    # Resumen final
    print("\n" + "=" * 80)
    print("RESUMEN FINAL")
    print("=" * 80)
    print(f"\n📊 Estadísticas:")
    print(f"  • Documentos procesados: {len(documentos_df)}")
    print(f"  • Artículos extraídos: {len(articulos_df) if not articulos_df.empty else 0}")
    print(f"  • Archivos en data/parsed: {len(os.listdir(f'{output_dir}/parsed'))}")

    print(f"\n📁 Archivos generados:")
    print(f"  • {documentos_csv}")
    print(f"  • {articulos_csv}")
    print(f"  • {output_dir}/parsed/ ({len(os.listdir(f'{output_dir}/parsed'))} archivos)")

    print("\n✅ Pipeline completado exitosamente!")
    print("=" * 80)

    return documentos_df, articulos_df


def main():
    """Función principal"""
    # Configuración por defecto
    URL = "https://www.gacetaoficialdebolivia.gob.bo/normas/buscar"
    MAX_DOCS = 3
    FORZAR_REPROCESAR = False

    # Ejecutar pipeline
    documentos, articulos = run_full_pipeline(
        url=URL,
        max_docs=MAX_DOCS,
        forzar_reprocesar=FORZAR_REPROCESAR
    )

    if documentos is not None:
        print("\n✓ Ejecución completada")
        return 0
    else:
        print("\n✗ Ejecución falló")
        return 1


if __name__ == "__main__":
    sys.exit(main())
