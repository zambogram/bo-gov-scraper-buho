#!/usr/bin/env python3
"""
BÚHO - Scraper de Documentos Gubernamentales de Bolivia
FASE 9 - Sites Reales + Parsers Avanzados + Delta-Update

CLI principal para ejecutar scrapers de sitios gubernamentales
"""
import click
from colorama import init, Fore, Style
from tabulate import tabulate
import json
import os

from scraper import (
    get_scraper,
    list_sites,
    SCRAPERS,
    SITE_NAMES,
    __version__
)

# Inicializar colorama
init(autoreset=True)


def print_banner():
    """Imprime el banner del sistema"""
    banner = f"""
{Fore.CYAN}╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   {Fore.YELLOW}BÚHO{Fore.CYAN} - Sistema de Scraping Gubernamental Bolivia      ║
║   {Fore.GREEN}FASE 9{Fore.CYAN}: Sites Reales + Parsers + Delta-Update        ║
║   Versión: {Fore.MAGENTA}{__version__}{Fore.CYAN}                                            ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
"""
    print(banner)


@click.group()
@click.version_option(version=__version__)
def cli():
    """
    BÚHO - Scraper de documentos gubernamentales de Bolivia

    Soporta scraping de: TCP, TSJ, Contraloría, ASFI, SIN
    Con actualización incremental y parsing avanzado de PDFs
    """
    print_banner()


@cli.command()
def listar():
    """Lista todos los sitios disponibles"""
    sites = list_sites()

    print(f"\n{Fore.YELLOW}Sitios Disponibles:{Style.RESET_ALL}\n")

    table_data = []
    for code, name in sites.items():
        table_data.append([
            f"{Fore.GREEN}{code}{Style.RESET_ALL}",
            name
        ])

    print(tabulate(table_data, headers=["Código", "Nombre Completo"], tablefmt="grid"))
    print(f"\n{Fore.CYAN}Total: {len(sites)} sitios{Style.RESET_ALL}\n")


@cli.command()
@click.argument('sitio', type=click.Choice(list(SCRAPERS.keys()), case_sensitive=False))
@click.option('--solo-nuevos', is_flag=True, help='Solo procesar documentos nuevos')
@click.option('--solo-modificados', is_flag=True, help='Solo procesar documentos modificados')
@click.option('--limit', type=int, help='Limitar número de documentos a procesar')
@click.option('--outputs-dir', default='outputs', help='Directorio de salidas')
def scrape(sitio, solo_nuevos, solo_modificados, limit, outputs_dir):
    """
    Ejecuta el scraper para un sitio específico

    Ejemplos:

        python main.py scrape tcp

        python main.py scrape tsj --solo-nuevos

        python main.py scrape asfi --limit 10
    """
    print(f"\n{Fore.YELLOW}Ejecutando scraper: {SITE_NAMES[sitio]}{Style.RESET_ALL}\n")

    try:
        scraper = get_scraper(sitio, outputs_dir=outputs_dir)
        stats = scraper.run(
            only_new=solo_nuevos,
            only_modified=solo_modificados,
            limit=limit
        )

        print(f"\n{Fore.GREEN}✓ Scraping completado exitosamente{Style.RESET_ALL}\n")

    except Exception as e:
        print(f"\n{Fore.RED}✗ Error durante el scraping: {e}{Style.RESET_ALL}\n")
        raise click.Abort()


@cli.command()
@click.option('--solo-nuevos', is_flag=True, help='Solo procesar documentos nuevos')
@click.option('--solo-modificados', is_flag=True, help='Solo procesar documentos modificados')
@click.option('--limit', type=int, help='Limitar número de documentos por sitio')
@click.option('--outputs-dir', default='outputs', help='Directorio de salidas')
@click.option('--sitios', help='Lista de sitios separados por coma (ej: tcp,tsj)')
def actualizar_todos(solo_nuevos, solo_modificados, limit, outputs_dir, sitios):
    """
    Actualiza todos los sitios o una lista específica

    Ejemplos:

        python main.py actualizar-todos

        python main.py actualizar-todos --solo-nuevos

        python main.py actualizar-todos --sitios tcp,tsj,asfi
    """
    # Determinar qué sitios procesar
    if sitios:
        sitios_list = [s.strip().lower() for s in sitios.split(',')]
        # Validar sitios
        for sitio in sitios_list:
            if sitio not in SCRAPERS:
                print(f"{Fore.RED}Error: Sitio '{sitio}' no reconocido{Style.RESET_ALL}")
                raise click.Abort()
    else:
        sitios_list = list(SCRAPERS.keys())

    print(f"\n{Fore.YELLOW}Actualizando {len(sitios_list)} sitios...{Style.RESET_ALL}\n")

    resultados = {}

    for sitio in sitios_list:
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"Procesando: {SITE_NAMES[sitio]}")
        print(f"{'='*60}{Style.RESET_ALL}\n")

        try:
            scraper = get_scraper(sitio, outputs_dir=outputs_dir)
            stats = scraper.run(
                only_new=solo_nuevos,
                only_modified=solo_modificados,
                limit=limit
            )
            resultados[sitio] = {'success': True, 'stats': stats}

        except Exception as e:
            print(f"{Fore.RED}Error en {sitio}: {e}{Style.RESET_ALL}")
            resultados[sitio] = {'success': False, 'error': str(e)}

    # Resumen final
    print(f"\n{Fore.YELLOW}{'='*60}")
    print("RESUMEN GENERAL")
    print(f"{'='*60}{Style.RESET_ALL}\n")

    table_data = []
    for sitio, resultado in resultados.items():
        if resultado['success']:
            stats = resultado['stats']
            table_data.append([
                f"{Fore.GREEN}✓{Style.RESET_ALL}",
                SITE_NAMES[sitio],
                stats.get('total_found', 0),
                stats.get('total_new', 0),
                stats.get('total_modified', 0),
                stats.get('total_skipped', 0),
            ])
        else:
            table_data.append([
                f"{Fore.RED}✗{Style.RESET_ALL}",
                SITE_NAMES[sitio],
                '-', '-', '-', '-'
            ])

    print(tabulate(table_data,
                   headers=['', 'Sitio', 'Encontrados', 'Nuevos', 'Modificados', 'Omitidos'],
                   tablefmt='grid'))

    print()


