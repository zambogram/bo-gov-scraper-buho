#!/usr/bin/env python3
"""
BÚHO - Scraper de Leyes Bolivianas
Sistema completo de scraping, procesamiento y exportación de documentos legales

Uso:
    python main.py --scrapear --sitios todos
    python main.py --procesar --ocr
    python main.py --exportar --formato csv
    python main.py --stats
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict

# Agregar el directorio actual al path
sys.path.insert(0, str(Path(__file__).parent))

# Importar módulos del scraper
from scraper.multi_site_scraper import MultiSiteScraper
from scraper.document_processor import DocumentProcessor
from scraper.metadata import MetadataExtractor
from scraper.pdf_splitter import PDFSplitter
from scraper.database import LawDatabase
from exporters import CSVExporter, JSONExporter, ExcelExporter


class BuhoScraper:
    """Clase principal que orquesta todo el sistema de scraping"""

    def __init__(self):
        """Inicializa el sistema BÚHO"""
        print("🦉 BÚHO - Sistema de Scraping de Leyes Bolivianas")
        print("=" * 60)

        self.scraper = MultiSiteScraper()
        self.processor = DocumentProcessor()
        self.metadata_extractor = MetadataExtractor()
        self.pdf_splitter = PDFSplitter()
        self.db = LawDatabase()

        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    def ejecutar_scraping_completo(self, max_workers: int = 5):
        """
        Ejecuta el proceso completo de scraping

        Args:
            max_workers: Número de hilos concurrentes
        """
        print("\n🚀 FASE 1: SCRAPING DE SITIOS WEB")
        print("-" * 60)

        # Registrar inicio de scraping
        scraping_id = self.db.registrar_scraping(
            "Scraping completo",
            datetime.now()
        )

        # Scrapear todos los sitios
        resultados = self.scraper.scrapear_todos_los_sitios(max_workers=max_workers)

        print(f"\n✅ Scraping completado:")
        print(f"   - Sitios exitosos: {len(resultados['exitosos'])}")
        print(f"   - Total documentos: {resultados['total_documentos']}")

        # Actualizar registro de scraping
        self.db.actualizar_scraping(
            scraping_id,
            fecha_fin=datetime.now().isoformat(),
            leyes_encontradas=resultados['total_documentos'],
            estado='completado'
        )

        return resultados

    def procesar_documentos(self, directorio: str = "data/raw",
                          aplicar_ocr: bool = True,
                          dividir_pdfs: bool = True):
        """
        Procesa todos los documentos descargados

        Args:
            directorio: Directorio con documentos crudos
            aplicar_ocr: Si se debe aplicar OCR
            dividir_pdfs: Si se deben dividir los PDFs grandes
        """
        print("\n📄 FASE 2: PROCESAMIENTO DE DOCUMENTOS")
        print("-" * 60)

        directorio_path = Path(directorio)
        archivos = list(directorio_path.rglob("*.pdf"))
        archivos.extend(list(directorio_path.rglob("*.doc*")))

        print(f"📁 {len(archivos)} archivos encontrados para procesar")

        documentos_procesados = 0
        documentos_con_error = 0

        for archivo in archivos:
            print(f"\n   Procesando: {archivo.name}")

            try:
                # 1. Extraer texto del documento
                resultado_procesamiento = self.processor.procesar_documento(str(archivo))

                if not resultado_procesamiento['exito']:
                    print(f"   ❌ Error procesando: {resultado_procesamiento.get('error')}")
                    documentos_con_error += 1
                    continue

                texto = resultado_procesamiento['texto']
                print(f"   ✅ Texto extraído: {len(texto)} caracteres")

                # 2. Extraer metadatos
                sitio_web = archivo.parent.name
                metadatos = self.metadata_extractor.extraer_metadatos(
                    texto,
                    archivo_path=str(archivo),
                    sitio_web=sitio_web,
                    url_origen=""
                )

                # Agregar información de procesamiento
                metadatos.update({
                    'numero_paginas': resultado_procesamiento.get('numero_paginas', 0),
                    'ocr_aplicado': resultado_procesamiento.get('ocr_aplicado', False),
                    'confianza_ocr': resultado_procesamiento.get('confianza_ocr', 0.0),
                    'texto_extraido': texto,
                    'estado_procesamiento': 'completado'
                })

                print(f"   📋 Metadatos extraídos:")
                print(f"      - Ley: {metadatos.get('numero_ley')}")
                print(f"      - Área: {metadatos.get('area_derecho')}")
                print(f"      - Tipo: {metadatos.get('tipo_norma')}")

                # 3. Guardar en base de datos
                ley_id = self.db.insertar_ley(metadatos)

                if ley_id:
                    print(f"   💾 Guardado en BD con ID: {ley_id}")
                    documentos_procesados += 1

                # 4. Dividir PDFs grandes si es necesario
                if dividir_pdfs and resultado_procesamiento.get('numero_paginas', 0) > 50:
                    print(f"   ✂️  Dividiendo PDF ({resultado_procesamiento['numero_paginas']} páginas)...")
                    archivos_divididos = self.pdf_splitter.dividir_pdf(
                        str(archivo),
                        max_paginas_por_seccion=30
                    )

                    # Agregar metadatos a cada sección
                    for archivo_dividido in archivos_divididos:
                        self.metadata_extractor.agregar_metadatos_a_pdf(
                            archivo_dividido,
                            metadatos
                        )

                    # Actualizar en BD con archivos divididos
                    self.db.actualizar_ley(
                        metadatos['codigo_unico'],
                        {'archivos_divididos': archivos_divididos}
                    )

            except Exception as e:
                print(f"   ❌ Error: {e}")
                documentos_con_error += 1

        print(f"\n📊 Resumen del procesamiento:")
        print(f"   ✅ Procesados exitosamente: {documentos_procesados}")
        print(f"   ❌ Con errores: {documentos_con_error}")

    def exportar_datos(self, formatos: List[str] = None):
        """
        Exporta los datos a diferentes formatos

        Args:
            formatos: Lista de formatos ('csv', 'json', 'excel')
        """
        if formatos is None:
            formatos = ['csv', 'json', 'excel']

        print("\n📤 FASE 3: EXPORTACIÓN DE DATOS")
        print("-" * 60)

        # Obtener todas las leyes de la BD
        leyes = self.db.buscar_ley()

        if not leyes:
            print("⚠️  No hay datos para exportar")
            return

        print(f"📋 {len(leyes)} leyes encontradas en la base de datos")

        # Crear directorio de exportación
        export_dir = Path("exports") / self.timestamp
        export_dir.mkdir(parents=True, exist_ok=True)

        # Exportar a cada formato
        for formato in formatos:
            archivo_salida = export_dir / f"leyes_bolivianas_{self.timestamp}.{formato}"

            if formato == 'csv':
                CSVExporter.exportar(leyes, str(archivo_salida))
            elif formato == 'json':
                JSONExporter.exportar(leyes, str(archivo_salida))
            elif formato == 'excel':
                archivo_salida = export_dir / f"leyes_bolivianas_{self.timestamp}.xlsx"
                ExcelExporter.exportar(leyes, str(archivo_salida))

    def mostrar_estadisticas(self):
        """Muestra estadísticas completas del sistema"""
        print("\n📊 ESTADÍSTICAS DEL SISTEMA")
        print("=" * 60)

        stats = self.db.obtener_estadisticas()

        print(f"\n📚 TOTAL DE LEYES: {stats['total_leyes']}")

        print(f"\n📊 Por Área del Derecho:")
        for area in stats['por_area'][:10]:
            print(f"   - {area['area_derecho']}: {area['cantidad']}")

        print(f"\n📋 Por Tipo de Norma:")
        for tipo in stats['por_tipo']:
            print(f"   - {tipo['tipo_norma']}: {tipo['cantidad']}")

        print(f"\n📅 Por Año (últimos 10):")
        for anio in stats['por_anio'][:10]:
            if anio['anio']:
                print(f"   - {anio['anio']}: {anio['cantidad']}")

        print(f"\n🌐 Por Sitio Web:")
        for sitio in stats['por_sitio']:
            print(f"   - {sitio['sitio_web']}: {sitio['cantidad']}")

        print(f"\n✅ Leyes Vigentes:")
        for vigencia in stats['vigencia']:
            estado = "Vigente" if vigencia['vigente'] else "No vigente"
            print(f"   - {estado}: {vigencia['cantidad']}")


def main():
    """Función principal con CLI"""
    parser = argparse.ArgumentParser(
        description='🦉 BÚHO - Scraper de Leyes Bolivianas',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('--scrapear', action='store_true',
                       help='Ejecutar scraping de sitios web')
    parser.add_argument('--procesar', action='store_true',
                       help='Procesar documentos descargados')
    parser.add_argument('--exportar', action='store_true',
                       help='Exportar datos a archivos')
    parser.add_argument('--stats', action='store_true',
                       help='Mostrar estadísticas')
    parser.add_argument('--completo', action='store_true',
                       help='Ejecutar flujo completo (scrapear + procesar + exportar)')

    parser.add_argument('--workers', type=int, default=5,
                       help='Número de hilos para scraping (default: 5)')
    parser.add_argument('--ocr', action='store_true',
                       help='Aplicar OCR a documentos escaneados')
    parser.add_argument('--dividir-pdfs', action='store_true',
                       help='Dividir PDFs grandes en secciones')
    parser.add_argument('--formato', nargs='+', choices=['csv', 'json', 'excel'],
                       default=['csv', 'json', 'excel'],
                       help='Formatos de exportación')

    args = parser.parse_args()

    # Si no se especifica ninguna acción, mostrar ayuda
    if not (args.scrapear or args.procesar or args.exportar or
            args.stats or args.completo):
        parser.print_help()
        sys.exit(0)

    # Inicializar sistema
    buho = BuhoScraper()

    try:
        if args.completo or args.scrapear:
            buho.ejecutar_scraping_completo(max_workers=args.workers)

        if args.completo or args.procesar:
            buho.procesar_documentos(
                aplicar_ocr=args.ocr,
                dividir_pdfs=args.dividir_pdfs
            )

        if args.completo or args.exportar:
            buho.exportar_datos(formatos=args.formato)

        if args.stats:
            buho.mostrar_estadisticas()

        print("\n✅ Proceso completado exitosamente")
        print("🦉 Gracias por usar BÚHO")

    except KeyboardInterrupt:
        print("\n\n⚠️  Proceso interrumpido por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        buho.db.cerrar()


if __name__ == "__main__":
    main()
