#!/usr/bin/env python3
"""
CLI principal para el scraper de sitios gubernamentales bolivianos.

Uso:
    python main.py list [--prioridad 1] [--categoria legislativo]
    python main.py scrape <site_id> [--limit 10] [--solo-nuevos]
    python main.py demo-ola1 [--limit 5]
    python main.py stats
"""

import sys
import argparse
import logging
from pathlib import Path
from typing import Optional

from scraper.catalog import CatalogManager, OLA1_SITE_IDS
from scraper.sites import get_scraper_class


# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('scraper.log')
    ]
)

logger = logging.getLogger(__name__)


def cmd_list(args):
    """Lista sitios del catálogo."""
    catalog = CatalogManager()

    sites = catalog.list_sites(
        prioridad=args.prioridad,
        categoria=args.categoria,
        estado_scraper=args.estado
    )

    if not sites:
        print("No se encontraron sitios con los filtros especificados.")
        return

    print(f"\n{'='*80}")
    print(f"CATÁLOGO DE SITIOS GUBERNAMENTALES")
    print(f"{'='*80}\n")

    for site in sites:
        print(f"ID: {site.site_id}")
        print(f"  Nombre: {site.nombre}")
        print(f"  Categoría: {site.categoria}")
        print(f"  Prioridad: {site.prioridad}")
        print(f"  Estado Scraper: {site.estado_scraper}")
        print(f"  URL: {site.url_base}")
        print(f"  Tipos: {', '.join(site.tipo_documentos[:3])}...")
        print(f"  Notas: {site.notas[:80]}...")
        print()

    print(f"Total: {len(sites)} sitios\n")


def cmd_scrape(args):
    """Ejecuta scraping de un sitio específico."""
    catalog = CatalogManager()

    # Verificar que el sitio existe
    if not catalog.site_exists(args.site_id):
        print(f"Error: El sitio '{args.site_id}' no existe en el catálogo.")
        print(f"Usa 'python main.py list' para ver los sitios disponibles.")
        return 1

    # Obtener configuración del sitio
    site_config = catalog.get_site(args.site_id)

    # Verificar que existe un scraper implementado
    scraper_class = get_scraper_class(args.site_id)
    if not scraper_class:
        print(f"Error: No hay scraper implementado para '{args.site_id}'.")
        print(f"Estado del scraper: {site_config.estado_scraper}")
        return 1

    # Crear instancia del scraper
    modo_demo = args.demo if hasattr(args, 'demo') else False
    scraper = scraper_class(site_config, modo_demo=modo_demo)

    print(f"\n{'='*80}")
    print(f"SCRAPING: {site_config.nombre}")
    print(f"{'='*80}")
    print(f"Site ID: {args.site_id}")
    print(f"URL: {site_config.url_listado}")
    print(f"Modo: {'DEMO' if modo_demo else 'REAL'}")
    print(f"Límite: {args.limit if args.limit else 'Sin límite'}")
    print(f"Solo nuevos: {'Sí' if args.solo_nuevos else 'No'}")
    print(f"{'='*80}\n")

    try:
        # Ejecutar scraping
        documentos = scraper.scrape(limit=args.limit, solo_nuevos=args.solo_nuevos)

        # Generar resumen
        resumen = scraper.generar_resumen(documentos)

        print(f"\n{'='*80}")
        print(f"RESUMEN DE SCRAPING")
        print(f"{'='*80}")
        print(f"Sitio: {resumen['site_id']}")
        print(f"Total encontrados: {resumen['total_encontrados']}")
        print(f"  - Nuevos: {resumen['nuevos']}")
        print(f"  - Modificados: {resumen['modificados']}")
        print(f"  - Sin cambios: {resumen['sin_cambios']}")
        print(f"  - Con PDF: {resumen['con_pdf']}")
        print(f"Fecha: {resumen['fecha_scraping']}")
        print(f"{'='*80}\n")

        # Mostrar algunos ejemplos
        if documentos:
            print("Ejemplos de documentos:")
            for doc in documentos[:3]:
                print(f"  - [{doc.estado.upper()}] {doc.titulo}")
                print(f"    Fecha: {doc.fecha_publicacion} | ID: {doc.document_id}")
            if len(documentos) > 3:
                print(f"  ... y {len(documentos) - 3} más")
            print()

        print(f"Datos guardados en: data/raw/{args.site_id}/")
        print(f"Índice guardado en: data/index/{args.site_id}.json\n")

        return 0

    except Exception as e:
        logger.error(f"Error durante el scraping: {e}", exc_info=True)
        print(f"\nError: {e}")
        return 1


