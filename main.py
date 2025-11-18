#!/usr/bin/env python3
"""
CLI principal para BO-GOV-SCRAPER-BUHO

Comandos:
  - listar: Listar sitios disponibles
  - scrape: Ejecutar scraping de uno o todos los sitios
  - stats: Ver estadísticas globales
"""
import argparse
import sys
from pathlib import Path
import json
import logging
from datetime import datetime

from config import list_active_sites, get_site_config
from scraper import run_site_pipeline, run_all_sites_pipeline

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

    # Parsear argumentos
    args = parser.parse_args()

    # Ejecutar comando
    if args.command in ['listar', 'list', 'ls']:
        cmd_listar(args)
    elif args.command == 'scrape':
        cmd_scrape(args)
    elif args.command == 'stats':
        cmd_stats(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
