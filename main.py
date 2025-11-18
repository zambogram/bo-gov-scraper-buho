#!/usr/bin/env python3
"""
Motor Multi-Sitio para Scraping de Sitios Gubernamentales de Bolivia.

Este script permite ejecutar scrapers para diferentes sitios gubernamentales
usando una arquitectura modular y configurable.

Uso:
    python main.py --sitio gaceta --limite 10 --reprocesar false
    python main.py --sitio hermes --limite 50
    python main.py --listar-sitios
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any


def cargar_configuracion(config_path: str = "config/sites.json") -> Dict[str, Any]:
    """
    Carga el archivo de configuración de sitios.

    Args:
        config_path: Ruta al archivo de configuración

    Returns:
        Diccionario con la configuración
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"ERROR: No se encontró el archivo de configuración: {config_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"ERROR: Error al parsear el archivo de configuración: {e}")
        sys.exit(1)


def listar_sitios_disponibles(config: Dict[str, Any]):
    """
    Muestra una lista de todos los sitios disponibles.

    Args:
        config: Configuración cargada
    """
    print("\n" + "=" * 70)
    print("SITIOS GUBERNAMENTALES DISPONIBLES")
    print("=" * 70 + "\n")

    sitios = config.get('sites', {})

    if not sitios:
        print("No hay sitios configurados.")
        return

    for site_id, site_config in sitios.items():
        nombre = site_config.get('nombre', 'Sin nombre')
        tipo = site_config.get('tipo', 'Sin tipo')
        descripcion = site_config.get('descripcion', 'Sin descripción')
        url = site_config.get('url_listado', 'Sin URL')

        print(f"ID: {site_id}")
        print(f"   Nombre: {nombre}")
        print(f"   Tipo: {tipo}")
        print(f"   Descripción: {descripcion}")
        print(f"   URL: {url}")
        print()

    print("=" * 70)
    print(f"\nTotal de sitios disponibles: {len(sitios)}")
    print("\nUso: python main.py --sitio <id> --limite <número>")
    print("=" * 70 + "\n")


def obtener_scraper(site_id: str, config_path: str = "config/sites.json"):
    """
    Obtiene la instancia del scraper apropiado para el sitio.

    Args:
        site_id: ID del sitio
        config_path: Ruta al archivo de configuración

    Returns:
        Instancia del scraper
    """
    # Importar scrapers disponibles
    from scraper.sites.gaceta import GacetaScraper

    # Mapeo de IDs a clases de scrapers
    scrapers_map = {
        'gaceta': GacetaScraper,
        # Aquí se agregarán más scrapers en el futuro:
        # 'hermes': HermesScraper,
        # 'icoes': IcoesScraper,
        # 'derechos_reales': DerechosRealesScraper,
        # 'sin': SinScraper,
    }

    scraper_class = scrapers_map.get(site_id)

    if not scraper_class:
        print(f"ERROR: No existe implementación para el sitio '{site_id}'")
        print(f"\nScrapers implementados: {', '.join(scrapers_map.keys())}")
        print("\nNOTA: El sitio está configurado pero aún no tiene implementación.")
        print("Consulte FASE7_MULTISITIO.md para aprender a crear un nuevo scraper.")
        sys.exit(1)

    return scraper_class(config_path=config_path)


def main():
    """Función principal del motor multi-sitio."""

    parser = argparse.ArgumentParser(
        description='Motor Multi-Sitio para Scraping de Sitios Gubernamentales',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:

  # Listar todos los sitios disponibles
  python main.py --listar-sitios

  # Scraping de la Gaceta Oficial (límite 10 documentos)
  python main.py --sitio gaceta --limite 10

  # Scraping sin límite y reprocesando documentos existentes
  python main.py --sitio gaceta --reprocesar

  # Scraping con configuración personalizada
  python main.py --sitio hermes --limite 50 --config config/mi_config.json

Para más información, consulte FASE7_MULTISITIO.md
        """
    )

    parser.add_argument(
        '--sitio',
        type=str,
        help='ID del sitio a scrapear (ej: gaceta, hermes, icoes)'
    )

    parser.add_argument(
        '--limite',
        type=int,
        default=None,
        help='Número máximo de documentos a procesar (default: sin límite)'
    )

    parser.add_argument(
        '--reprocesar',
        action='store_true',
        help='Reprocesar documentos ya descargados (default: false)'
    )

    parser.add_argument(
        '--config',
        type=str,
        default='config/sites.json',
        help='Ruta al archivo de configuración (default: config/sites.json)'
    )

    parser.add_argument(
        '--listar-sitios',
        action='store_true',
        help='Listar todos los sitios disponibles'
    )

    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 1.0.0 - Fase 7: Motor Multi-Sitio'
    )

    args = parser.parse_args()

    # Cargar configuración
    config = cargar_configuracion(args.config)

    # Listar sitios si se solicita
    if args.listar_sitios:
        listar_sitios_disponibles(config)
        return

    # Validar que se especificó un sitio
    if not args.sitio:
        parser.print_help()
        print("\n" + "=" * 70)
        print("ERROR: Debe especificar un sitio usando --sitio")
        print("=" * 70)
        print("\nUse --listar-sitios para ver los sitios disponibles")
        sys.exit(1)

    # Validar que el sitio existe en la configuración
    sitios_disponibles = config.get('sites', {})
    if args.sitio not in sitios_disponibles:
        print(f"ERROR: El sitio '{args.sitio}' no está configurado")
        print(f"\nSitios disponibles: {', '.join(sitios_disponibles.keys())}")
        print("\nUse --listar-sitios para más detalles")
        sys.exit(1)

    # Banner de inicio
    site_config = sitios_disponibles[args.sitio]
    print("\n" + "=" * 70)
    print("MOTOR MULTI-SITIO - SCRAPER GUBERNAMENTAL")
    print("=" * 70)
    print(f"Sitio: {site_config.get('nombre', args.sitio)}")
    print(f"Tipo: {site_config.get('tipo', 'N/A')}")
    print(f"URL: {site_config.get('url_listado', 'N/A')}")
    print(f"Límite: {args.limite if args.limite else 'Sin límite'}")
    print(f"Reprocesar: {'Sí' if args.reprocesar else 'No'}")
    print("=" * 70 + "\n")

    try:
        # Obtener el scraper apropiado
        scraper = obtener_scraper(args.sitio, args.config)

        # Ejecutar el scraping
        scraper.run(limite=args.limite, reprocesar=args.reprocesar)

        print("\n" + "=" * 70)
        print("SCRAPING COMPLETADO EXITOSAMENTE")
        print("=" * 70 + "\n")

    except KeyboardInterrupt:
        print("\n\nProceso interrumpido por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nERROR FATAL: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