def cmd_demo_ola1(args):
    """Ejecuta scraping demo de todos los sitios de la Ola 1."""
    catalog = CatalogManager()

    print(f"\n{'='*80}")
    print(f"DEMO - OLA 1 (SCRAPERS DE PRIORIDAD MÁXIMA)")
    print(f"{'='*80}\n")

    ola1_ids = catalog.get_ola1_site_ids()
    print(f"Sitios a procesar: {', '.join(ola1_ids)}\n")

    resultados = []

    for site_id in ola1_ids:
        site_config = catalog.get_site(site_id)
        scraper_class = get_scraper_class(site_id)

        if not scraper_class:
            print(f"⚠️  {site_id}: No implementado (saltando)")
            continue

        print(f"▶️  Procesando {site_id}...")

        try:
            scraper = scraper_class(site_config, modo_demo=True)
            documentos = scraper.scrape(limit=args.limit, solo_nuevos=False)
            resumen = scraper.generar_resumen(documentos)

            resultados.append({
                'site_id': site_id,
                'nombre': site_config.nombre,
                'total': resumen['total_encontrados'],
                'nuevos': resumen['nuevos'],
                'status': 'OK'
            })

            print(f"   ✅ {resumen['total_encontrados']} documentos | "
                  f"{resumen['nuevos']} nuevos | "
                  f"{resumen['con_pdf']} con PDF")

        except Exception as e:
            logger.error(f"Error en {site_id}: {e}")
            resultados.append({
                'site_id': site_id,
                'nombre': site_config.nombre,
                'status': 'ERROR',
                'error': str(e)
            })
            print(f"   ❌ Error: {e}")

        print()

    # Resumen final
    print(f"\n{'='*80}")
    print(f"RESUMEN FINAL - OLA 1")
    print(f"{'='*80}\n")

    total_docs = sum(r.get('total', 0) for r in resultados if r['status'] == 'OK')
    total_nuevos = sum(r.get('nuevos', 0) for r in resultados if r['status'] == 'OK')
    exitosos = sum(1 for r in resultados if r['status'] == 'OK')
    errores = sum(1 for r in resultados if r['status'] == 'ERROR')

    print(f"Sitios procesados: {exitosos}/{len(ola1_ids)}")
    print(f"Total documentos: {total_docs}")
    print(f"Nuevos: {total_nuevos}")
    if errores > 0:
        print(f"Errores: {errores}")

    print(f"\n{'='*80}\n")


def cmd_stats(args):
    """Muestra estadísticas de los scrapers."""
    catalog = CatalogManager()
    data_dir = Path("data/index")

    print(f"\n{'='*80}")
    print(f"ESTADÍSTICAS DE SCRAPERS")
    print(f"{'='*80}\n")

    if not data_dir.exists():
        print("No hay datos de scraping todavía.")
        return

    for index_file in data_dir.glob("*.json"):
        site_id = index_file.stem
        site_config = catalog.get_site(site_id)

        if not site_config:
            continue

        from scraper.base import DocumentIndex
        index = DocumentIndex(site_id)
        stats = index.get_stats()

        print(f"{site_config.nombre} ({site_id})")
        print(f"  Total documentos: {stats['total_documentos']}")
        print(f"  Última actualización: {stats['ultima_actualizacion']}")
        print()

    print(f"{'='*80}\n")


def main():
    """Función principal del CLI."""
    parser = argparse.ArgumentParser(
        description='Scraper de sitios gubernamentales de Bolivia',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest='command', help='Comandos disponibles')

    # Comando: list
    parser_list = subparsers.add_parser('list', help='Listar sitios del catálogo')
    parser_list.add_argument('--prioridad', type=int, help='Filtrar por prioridad (1, 2, ...)')
    parser_list.add_argument('--categoria', help='Filtrar por categoría (legislativo, judicial, ...)')
    parser_list.add_argument('--estado', help='Filtrar por estado (implementado, pendiente)')

    # Comando: scrape
    parser_scrape = subparsers.add_parser('scrape', help='Ejecutar scraping de un sitio')
    parser_scrape.add_argument('site_id', help='ID del sitio a scrapear')
    parser_scrape.add_argument('--limit', type=int, help='Límite de documentos a scrapear')
    parser_scrape.add_argument('--solo-nuevos', action='store_true', default=True,
                               help='Solo procesar documentos nuevos o modificados (default: True)')
    parser_scrape.add_argument('--demo', action='store_true',
                               help='Modo demo (genera datos de prueba)')

    # Comando: demo-ola1
    parser_demo = subparsers.add_parser('demo-ola1', help='Demo de todos los sitios Ola 1')
    parser_demo.add_argument('--limit', type=int, default=5,
                            help='Límite de documentos por sitio (default: 5)')

    # Comando: stats
    parser_stats = subparsers.add_parser('stats', help='Mostrar estadísticas')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    # Ejecutar comando
    if args.command == 'list':
        return cmd_list(args)
    elif args.command == 'scrape':
        return cmd_scrape(args)
    elif args.command == 'demo-ola1':
        return cmd_demo_ola1(args)
    elif args.command == 'stats':
        return cmd_stats(args)
    else:
        parser.print_help()
        return 0


if __name__ == '__main__':
    sys.exit(main())