@cli.command()
@click.argument('sitio', type=click.Choice(list(SCRAPERS.keys()), case_sensitive=False))
@click.option('--outputs-dir', default='outputs', help='Directorio de salidas')
def estadisticas(sitio, outputs_dir):
    """
    Muestra estadísticas de un sitio específico

    Ejemplo:

        python main.py estadisticas tcp
    """
    print(f"\n{Fore.YELLOW}Estadísticas: {SITE_NAMES[sitio]}{Style.RESET_ALL}\n")

    try:
        scraper = get_scraper(sitio, outputs_dir=outputs_dir)
        stats = scraper.delta_manager.get_statistics()
        total_docs = scraper.delta_manager.index["total_documents"]

        print(f"{Fore.CYAN}Total de documentos registrados:{Style.RESET_ALL} {total_docs}")
        print(f"{Fore.CYAN}Última actualización:{Style.RESET_ALL} {scraper.delta_manager.index.get('last_updated', 'N/A')}")
        print(f"\n{Fore.YELLOW}Última ejecución:{Style.RESET_ALL}")
        print(f"  Fecha: {stats.get('last_run', 'N/A')}")
        print(f"  Procesados: {stats.get('total_processed', 0)}")
        print(f"  Nuevos: {stats.get('total_new', 0)}")
        print(f"  Modificados: {stats.get('total_modified', 0)}")
        print(f"  Omitidos: {stats.get('total_skipped', 0)}")
        print()

    except Exception as e:
        print(f"{Fore.RED}Error obteniendo estadísticas: {e}{Style.RESET_ALL}")
        raise click.Abort()


@cli.command()
@click.argument('sitio', type=click.Choice(list(SCRAPERS.keys()), case_sensitive=False))
@click.option('--outputs-dir', default='outputs', help='Directorio de salidas')
def limpiar_index(sitio, outputs_dir):
    """
    Limpia documentos del índice cuyos archivos no existen

    Ejemplo:

        python main.py limpiar-index tcp
    """
    print(f"\n{Fore.YELLOW}Limpiando índice: {SITE_NAMES[sitio]}{Style.RESET_ALL}\n")

    try:
        scraper = get_scraper(sitio, outputs_dir=outputs_dir)
        removed = scraper.delta_manager.cleanup_missing_files(scraper.pdfs_dir)

        print(f"{Fore.GREEN}✓ Limpieza completada{Style.RESET_ALL}")
        print(f"  Documentos eliminados del índice: {removed}\n")

    except Exception as e:
        print(f"{Fore.RED}Error durante limpieza: {e}{Style.RESET_ALL}")
        raise click.Abort()


@cli.command()
@click.option('--outputs-dir', default='outputs', help='Directorio de salidas')
def resumen(outputs_dir):
    """
    Muestra un resumen de todos los sitios
    """
    print(f"\n{Fore.YELLOW}Resumen General de Todos los Sitios{Style.RESET_ALL}\n")

    table_data = []

    for sitio_code, sitio_name in SITE_NAMES.items():
        try:
            scraper = get_scraper(sitio_code, outputs_dir=outputs_dir)
            total_docs = scraper.delta_manager.index["total_documents"]
            last_updated = scraper.delta_manager.index.get('last_updated', 'N/A')

            table_data.append([
                sitio_code.upper(),
                sitio_name,
                total_docs,
                last_updated
            ])
        except Exception:
            table_data.append([
                sitio_code.upper(),
                sitio_name,
                0,
                'N/A'
            ])

    print(tabulate(table_data,
                   headers=['Código', 'Sitio', 'Docs', 'Última Actualización'],
                   tablefmt='grid'))
    print()


if __name__ == '__main__':
    cli()
