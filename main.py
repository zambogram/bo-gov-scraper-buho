#!/usr/bin/env python3
"""
CLI principal para BO-GOV-SCRAPER-BUHO

Comandos:
  - listar: Listar sitios disponibles
  - scrape: Ejecutar scraping de uno o todos los sitios
  - stats: Ver estadísticas globales
  - sync-supabase: Sincronizar datos con Supabase
"""
import argparse
import sys
from pathlib import Path
import json
import logging
from datetime import datetime

from config import list_active_sites, get_site_config
from scraper import run_site_pipeline, run_all_sites_pipeline

# Importación opcional de sync (solo si se necesita)
try:
    from sync import SupabaseSyncExtended
    SYNC_AVAILABLE = True
except ImportError:
    SYNC_AVAILABLE = False
    SupabaseSyncExtended = None

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def cmd_listar(args):
    """Listar todos los sitios disponibles"""
    print("\n🦉 BÚHO - Sitios disponibles\n")
    print("-" * 80)

    sites = list_active_sites()

    if not sites:
        print("No hay sitios activos configurados.")
        return

    for site in sites:
        print(f"\n📍 {site.nombre}")
        print(f"   ID: {site.id}")
        print(f"   Tipo: {site.tipo}")
        print(f"   Categoría: {site.categoria}")
        print(f"   URL: {site.url_base}")
        print(f"   Prioridad: {site.prioridad} | Ola: {site.ola}")
        print(f"   Activo: {'✓' if site.activo else '✗'}")

    print(f"\n{'-' * 80}")
    print(f"Total sitios activos: {len(sites)}")
    print()


def cmd_scrape(args):
    """Ejecutar scraping de un sitio o todos"""

    # Configuración
    site_id = args.site if args.site != 'all' else None
    mode = args.mode
    limit = args.limit
    save_pdf = args.save_pdf
    save_txt = not args.no_txt
    save_json = not args.no_json

    print(f"\n🚀 Iniciando scraping")
    print(f"   Sitio: {site_id or 'TODOS'}")
    print(f"   Modo: {mode}")
    print(f"   Límite: {limit or 'sin límite'}")
    print(f"   Guardar - PDF: {save_pdf}, TXT: {save_txt}, JSON: {save_json}")
    print()

    if site_id:
        # Scraping de un sitio específico
        try:
            result = run_site_pipeline(
                site_id=site_id,
                mode=mode,
                limit=limit,
                save_pdf=save_pdf,
                save_txt=save_txt,
                save_json=save_json
            )

            # Mostrar resultados
            print(f"\n✅ Scraping completado")
            print(f"   Encontrados: {result.total_encontrados}")
            print(f"   Descargados: {result.total_descargados}")
            print(f"   Parseados: {result.total_parseados}")
            print(f"   Errores: {result.total_errores}")
            print(f"   Duración: {result.duracion_segundos:.2f}s")

            if result.total_errores > 0:
                print(f"\n❌ Errores:")
                for error in result.errores[:5]:  # Mostrar solo primeros 5
                    print(f"   - {error['descripcion']}: {error['detalle']}")

        except Exception as e:
            logger.error(f"Error en scraping: {e}", exc_info=True)
            sys.exit(1)

    else:
        # Scraping de todos los sitios
        try:
            results = run_all_sites_pipeline(
                mode=mode,
                limit=limit,
                save_pdf=save_pdf,
                save_txt=save_txt,
                save_json=save_json
            )

            # Mostrar resumen
            print(f"\n✅ Scraping de todos los sitios completado\n")
            print("-" * 80)

            for site_id, result in results.items():
                print(f"\n📊 {site_id}")
                print(f"   Encontrados: {result.total_encontrados}")
                print(f"   Descargados: {result.total_descargados}")
                print(f"   Parseados: {result.total_parseados}")
                print(f"   Errores: {result.total_errores}")

        except Exception as e:
            logger.error(f"Error en scraping: {e}", exc_info=True)
            sys.exit(1)

    print()


def cmd_stats(args):
    """Mostrar estadísticas globales"""
    print("\n📊 Estadísticas globales\n")
    print("-" * 80)

    sites = list_active_sites()
    total_docs = 0
    total_arts = 0

    for site in sites:
        index_file = site.index_file

        if not index_file.exists():
            print(f"\n{site.nombre}: Sin datos")
            continue

        try:
            with open(index_file, 'r', encoding='utf-8') as f:
                index_data = json.load(f)

            num_docs = len(index_data.get('documentos', {}))
            total_docs += num_docs

            # Contar artículos (aproximado)
            num_arts = 0
            for doc_id, doc_data in index_data.get('documentos', {}).items():
                if doc_data.get('ruta_json'):
                    try:
                        with open(doc_data['ruta_json'], 'r', encoding='utf-8') as jf:
                            doc_json = json.load(jf)
                            num_arts += len(doc_json.get('articulos', []))
                    except:
                        pass

            total_arts += num_arts

            print(f"\n{site.nombre}")
            print(f"   Documentos: {num_docs}")
            print(f"   Artículos: {num_arts}")
            print(f"   Última actualización: {index_data.get('last_update', 'N/A')}")

        except Exception as e:
            print(f"\n{site.nombre}: Error leyendo datos - {e}")

    print(f"\n{'-' * 80}")
    print(f"TOTAL - Documentos: {total_docs}, Artículos: {total_arts}")
    print()


