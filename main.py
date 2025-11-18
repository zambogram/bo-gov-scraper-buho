#!/usr/bin/env python3
"""
BÚHO - Motor Multi-sitio de Scraping Jurídico Boliviano
========================================================

CLI principal del sistema de scraping de fuentes estatales bolivianas.

Comandos disponibles:
    list        - Listar sitios del catálogo
    info        - Información detallada de un sitio
    stats       - Estadísticas del catálogo
    scrape      - Ejecutar scraping de un sitio
    demo-ola1   - Demo del scraping de sitios Ola 1
    validate    - Validar integridad del catálogo
    export      - Exportar datos a formato Supabase

Autor: BÚHO LegalTech
Fecha: 2025-01-18
"""

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
from tabulate import tabulate
import sys
from pathlib import Path

# Importar módulos del proyecto
sys.path.insert(0, str(Path(__file__).parent))
from scraper.catalog import CatalogManager, SiteInfo


# ========================================
# CONFIGURACIÓN
# ========================================

console = Console()


# ========================================
# UTILIDADES DE DISPLAY
# ========================================

def print_header():
    """Imprimir header del sistema."""
    console.print()
    console.print(Panel.fit(
        "[bold cyan]BÚHO[/bold cyan] - Motor Multi-sitio de Scraping Jurídico Boliviano\n"
        "[dim]Sistema de captura, procesamiento y exportación de normativa y jurisprudencia[/dim]",
        border_style="cyan",
        box=box.DOUBLE
    ))
    console.print()


def get_status_emoji(estado: str) -> str:
    """Obtener emoji según estado del scraper."""
    emojis = {
        "implementado": "✅",
        "en_progreso": "🔄",
        "pendiente": "⏳",
        "deshabilitado": "❌"
    }
    return emojis.get(estado, "❓")


def get_prioridad_badge(prioridad: int) -> str:
    """Obtener badge según prioridad."""
    badges = {
        1: "[bold red]●[/bold red] P1",
        2: "[bold yellow]●[/bold yellow] P2",
        3: "[bold green]●[/bold green] P3"
    }
    return badges.get(prioridad, "● P?")


# ========================================
# GRUPO PRINCIPAL DE COMANDOS
# ========================================

@click.group()
@click.version_option(version="1.0.0", prog_name="BÚHO Scraper")
def cli():
    """
    BÚHO - Motor Multi-sitio de Scraping Jurídico Boliviano.

    Sistema completo para capturar, procesar y exportar normativa y
    jurisprudencia de fuentes estatales bolivianas.
    """
    pass


# ========================================
# COMANDO: LIST
# ========================================

@cli.command()
@click.option('--prioridad', '-p', type=int, help='Filtrar por prioridad (1, 2, 3)')
@click.option('--estado', '-e', help='Filtrar por estado (pendiente, implementado, etc.)')
@click.option('--nivel', '-n', help='Filtrar por nivel (nacional, departamental, municipal)')
@click.option('--tipo', '-t', help='Filtrar por tipo (normativa, jurisprudencia, regulador)')
@click.option('--json', 'output_json', is_flag=True, help='Salida en formato JSON')
def list(prioridad, estado, nivel, tipo, output_json):
    """
    Listar sitios del catálogo.

    Ejemplos:
        python main.py list
        python main.py list --prioridad 1
        python main.py list --estado implementado
        python main.py list --tipo normativa
    """
    print_header()

    # Cargar catálogo
    catalog = CatalogManager()

    # Aplicar filtros
    sites = catalog.search_sites(
        prioridad=prioridad,
        estado=estado,
        nivel=nivel,
        tipo_fuente=tipo
    )

    if not sites:
        console.print("[yellow]No se encontraron sitios con los filtros especificados.[/yellow]")
        return

    # Output JSON
    if output_json:
        import json
        data = [site.to_dict() for site in sites]
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return

    # Output tabla
    console.print(f"[bold]Total de sitios:[/bold] {len(sites)}\n")

    table = Table(show_header=True, header_style="bold cyan", box=box.ROUNDED)
    table.add_column("ID", style="cyan", width=20)
    table.add_column("Nombre", style="white", width=40)
    table.add_column("Tipo", width=12)
    table.add_column("Nivel", width=10)
    table.add_column("Pri", justify="center", width=5)
    table.add_column("Estado", width=15)
    table.add_column("Docs", justify="right", width=8)

    for site in sorted(sites, key=lambda s: (s.prioridad, s.site_id)):
        estado_display = f"{get_status_emoji(site.estado_scraper)} {site.estado_scraper}"

        table.add_row(
            site.site_id,
            site.nombre[:37] + "..." if len(site.nombre) > 40 else site.nombre,
            site.tipo_fuente,
            site.nivel,
            str(site.prioridad),
            estado_display,
            str(site.documentos_totales)
        )

    console.print(table)
    console.print()


