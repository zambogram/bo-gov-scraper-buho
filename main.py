"""
BÚHO - Scraper de Gaceta Oficial de Bolivia
Punto de entrada principal del sistema

Fase 3: Extracción de Metadatos Legales
"""

import sys
from pathlib import Path

# Agregar el directorio raíz al path para imports
sys.path.insert(0, str(Path(__file__).parent))

from scraper.gaceta_scraper import crear_datos_ejemplo, GacetaScraper


def main():
    """
    Función principal del scraper.

    Ejecuta el scraper con un límite pequeño de documentos
    y muestra un resumen de metadatos extraídos.
    """
    print("="*80)
    print("🦉 BÚHO - Sistema de Scraping de Gaceta Oficial de Bolivia")
    print("   FASE 3: Extracción y Normalización de Metadatos")
    print("="*80)
    print()

    # Configuración
    NUM_DOCUMENTOS_PRUEBA = 8  # Límite pequeño para pruebas
    OUTPUT_DIR = "data"
    EXPORT_DIR = "exports"

    print(f"⚙️  Configuración:")
    print(f"   - Documentos a procesar: {NUM_DOCUMENTOS_PRUEBA}")
    print(f"   - Directorio de PDFs: {OUTPUT_DIR}/")
    print(f"   - Directorio de exports: {EXPORT_DIR}/")
    print()

    # Ejecutar scraper con datos de ejemplo
    # En producción, esto se reemplazaría con el scraping real
    print("🚀 Iniciando scraper...\n")

    scraper = crear_datos_ejemplo(
        output_dir=OUTPUT_DIR,
        export_dir=EXPORT_DIR,
        num_docs=NUM_DOCUMENTOS_PRUEBA
    )

    # Mostrar resumen de metadatos
    print("\n" + "="*80)
    print("📊 RESUMEN DE METADATOS EXTRAÍDOS")
    print("="*80)

    resumen = scraper.obtener_resumen(limit=5)

    if resumen:
        for i, doc in enumerate(resumen, 1):
            print(f"\n{i}. DOCUMENTO:")
            print(f"   📝 Título: {doc['titulo'][:70]}...")
            print(f"   🏷️  Tipo de norma: {doc['tipo_norma']}")
            print(f"   🔢 Número: {doc['numero_norma'] or 'No detectado'}")
            print(f"   📅 Fecha: {doc['fecha_publicacion_aproximada'] or 'No detectada'}")
            print(f"   📄 Archivo: {doc['archivo_descargado']}")
            print(f"   ✅ Estado: {doc['estado']}")
    else:
        print("\n⚠️  No se procesaron documentos")

    # Información del CSV
    print("\n" + "="*80)
    print("📁 ARCHIVOS GENERADOS")
    print("="*80)

    csv_path = Path(EXPORT_DIR) / "gaceta_log.csv"
    if csv_path.exists():
        print(f"\n✅ CSV de log generado:")
        print(f"   📍 Ruta: {csv_path.absolute()}")
        print(f"   📊 Registros: {len(scraper.documentos)}")
        print(f"\n   Columnas del CSV:")
        print(f"   - titulo")
        print(f"   - url_pdf")
        print(f"   - archivo_descargado")
        print(f"   - fecha_extraccion")
        print(f"   - estado")
        print(f"   - tipo_norma           [NUEVA - Fase 3]")
        print(f"   - numero_norma         [NUEVA - Fase 3]")
        print(f"   - fecha_publicacion_aproximada [NUEVA - Fase 3]")
    else:
        print("\n⚠️  No se generó el archivo CSV")

    # Estadísticas de metadatos
    print("\n" + "="*80)
    print("📈 ESTADÍSTICAS DE EXTRACCIÓN")
    print("="*80)

    if scraper.documentos:
        # Contar tipos de norma
        tipos_norma = {}
        metadatos_completos = 0
        metadatos_parciales = 0

        for doc in scraper.documentos:
            # Contar tipo
            tipo = doc.get('tipo_norma', 'Desconocido')
            tipos_norma[tipo] = tipos_norma.get(tipo, 0) + 1

            # Contar completitud de metadatos
            tiene_numero = bool(doc.get('numero_norma'))
            tiene_fecha = bool(doc.get('fecha_publicacion_aproximada'))

            if tiene_numero and tiene_fecha:
                metadatos_completos += 1
            elif tiene_numero or tiene_fecha:
                metadatos_parciales += 1

        print(f"\n📊 Tipos de norma detectados:")
        for tipo, cantidad in sorted(tipos_norma.items(), key=lambda x: x[1], reverse=True):
            porcentaje = (cantidad / len(scraper.documentos)) * 100
            print(f"   - {tipo}: {cantidad} ({porcentaje:.1f}%)")

        print(f"\n🎯 Completitud de metadatos:")
        print(f"   - Metadatos completos (tipo + número + fecha): {metadatos_completos}")
        print(f"   - Metadatos parciales (tipo + número o fecha): {metadatos_parciales}")
        print(f"   - Solo tipo detectado: {len(scraper.documentos) - metadatos_completos - metadatos_parciales}")

    print("\n" + "="*80)
    print("✅ Proceso completado exitosamente")
    print("="*80)
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Proceso interrumpido por el usuario")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