def cmd_sync_supabase(args):
    """Sincronizar datos con Supabase"""
    print("\n🔄 Sincronización con Supabase\n")
    print("-" * 80)

    if not SYNC_AVAILABLE:
        print("\n❌ Error: Módulo de sincronización no disponible")
        print("Instalar dependencias: pip install supabase python-dotenv")
        print()
        sys.exit(1)

    try:
        # Inicializar sincronizador
        syncer = SupabaseSyncExtended(
            exports_dir=Path("exports"),
            normalized_dir=Path("data/normalized"),
            log_dir=Path("logs/sync_supabase")
        )

        if args.all:
            # Sincronizar todos los sitios
            print("\n📋 Sincronizando TODOS los sitios...\n")
            stats = syncer.sync_all_sites()

            # Mostrar resumen
            print(f"\n{'='*80}")
            print("RESUMEN DE SINCRONIZACIÓN")
            print(f"{'='*80}")
            print(f"Sitios procesados: {stats['sitios_procesados']}")
            print(f"Sitios exitosos: {stats['sitios_exitosos']}")
            print(f"Sitios con errores: {stats['sitios_con_errores']}")
            print()

        else:
            # Sincronizar sitio específico
            site_id = args.site
            print(f"\n📍 Sincronizando sitio: {site_id}\n")

            stats = syncer.sync_site(site_id, args.session)

            # Mostrar resultados
            print(f"\n{'='*80}")
            print(f"RESULTADOS - {site_id}")
            print(f"{'='*80}")
            print(f"Sources: {stats['sources_insertados']} insertados, {stats['sources_actualizados']} actualizados")
            print(f"Documents: {stats['documents_insertados']} insertados, {stats['documents_actualizados']} actualizados")
            print(f"Articles: {stats['articles_insertados']} insertados")
            print(f"Errores: {len(stats['errores'])}")

            if stats['errores']:
                print(f"\n❌ Errores encontrados:")
                for error in stats['errores'][:5]:  # Mostrar solo primeros 5
                    print(f"   - {error.get('tipo')}: {error.get('mensaje')}")

            print()

        print("\n✅ Sincronización completada")
        print(f"Ver logs en: logs/sync_supabase/")
        print()

    except ImportError:
        print("\n❌ Error: Supabase no está instalado")
        print("Instalar con: pip install supabase")
        print()
        sys.exit(1)
    except ValueError as e:
        print(f"\n❌ Error de configuración: {e}")
        print("\nAsegúrate de tener configuradas las variables de entorno:")
        print("  SUPABASE_URL=tu_url_de_supabase")
        print("  SUPABASE_KEY=tu_clave_de_supabase")
        print("\nPuedes agregarlas en un archivo .env")
        print()
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error en sincronización: {e}", exc_info=True)
        sys.exit(1)


def main():
    """Función principal del CLI"""

    parser = argparse.ArgumentParser(
        description='BÚHO - Scraper legal de sitios del Estado Boliviano',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest='command', help='Comandos disponibles')

    # Comando: listar
    parser_listar = subparsers.add_parser('listar', aliases=['list', 'ls'], help='Listar sitios disponibles')

    # Comando: scrape
    parser_scrape = subparsers.add_parser('scrape', help='Ejecutar scraping')
    parser_scrape.add_argument(
        'site',
        nargs='?',
        default='all',
        help='ID del sitio a scrapear (tcp, tsj, asfi, sin, contraloria) o "all" para todos'
    )
    parser_scrape.add_argument(
        '--mode',
        choices=['full', 'delta'],
        default='delta',
        help='Modo de scraping: full (histórico completo) o delta (solo nuevos)'
    )
    parser_scrape.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Límite de documentos a procesar'
    )
    parser_scrape.add_argument(
        '--save-pdf',
        action='store_true',
        help='Guardar PDFs originales'
    )
    parser_scrape.add_argument(
        '--no-txt',
        action='store_true',
        help='NO guardar texto normalizado'
    )
    parser_scrape.add_argument(
        '--no-json',
        action='store_true',
        help='NO guardar estructura JSON'
    )

    # Comando: stats
    parser_stats = subparsers.add_parser('stats', help='Ver estadísticas globales')

    # Comando: sync-supabase
    parser_sync = subparsers.add_parser('sync-supabase', help='Sincronizar con Supabase')
    parser_sync.add_argument(
        'site',
        nargs='?',
        help='ID del sitio a sincronizar (tcp, tsj, asfi, sin, contraloria)'
    )
    parser_sync.add_argument(
        '--all',
        action='store_true',
        help='Sincronizar todos los sitios disponibles'
    )
    parser_sync.add_argument(
        '--session',
        type=str,
        default=None,
        help='Timestamp de sesión específica a sincronizar (formato: YYYYMMDD_HHMMSS)'
    )

    # Parsear argumentos
    args = parser.parse_args()

    # Ejecutar comando
    if args.command in ['listar', 'list', 'ls']:
        cmd_listar(args)
    elif args.command == 'scrape':
        cmd_scrape(args)
    elif args.command == 'stats':
        cmd_stats(args)
    elif args.command == 'sync-supabase':
        cmd_sync_supabase(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