# ========================================
# COMANDO: INFO
# ========================================

@cli.command()
@click.argument('site_id')
@click.option('--json', 'output_json', is_flag=True, help='Salida en formato JSON')
def info(site_id, output_json):
    """
    Mostrar información detallada de un sitio.

    Ejemplos:
        python main.py info gaceta_oficial
        python main.py info tcp
        python main.py info asfi --json
    """
    print_header()

    # Cargar catálogo
    catalog = CatalogManager()
    site = catalog.get_site(site_id)

    if not site:
        console.print(f"[red]✗[/red] Sitio no encontrado: [yellow]{site_id}[/yellow]")
        console.print("\nUsa [cyan]python main.py list[/cyan] para ver sitios disponibles.")
        sys.exit(1)

    # Output JSON
    if output_json:
        print(site.to_json())
        return

    # Output formateado
    console.print(f"[bold cyan]{site.nombre}[/bold cyan]\n")

    # Información básica
    info_basica = Table(show_header=False, box=box.SIMPLE, padding=(0, 2))
    info_basica.add_row("[bold]ID:[/bold]", f"[cyan]{site.site_id}[/cyan]")
    info_basica.add_row("[bold]Nivel:[/bold]", site.nivel)
    info_basica.add_row("[bold]Tipo:[/bold]", site.tipo_fuente)
    info_basica.add_row("[bold]Prioridad:[/bold]", f"{site.prioridad} ({'MVP' if site.prioridad == 1 else 'Importante' if site.prioridad == 2 else 'Complementario'})")
    info_basica.add_row("[bold]Estado:[/bold]", f"{get_status_emoji(site.estado_scraper)} {site.estado_scraper}")
    console.print(Panel(info_basica, title="📋 Información Básica", border_style="blue"))

    # URLs
    console.print()
    urls = Table(show_header=False, box=box.SIMPLE, padding=(0, 2))
    urls.add_row("[bold]URL Base:[/bold]", f"[link={site.url_base}]{site.url_base}[/link]")
    if site.url_busqueda:
        urls.add_row("[bold]URL Búsqueda:[/bold]", f"[link={site.url_busqueda}]{site.url_busqueda}[/link]")
    if site.url_listado:
        urls.add_row("[bold]URL Listado:[/bold]", f"[link={site.url_listado}]{site.url_listado}[/link]")
    console.print(Panel(urls, title="🔗 URLs", border_style="green"))

    # Características técnicas
    console.print()
    tecnicas = Table(show_header=False, box=box.SIMPLE, padding=(0, 2))
    tecnicas.add_row("[bold]Formato:[/bold]", site.formato_documento)
    tecnicas.add_row("[bold]Requiere Selenium:[/bold]", "✓ Sí" if site.requiere_selenium else "✗ No")
    tecnicas.add_row("[bold]Requiere Login:[/bold]", "✓ Sí" if site.requiere_login else "✗ No")
    tecnicas.add_row("[bold]Tiene API:[/bold]", "✓ Sí" if site.tiene_api else "✗ No")
    tecnicas.add_row("[bold]Estructura:[/bold]", site.estructura_texto)
    console.print(Panel(tecnicas, title="⚙️  Características Técnicas", border_style="yellow"))

    # Estadísticas
    console.print()
    stats = Table(show_header=False, box=box.SIMPLE, padding=(0, 2))
    stats.add_row("[bold]Frecuencia:[/bold]", site.frecuencia_actualizacion)
    stats.add_row("[bold]Última actualización:[/bold]", site.ultima_actualizacion or "[dim]Nunca[/dim]")
    stats.add_row("[bold]Documentos totales:[/bold]", f"[cyan]{site.documentos_totales:,}[/cyan]")
    stats.add_row("[bold]Artículos totales:[/bold]", f"[cyan]{site.articulos_totales:,}[/cyan]")
    console.print(Panel(stats, title="📊 Estadísticas", border_style="magenta"))

    # Tipos de documentos
    if site.tipos_documentos:
        console.print()
        console.print(Panel(
            ", ".join(site.tipos_documentos),
            title="📄 Tipos de Documentos",
            border_style="cyan"
        ))

    # Notas
    if site.notas:
        console.print()
        console.print(Panel(
            site.notas,
            title="📝 Notas",
            border_style="white"
        ))

    console.print()


