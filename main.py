#!/usr/bin/env python3
"""
BÚHO - Scraper de normativa boliviana
CLI principal para scraping, extracción y exportación a Supabase

FASE 8 - Exportaciones Profesionales para Memoria Legal Dinámica (MLD)

Uso:
    python main.py --help
    python main.py --export-supabase
    python main.py --export-supabase --sitio gaceta
    python main.py --export-documento data/documento.json
"""

import sys
import argparse
import logging
from pathlib import Path
from typing import Optional

# Importar módulos del proyecto
try:
    from exporter import export_supabase_ready, procesar_documento_individual
    from exporter.export_supabase import SupabaseExporter
except ImportError as e:
    print(f"Error importando módulos: {e}")
    print("Asegúrate de que el directorio exporter/ existe y contiene los archivos necesarios.")
    sys.exit(1)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('buho_scraper.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)


def print_banner():
    """Imprime el banner de BÚHO"""
    banner = """
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║   ███████╗ ██╗   ██╗ ██╗  ██╗  ██████╗                      ║
    ║   ██╔══██╗ ██║   ██║ ██║  ██║ ██╔═══██╗                     ║
    ║   ███████║ ██║   ██║ ███████║ ██║   ██║                     ║
    ║   ██╔══██║ ██║   ██║ ██╔══██║ ██║   ██║                     ║
    ║   ██████╔╝ ╚██████╔╝ ██║  ██║ ╚██████╔╝                     ║
    ║   ╚═════╝   ╚═════╝  ╚═╝  ╚═╝  ╚═════╝                      ║
    ║                                                               ║
    ║   Scraper de Normativa Boliviana                             ║
    ║   Memoria Legal Dinámica (MLD) - Sistema de Información      ║
    ║   FASE 8: Exportaciones Profesionales para Supabase          ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def comando_export_supabase(args):
    """
    Ejecuta la exportación de datos a formato Supabase JSONL.

    Args:
        args: Argumentos de línea de comandos
    """
    print_banner()
    logger.info("Iniciando exportación a Supabase...")

    try:
        # Crear exportador
        exporter = SupabaseExporter(
            data_dir=args.data_dir,
            export_dir=args.export_dir
        )

        # Ejecutar exportación
        if args.sitio:
            logger.info(f"Exportando datos del sitio: {args.sitio}")
            resultados = exporter.export_supabase_ready(sitio=args.sitio)
        else:
            logger.info("Exportando todos los datos disponibles")
            resultados = exporter.export_supabase_ready()

        # Mostrar resultados
        print("\n" + "="*70)
        print("✅ EXPORTACIÓN COMPLETADA CON ÉXITO")
        print("="*70)
        print(f"\n📄 Documentos:  {resultados['documents']}")
        print(f"📋 Artículos:   {resultados['articles']}")
        print(f"📊 Estadísticas: {resultados['stats']}")
        print("\n" + "="*70)
        print("\n💡 Próximos pasos:")
        print("   1. Revisa los archivos JSONL generados en exports/")
        print("   2. Importa a Supabase usando el dashboard o SQL")
        print("   3. Consulta FASE8_SUPABASE.md para instrucciones detalladas")
        print("="*70 + "\n")

        return 0

    except Exception as e:
        logger.error(f"Error durante la exportación: {str(e)}", exc_info=True)
        print(f"\n❌ ERROR: {str(e)}\n")
        return 1


def comando_export_documento(args):
    """
    Exporta un documento individual a formato Supabase.

    Args:
        args: Argumentos de línea de comandos
    """
    logger.info(f"Exportando documento: {args.archivo}")

    try:
        # Validar que el archivo existe
        if not Path(args.archivo).exists():
            logger.error(f"Archivo no encontrado: {args.archivo}")
            print(f"\n❌ ERROR: Archivo no encontrado: {args.archivo}\n")
            return 1

        # Procesar documento
        resultados = procesar_documento_individual(
            filepath=args.archivo,
            sitio=args.sitio
        )

        # Mostrar resultados
        print("\n" + "="*70)
        print("✅ DOCUMENTO EXPORTADO CON ÉXITO")
        print("="*70)
        print(f"\n📄 Documentos exportados: {resultados['stats']['documentos']}")
        print(f"📋 Artículos exportados: {resultados['stats']['articulos']}")
        print(f"\nArchivos generados:")
        print(f"  • {resultados['documents']}")
        print(f"  • {resultados['articles']}")
        print("="*70 + "\n")

        return 0

    except Exception as e:
        logger.error(f"Error exportando documento: {str(e)}", exc_info=True)
        print(f"\n❌ ERROR: {str(e)}\n")
        return 1


def comando_scrape(args):
    """
    Ejecuta el scraping de un sitio (placeholder para futuras fases).

    Args:
        args: Argumentos de línea de comandos
    """
    print_banner()
    logger.info(f"Scraping de sitio: {args.sitio}")

    print("\n⚠️  FUNCIÓN EN DESARROLLO")
    print("="*70)
    print("El módulo de scraping se implementará en fases futuras.")
    print("Por ahora, puedes:")
    print("  1. Colocar archivos JSON en data/")
    print("  2. Ejecutar: python main.py --export-supabase")
    print("="*70 + "\n")

    return 0


def comando_info(args):
    """
    Muestra información del proyecto y estadísticas.

    Args:
        args: Argumentos de línea de comandos
    """
    print_banner()

    print("\n📊 INFORMACIÓN DEL PROYECTO")
    print("="*70)

    # Verificar directorios
    data_dir = Path(args.data_dir)
    export_dir = Path(args.export_dir)

    if data_dir.exists():
        archivos_json = list(data_dir.glob("*.json"))
        print(f"\n📁 Directorio de datos: {data_dir}")
        print(f"   Archivos JSON encontrados: {len(archivos_json)}")
    else:
        print(f"\n⚠️  Directorio de datos no existe: {data_dir}")

    if export_dir.exists():
        archivos_jsonl = list(export_dir.glob("*.jsonl"))
        archivos_stats = list(export_dir.glob("*stats*.json"))
        print(f"\n📁 Directorio de exportaciones: {export_dir}")
        print(f"   Archivos JSONL: {len(archivos_jsonl)}")
        print(f"   Archivos de estadísticas: {len(archivos_stats)}")
    else:
        print(f"\n⚠️  Directorio de exportaciones no existe: {export_dir}")

    # Información del schema
    schema_file = Path("schema/supabase_schema.sql")
    if schema_file.exists():
        print(f"\n✅ Schema de Supabase disponible: {schema_file}")
    else:
        print(f"\n⚠️  Schema de Supabase no encontrado")

    print("\n" + "="*70)
    print("\n💡 Comandos disponibles:")
    print("   python main.py --export-supabase         # Exportar todos los datos")
    print("   python main.py --export-supabase --sitio gaceta  # Filtrar por sitio")
    print("   python main.py --export-documento FILE   # Exportar un documento")
    print("   python main.py --info                    # Esta pantalla")
    print("="*70 + "\n")

    return 0


def main():
    """Función principal del CLI"""

    # Parser principal
    parser = argparse.ArgumentParser(
        description='BÚHO - Scraper de normativa boliviana con exportación a Supabase',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:

  # Exportar todos los datos a Supabase
  python main.py --export-supabase

  # Exportar solo datos de un sitio específico
  python main.py --export-supabase --sitio gaceta

  # Exportar un documento individual
  python main.py --export-documento data/documento.json

  # Ver información del proyecto
  python main.py --info

Para más información, consulta FASE8_SUPABASE.md
        """
    )

    # Argumentos globales
    parser.add_argument(
        '--data-dir',
        default='data',
        help='Directorio con archivos JSON de entrada (default: data/)'
    )
    parser.add_argument(
        '--export-dir',
        default='exports',
        help='Directorio de salida para exportaciones (default: exports/)'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Modo verbose (más detalles en logs)'
    )

    # Subcomandos
    subparsers = parser.add_subparsers(dest='comando', help='Comandos disponibles')

    # Comando: export-supabase
    parser_export = subparsers.add_parser(
        'export-supabase',
        help='Exportar datos a formato JSONL para Supabase'
    )
    parser_export.add_argument(
        '--sitio',
        help='Filtrar por sitio específico (ej: gaceta, abi, verbo_juridico)'
    )

    # Comando: export-documento
    parser_export_doc = subparsers.add_parser(
        'export-documento',
        help='Exportar un documento individual'
    )
    parser_export_doc.add_argument(
        'archivo',
        help='Ruta al archivo JSON del documento'
    )
    parser_export_doc.add_argument(
        '--sitio',
        help='Nombre del sitio fuente (opcional)'
    )

    # Comando: scrape (futuro)
    parser_scrape = subparsers.add_parser(
        'scrape',
        help='Ejecutar scraping de un sitio (en desarrollo)'
    )
    parser_scrape.add_argument(
        '--sitio',
        required=True,
        help='Sitio a scrapear (gaceta, abi, verbo_juridico, etc.)'
    )

    # Comando: info
    parser_info = subparsers.add_parser(
        'info',
        help='Mostrar información del proyecto y estadísticas'
    )

    # Soporte para flags legacy (--export-supabase sin subcomando)
    parser.add_argument(
        '--export-supabase',
        action='store_true',
        help='Exportar datos a Supabase (legacy)'
    )
    parser.add_argument(
        '--export-documento',
        help='Exportar un documento individual (legacy)'
    )
    parser.add_argument(
        '--sitio',
        help='Sitio fuente o filtro'
    )
    parser.add_argument(
        '--info',
        action='store_true',
        help='Mostrar información del proyecto'
    )

    # Parse argumentos
    args = parser.parse_args()

    # Configurar nivel de logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Ejecutar comando
    try:
        # Manejo de flags legacy
        if args.export_supabase and not args.comando:
            return comando_export_supabase(args)
        elif args.export_documento and not args.comando:
            args.archivo = args.export_documento
            return comando_export_documento(args)
        elif args.info and not args.comando:
            return comando_info(args)
        elif not args.comando:
            parser.print_help()
            return 0

        # Manejo de subcomandos
        if args.comando == 'export-supabase':
            return comando_export_supabase(args)
        elif args.comando == 'export-documento':
            return comando_export_documento(args)
        elif args.comando == 'scrape':
            return comando_scrape(args)
        elif args.comando == 'info':
            return comando_info(args)
        else:
            parser.print_help()
            return 0

    except KeyboardInterrupt:
        print("\n\n⚠️  Operación cancelada por el usuario.\n")
        return 130
    except Exception as e:
        logger.error(f"Error inesperado: {str(e)}", exc_info=True)
        print(f"\n❌ ERROR INESPERADO: {str(e)}\n")
        return 1


if __name__ == '__main__':
    sys.exit(main())
