#!/usr/bin/env python3
"""
Utilidad para verificar la disponibilidad de todos los sitios gubernamentales
Genera reporte de salud de infraestructura
"""
import logging
from datetime import datetime

from config import list_active_sites
from scraper.sites import get_scraper

# Configurar logging
logging.basicConfig(
    level=logging.WARNING,  # Solo warnings y errores
    format='%(message)s'
)

def check_all_sites():
    """Verificar disponibilidad de todos los sitios activos"""
    print("="*80)
    print(" VERIFICACIÓN DE SALUD DE SITIOS GUBERNAMENTALES BOLIVIANOS")
    print("="*80)
    print(f" Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    print()

    sites = list_active_sites()
    results = []

    for site_config in sites:
        print(f"Verificando {site_config.nombre}...", end=" ", flush=True)

        try:
            scraper = get_scraper(site_config.id)
            is_available, message = scraper.check_availability(force=True)

            status_icon = "✅" if is_available else "❌"
            print(f"{status_icon}")

            results.append({
                'Sitio': site_config.nombre,
                'ID': site_config.id,
                'Estado': status_icon,
                'Mensaje': message,
                'URL': site_config.url_base,
                'Prioridad': site_config.prioridad,
                'Ola': site_config.ola
            })

        except Exception as e:
            print(f"❌ Error")
            results.append({
                'Sitio': site_config.nombre,
                'ID': site_config.id,
                'Estado': "❌",
                'Mensaje': f"Error: {type(e).__name__}",
                'URL': site_config.url_base,
                'Prioridad': site_config.prioridad,
                'Ola': site_config.ola
            })

    # Generar reporte
    print("\n" + "="*80)
    print(" REPORTE DE DISPONIBILIDAD")
    print("="*80)
    print()

    # Tabla resumida
    print(f"{'Estado':<8} | {'Sitio':<40} | {'Mensaje':<45} | {'Fase':<6}")
    print("-" * 110)
    for r in results:
        print(f"{r['Estado']:<8} | {r['Sitio'][:40]:<40} | {r['Mensaje'][:45]:<45} | Ola {r['Ola']:<3}")

    # Estadísticas
    total = len(results)
    disponibles = sum(1 for r in results if r['Estado'] == "✅")
    no_disponibles = total - disponibles

    print("\n" + "="*80)
    print(" ESTADÍSTICAS")
    print("="*80)
    print(f" Total de sitios:        {total}")
    print(f" Disponibles:            {disponibles} ({disponibles/total*100:.1f}%)")
    print(f" No disponibles:         {no_disponibles} ({no_disponibles/total*100:.1f}%)")
    print("="*80)

    # Sitios problemáticos por ola
    if no_disponibles > 0:
        print("\n⚠️  SITIOS NO DISPONIBLES POR FASE:")
        for ola in sorted(set(r['Ola'] for r in results)):
            sitios_ola = [r for r in results if r['Ola'] == ola and r['Estado'] == "❌"]
            if sitios_ola:
                print(f"\n  Ola {ola}:")
                for s in sitios_ola:
                    print(f"    • {s['Sitio']}: {s['Mensaje']}")

    # Recomendaciones
    print("\n" + "="*80)
    print(" RECOMENDACIONES")
    print("="*80)

    if disponibles == total:
        print(" ✅ Todos los sitios están disponibles. Proceder con scraping.")
    else:
        print(f" ⚠️  {no_disponibles} sitios no disponibles.")
        print(" Recomendaciones:")
        print("   1. Ejecutar scraping solo para sitios disponibles")
        print("   2. Configurar monitoreo automático para detectar cuando sitios vuelvan")
        print("   3. Implementar cola de reintentos para sitios caídos")
        print("   4. Verificar manualmente problemas SSL en sitios con certificados mal configurados")

    print("="*80)

    return results

if __name__ == "__main__":
    results = check_all_sites()