# ========================================
# COMANDO: STATS
# ========================================

@cli.command()
@click.option('--json', 'output_json', is_flag=True, help='Salida en formato JSON')
def stats(output_json):
    """
    Mostrar estadísticas del catálogo completo.

    Ejemplo:
        python main.py stats
        python main.py stats --json
    """
    print_header()

    # Cargar catálogo
    catalog = CatalogManager()
    stats_data = catalog.get_stats()

    # Output JSON
    if output_json:
        import json
        print(json.dumps(stats_data, indent=2, ensure_ascii=False))
        return

    # Output formateado
    console.print("[bold cyan]📊 Estadísticas del Catálogo[/bold cyan]\n")

    # Tabla general
    general = Table(show_header=False, box=box.ROUNDED, padding=(0, 2))
    general.add_row("[bold]Total de sitios:[/bold]", f"[cyan]{stats_data['total_sitios']}[/cyan]")
    general.add_row("[bold]Implementados:[/bold]", f"[green]{stats_data['implementados']}[/green]")
    general.add_row("[bold]En progreso:[/bold]", f"[yellow]{stats_data['en_progreso']}[/yellow]")
    general.add_row("[bold]Pendientes:[/bold]", f"[red]{stats_data['pendientes']}[/red]")
    general.add_row("[bold]Completado:[/bold]", f"{stats_data['porcentaje_completado']}%")
    console.print(general)

    console.print()

    # Tabla de documentos
    docs = Table(show_header=False, box=box.ROUNDED, padding=(0, 2))
    docs.add_row("[bold]Total documentos procesados:[/bold]", f"[cyan]{stats_data['total_documentos']:,}[/cyan]")
    docs.add_row("[bold]Total artículos extraídos:[/bold]", f"[cyan]{stats_data['total_articulos']:,}[/cyan]")
    console.print(docs)

    console.print()

    # Distribución
    console.print("[bold]Por Prioridad:[/bold]")
    for prio, count in stats_data['por_prioridad'].items():
        console.print(f"  {get_prioridad_badge(prio)}: {count} sitios")

    console.print()
    console.print("[bold]Por Nivel:[/bold]")
    for nivel, count in stats_data['por_nivel'].items():
        console.print(f"  • {nivel.capitalize()}: {count} sitios")

    console.print()
    console.print("[bold]Por Tipo:[/bold]")
    for tipo, count in stats_data['por_tipo'].items():
        console.print(f"  • {tipo.capitalize()}: {count} sitios")

    console.print()


# ========================================
# COMANDO: SCRAPE
# ========================================

