#!/usr/bin/env python3
"""
BÚHO - Scraper de Leyes Bolivianas
Sistema completo de scraping, procesamiento y exportación de documentos legales

Uso:
    # Nuevo sistema de scrapers especializados
    python main.py scrape tcp_jurisprudencia --mode full --save-pdf
    python main.py scrape tcp_jurisprudencia --mode test --limit 100

    # Sistema antiguo (compatibilidad)
    python main.py --scrapear --sitios todos
    python main.py --procesar --ocr
    python main.py --exportar --formato csv
    python main.py --stats
"""

import argparse
import sys
import yaml
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict
import pandas as pd

# Agregar el directorio actual al path
sys.path.insert(0, str(Path(__file__).parent))

# Importar módulos del scraper
from scraper.multi_site_scraper import MultiSiteScraper
from scraper.document_processor import DocumentProcessor
from scraper.metadata import MetadataExtractor
from scraper.pdf_splitter import PDFSplitter
from scraper.database import LawDatabase
from exporters import CSVExporter, JSONExporter, ExcelExporter

# Importar scrapers especializados
from scraper.sites.tcp_jurisprudencia_scraper import TCPJurisprudenciaScraper


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

    def ejecutar_scraper_especializado(self, site_id: str, mode: str = "test",
                                      limite: int = None, save_pdf: bool = True,
                                      export_csv: bool = True):
        """
        Ejecuta un scraper especializado de sites_catalog.yaml

        Args:
            site_id: ID del sitio (ej: 'tcp_jurisprudencia')
            mode: Modo de scraping (test, full, incremental)
            limite: Límite de documentos
            save_pdf: Si se deben descargar PDFs
            export_csv: Si se debe exportar a CSV
        """
        print(f"\n🚀 SCRAPER ESPECIALIZADO: {site_id}")
        print("=" * 60)
        print(f"   Modo: {mode}")
        if limite:
            print(f"   Límite: {limite} documentos")
        print(f"   Descargar PDFs: {'Sí' if save_pdf else 'No'}")
        print("-" * 60)

        # Cargar configuración del sitio
        config_path = Path("config/sites_catalog.yaml")
        if not config_path.exists():
            print(f"❌ No se encontró {config_path}")
            return

        with open(config_path, 'r', encoding='utf-8') as f:
            catalog = yaml.safe_load(f)

        if site_id not in catalog.get('sites', {}):
            print(f"❌ Sitio '{site_id}' no encontrado en sites_catalog.yaml")
            print(f"\nSitios disponibles:")
            for sid in catalog.get('sites', {}).keys():
                print(f"   - {sid}")
            return

        config_sitio = catalog['sites'][site_id]

        # Crear scraper según el tipo
        scraper = None

        if site_id == 'tcp_jurisprudencia':
            scraper = TCPJurisprudenciaScraper(config_sitio)
        else:
            print(f"❌ Scraper para '{site_id}' no implementado aún")
            return

        # Ejecutar scraping
        try:
            print(f"\n📡 Iniciando scraping...")

            # Listar documentos
            documentos = scraper.listar_documentos(
                limite=limite,
                modo=mode
            )

            print(f"\n✅ {len(documentos)} documentos encontrados")

            # Descargar PDFs si se solicita
            if save_pdf and documentos:
                print(f"\n📥 Descargando PDFs...")
                documentos = scraper.descargar_pdfs(documentos)

            # Guardar metadatos JSON
            print(f"\n💾 Guardando metadatos...")
            archivo_json = scraper.guardar_metadatos(documentos)
            print(f"   ✅ JSON: {archivo_json}")

            # Exportar a CSV si se solicita
            if export_csv and documentos:
                print(f"\n📊 Exportando a CSV...")
                self._exportar_scraper_a_csv(documentos, site_id, scraper.directorio_salida)

            # Validar cobertura
            print(f"\n🔍 Validando cobertura...")
            validacion = scraper.validar_cobertura()
            self._mostrar_validacion(validacion)

            # Mostrar estadísticas
            print(f"\n📊 ESTADÍSTICAS FINALES")
            print("=" * 60)
            stats = scraper.obtener_estadisticas()
            print(f"Documentos encontrados: {stats['total_documentos_encontrados']}")
            print(f"PDFs descargados: {stats['total_pdfs_descargados']}")
            print(f"Errores: {stats['total_errores']}")

            if stats['total_errores'] > 0:
                print(f"\n⚠️  Errores detectados:")
                for error in stats['errores'][:5]:  # Mostrar primeros 5
                    print(f"   - {error.get('tipo', 'unknown')}: {error.get('error', 'N/A')}")

            print(f"\n📁 Archivos guardados en: {scraper.directorio_salida}")

        except Exception as e:
            print(f"\n❌ Error durante el scraping: {e}")
            import traceback
            traceback.print_exc()

    def _exportar_scraper_a_csv(self, documentos: List[Dict], site_id: str,
                               directorio: Path):
        """Exporta documentos de scraper especializado a CSV"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archivo_csv = directorio / f"documentos_{timestamp}.csv"

        # Convertir a DataFrame
        # Excluir campos muy grandes (json_raw)
        docs_para_csv = []
        for doc in documentos:
            doc_limpio = {k: v for k, v in doc.items() if k != 'json_raw'}
            docs_para_csv.append(doc_limpio)

        df = pd.DataFrame(docs_para_csv)

        # Guardar
        df.to_csv(archivo_csv, index=False, encoding='utf-8-sig')

        print(f"   ✅ CSV: {archivo_csv}")
        print(f"   📊 {len(df)} filas × {len(df.columns)} columnas")

    def _mostrar_validacion(self, validacion: Dict):
        """Muestra resultados de validación de cobertura"""
        print(f"\n📋 VALIDACIÓN DE COBERTURA")
        print("-" * 60)
        print(f"Total documentos encontrados: {validacion['total_documentos_encontrados']}")
        print(f"Total PDFs descargados: {validacion['total_pdfs_descargados']}")
        print(f"Porcentaje éxito descarga: {validacion['porcentaje_exito_descarga']:.1f}%")

        if 'total_esperado' in validacion:
            print(f"Total esperado (API): {validacion['total_esperado']}")
            print(f"Diferencia: {validacion['diferencia']} ({validacion['porcentaje_diferencia']:.1f}%)")

            if validacion.get('cobertura_completa'):
                print(f"✅ Cobertura completa verificada")
            else:
                print(f"⚠️  Cobertura incompleta - revisar paginación")


def main():
    """Función principal con CLI"""
    parser = argparse.ArgumentParser(
        description='🦉 BÚHO - Scraper de Leyes Bolivianas',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  # Scraper especializado TCP Jurisprudencia (NUEVO)
  python main.py scrape tcp_jurisprudencia --mode full --save-pdf
  python main.py scrape tcp_jurisprudencia --mode test --limit 100

  # Sistema antiguo (compatibilidad)
  python main.py --scrapear --sitios todos
  python main.py --stats
        """
    )

    # Subcomandos
    subparsers = parser.add_subparsers(dest='command', help='Comando a ejecutar')

    # =========================================================================
    # COMANDO: scrape (NUEVO)
    # =========================================================================
    scrape_parser = subparsers.add_parser(
        'scrape',
        help='Ejecutar scraper especializado de un sitio',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    scrape_parser.add_argument(
        'site_id',
        help='ID del sitio a scrapear (ej: tcp_jurisprudencia)'
    )

    scrape_parser.add_argument(
        '--mode',
        choices=['test', 'full', 'incremental'],
        default='test',
        help='Modo de scraping (default: test)'
    )

    scrape_parser.add_argument(
        '--limit',
        type=int,
        help='Límite de documentos a obtener'
    )

    scrape_parser.add_argument(
        '--save-pdf',
        action='store_true',
        default=True,
        help='Descargar PDFs (default: True)'
    )

    scrape_parser.add_argument(
        '--no-pdf',
        action='store_true',
        help='NO descargar PDFs'
    )

    scrape_parser.add_argument(
        '--export-csv',
        action='store_true',
        default=True,
        help='Exportar a CSV (default: True)'
    )

    # =========================================================================
    # COMANDOS ANTIGUOS (compatibilidad)
    # =========================================================================
    parser.add_argument('--scrapear', action='store_true',
                       help='Ejecutar scraping de sitios web (sistema antiguo)')
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

    # =========================================================================
    # PROCESAR COMANDO
    # =========================================================================

    # Comando scrape (NUEVO)
    if args.command == 'scrape':
        buho = BuhoScraper()
        try:
            save_pdf = not args.no_pdf
            buho.ejecutar_scraper_especializado(
                site_id=args.site_id,
                mode=args.mode,
                limite=args.limit,
                save_pdf=save_pdf,
                export_csv=args.export_csv
            )
            print("\n✅ Scraping completado exitosamente")
        except KeyboardInterrupt:
            print("\n\n⚠️  Proceso interrumpido por el usuario")
            sys.exit(1)
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
        return

    # Si no se especifica ninguna acción, mostrar ayuda
    if not (args.scrapear or args.procesar or args.exportar or
            args.stats or args.completo or args.command):
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
