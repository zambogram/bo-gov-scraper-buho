#!/usr/bin/env python3
"""
BÚHO - Bolivian Government Document Scraper
Main CLI interface
"""
import sys
import os
import click
from rich.console import Console
from rich.table import Table
from rich import print as rprint

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scraper import get_scraper, SCRAPERS
from scraper.parser import LegalParser
from scraper.metadata import MetadataExtractor

console = Console()


@click.group()
def cli():
    """BÚHO - Bolivian Government Document Scraper"""
    pass


@cli.command()
def listar():
    """List all available scrapers and their stats"""
    table = Table(title="Available Scrapers", show_header=True, header_style="bold magenta")
    table.add_column("Site", style="cyan")
    table.add_column("Documents", justify="right")
    table.add_column("Articles", justify="right")
    table.add_column("Last Update", style="green")

    for name in SCRAPERS.keys():
        scraper = get_scraper(name)
        stats = scraper.get_stats()
        table.add_row(
            stats['name'],
            str(stats['total_documents']),
            str(stats['total_articles']),
            stats['last_update'] or 'Never'
        )

    console.print(table)


@cli.command()
@click.argument('site', type=click.Choice(list(SCRAPERS.keys())))
@click.option('--limit', '-l', type=int, default=10, help='Limit number of documents to scrape')
@click.option('--solo-nuevos', is_flag=True, help='Only scrape new documents')
def scrape(site, limit, solo_nuevos):
    """Scrape a specific site"""
    console.print(f"\n[bold cyan]Scraping {site}...[/bold cyan]\n")

    scraper = get_scraper(site)
    stats = scraper.scrape(limit=limit, only_new=solo_nuevos)

    console.print(f"[green]✓ Scraping complete![/green]")
    console.print(f"  New: {stats['new']}")
    console.print(f"  Modified: {stats['modified']}")
    console.print(f"  Unchanged: {stats['unchanged']}")
    console.print(f"  Errors: {stats['errors']}\n")

    # Parse articles
    console.print("[bold cyan]Parsing articles...[/bold cyan]")
    documents = scraper.load_index()
    articles = LegalParser.parse_all_documents(documents)
    scraper.save_articles(articles)
    console.print(f"[green]✓ Parsed {len(articles)} articles[/green]\n")


@cli.command()
@click.option('--solo-nuevos', is_flag=True, help='Only scrape new documents')
@click.option('--limit', '-l', type=int, default=10, help='Limit per site')
def actualizar_todos(solo_nuevos, limit):
    """Update all sites"""
    console.print("\n[bold cyan]Updating all sites...[/bold cyan]\n")

    total_stats = {'new': 0, 'modified': 0, 'unchanged': 0, 'errors': 0}

    for name in SCRAPERS.keys():
        console.print(f"[yellow]→ Scraping {name}...[/yellow]")
        scraper = get_scraper(name)
        stats = scraper.scrape(limit=limit, only_new=solo_nuevos)

        for key in total_stats:
            total_stats[key] += stats[key]

        # Parse articles
        documents = scraper.load_index()
        articles = LegalParser.parse_all_documents(documents)
        scraper.save_articles(articles)

        console.print(f"  New: {stats['new']}, Modified: {stats['modified']}, Articles: {len(articles)}")

    console.print(f"\n[green]✓ All sites updated![/green]")
    console.print(f"  Total New: {total_stats['new']}")
    console.print(f"  Total Modified: {total_stats['modified']}")
    console.print(f"  Total Unchanged: {total_stats['unchanged']}")
    console.print(f"  Total Errors: {total_stats['errors']}\n")


@cli.command()
@click.argument('site', type=click.Choice(list(SCRAPERS.keys()) + ['all']))
def export_jsonl(site):
    """Export documents and articles to JSONL format"""
    if site == 'all':
        sites = list(SCRAPERS.keys())
    else:
        sites = [site]

    for site_name in sites:
        console.print(f"\n[bold cyan]Exporting {site_name}...[/bold cyan]")
        scraper = get_scraper(site_name)
        result = scraper.export_jsonl()

        console.print(f"[green]✓ Exported {result['documents']} documents[/green]")
        console.print(f"  → {result['documents_path']}")
        console.print(f"[green]✓ Exported {result['articles']} articles[/green]")
        console.print(f"  → {result['articles_path']}\n")


@cli.command()
@click.argument('site', type=click.Choice(list(SCRAPERS.keys())))
def stats(site):
    """Show detailed statistics for a site"""
    scraper = get_scraper(site)
    site_stats = scraper.get_stats()

    console.print(f"\n[bold cyan]Statistics for {site}[/bold cyan]\n")
    console.print(f"Total Documents: {site_stats['total_documents']}")
    console.print(f"Total Articles: {site_stats['total_articles']}")
    console.print(f"Last Update: {site_stats['last_update'] or 'Never'}\n")


@cli.command()
def ui():
    """Launch Streamlit UI"""
    console.print("[bold cyan]Launching Streamlit UI...[/bold cyan]\n")
    import subprocess
    app_path = os.path.join(os.path.dirname(__file__), 'app', 'streamlit_app.py')
    subprocess.run(['streamlit', 'run', app_path])


if __name__ == '__main__':
    cli()