@cli.command()
@click.argument('site_id')
@click.option('--limit', '-l', type=int, default=10, help='Límite de documentos a procesar')
@click.option('--full', is_flag=True, help='Scraping completo (sin límite)')
@click.option('--force', is_flag=True, help='Forzar re-scraping (ignorar delta-update)')
def scrape(site_id, limit, full, force):
    """
    Ejecutar scraping de un sitio específico.

    Ejemplos:
        python main.py scrape gaceta_oficial
        python main.py scrape tcp --limit 5
        python main.py scrape asfi --full
    """
    print_header()

    # Cargar catálogo
    catalog = CatalogManager()
    site = catalog.get_site(site_id)

    if not site:
        console.print(f"[red]✗[/red] Sitio no encontrado: [yellow]{site_id}[/yellow]")
        sys.exit(1)

    console.print(f"[bold cyan]Scraping:[/bold cyan] {site.nombre}")
    console.print(f"[dim]URL:[/dim] {site.url_base}\n")

    # Verificar si está implementado
    if site.estado_scraper == "pendiente":
        console.print("[yellow]⚠[/yellow]  [bold]Scraper no implementado aún[/bold]")
        console.print(f"\nEste sitio está catalogado pero el scraper no ha sido desarrollado.")
        console.print(f"Estado actual: [yellow]{site.estado_scraper}[/yellow]")
        console.print(f"Prioridad: {site.prioridad} ({'Ola 1 - MVP' if site.prioridad == 1 else 'Ola 2+'})")
        console.print()
        return

    if site.estado_scraper == "deshabilitado":
        console.print("[red]✗[/red] [bold]Scraper deshabilitado[/bold]")
        if site.notas:
            console.print(f"\nMotivo: {site.notas}")
        console.print()
        return

    # TODO: Implementar lógica de scraping real
    console.print("[yellow]⚠[/yellow]  Scraping aún no implementado (módulo en desarrollo)")
    console.print(f"\nParámetros configurados:")
    console.print(f"  • Límite: {'Sin límite' if full else limit} documentos")
    console.print(f"  • Modo: {'Full scraping' if force else 'Delta-update'}")
    console.print()


# ========================================
# COMANDO: VALIDATE
# ========================================

@cli.command()
def validate():
    """
    Validar la integridad del catálogo.

    Ejemplo:
        python main.py validate
    """
    print_header()

    console.print("[bold cyan]Validando catálogo...[/bold cyan]\n")

    # Cargar y validar
    catalog = CatalogManager()
    errores = catalog.validate_catalog()

    if not errores:
        console.print("[green]✓[/green] Catálogo válido - sin errores")
        console.print()
        return

    # Mostrar errores
    console.print(f"[red]✗[/red] Se encontraron {len(errores)} errores:\n")
    for i, error in enumerate(errores, 1):
        console.print(f"  {i}. [red]{error}[/red]")

    console.print()
    sys.exit(1)


# ========================================
# COMANDO: DEMO-OLA1
# ========================================

@cli.command()
@click.option('--limit', '-l', type=int, default=3, help='Límite de documentos por sitio')
def demo_ola1(limit):
    """
    Demo de scraping para sitios de Ola 1 (MVP).

    Ejecuta scraping limitado de todos los sitios prioritarios.

    Ejemplo:
        python main.py demo-ola1
        python main.py demo-ola1 --limit 5
    """
    print_header()

    console.print("[bold cyan]🚀 DEMO - Scraping Ola 1 (MVP)[/bold cyan]\n")

    # Cargar catálogo
    catalog = CatalogManager()
    ola1_sites = catalog.get_ola1_sites()

    console.print(f"Sitios a procesar: {len(ola1_sites)}")
    console.print(f"Límite por sitio: {limit} documentos\n")

    # Listar sitios
    for site in ola1_sites:
        status = get_status_emoji(site.estado_scraper)
        console.print(f"  {status} {site.site_id:20s} - {site.nombre}")

    console.print()

    # TODO: Implementar scraping real
    console.print("[yellow]⚠[/yellow]  Demo aún no implementado (módulo de scraping en desarrollo)")
    console.print("\nPróximos pasos:")
    console.print("  1. Implementar scrapers individuales para cada sitio")
    console.print("  2. Conectar con pipeline de procesamiento (PDF → texto → artículos)")
    console.print("  3. Exportar a formato Supabase")
    console.print()


# ========================================
# MAIN
# ========================================

if __name__ == '__main__':
    try:
        cli()
    except KeyboardInterrupt:
        console.print("\n\n[yellow]Operación cancelada por el usuario.[/yellow]\n")
        sys.exit(130)
    except Exception as e:
        console.print(f"\n[red]✗ Error:[/red] {str(e)}\n", style="bold red")
        sys.exit(1)
