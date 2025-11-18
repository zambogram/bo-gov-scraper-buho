"""
PROGRAMA PRINCIPAL - SCRAPER DE LA GACETA OFICIAL DE BOLIVIA
=============================================================

Este es el punto de entrada principal de nuestro proyecto.
Aquí ejecutamos el scraper de la Gaceta Oficial de Bolivia.

¿Qué hace este programa?
- Importa el módulo del scraper
- Define la URL de inicio (página de listado de normas)
- Ejecuta el scraper para descargar documentos
- Muestra los resultados en pantalla
"""

import sys
import os

# Agregamos el directorio raíz al path para poder importar nuestros módulos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importamos nuestro scraper
from scraper.gaceta_scraper import run_gaceta_scraper


def main():
    """
    Función principal del programa.
    """

    print("\n")
    print("╔═══════════════════════════════════════════════════════════════╗")
    print("║                                                               ║")
    print("║     SCRAPER DE LA GACETA OFICIAL DE BOLIVIA                  ║")
    print("║     Descarga automática de normas y decretos                 ║")
    print("║                                                               ║")
    print("╚═══════════════════════════════════════════════════════════════╝")
    print("\n")

    # URL de la página de listado de decretos más recientes
    # Esta URL muestra los últimos decretos publicados
    url_inicial = "http://gacetaoficialdebolivia.gob.bo/normas/listadonordes/0"

    # Alternativas (puedes probar estas URLs si la primera no funciona):
    # url_inicial = "http://www.gacetaoficialdebolivia.gob.bo/normas/buscar/10/page/1"
    # url_inicial = "http://www.gacetaoficialdebolivia.gob.bo"

    # Configuración
    limite_descargas = 10  # Número de PDFs a descargar
    carpeta_destino = "data"  # Carpeta donde guardar los PDFs
    archivo_log = "exports/gaceta_log.csv"  # Archivo de registro

    print(f"📍 URL objetivo: {url_inicial}")
    print(f"📊 Límite de descargas: {limite_descargas} documentos")
    print(f"📁 Carpeta de destino: {carpeta_destino}/")
    print(f"📝 Archivo de log: {archivo_log}")
    print("\n")

    # Ejecutamos el scraper
    try:
        resultados = run_gaceta_scraper(
            url_inicial=url_inicial,
            limite=limite_descargas,
            carpeta_destino=carpeta_destino,
            archivo_log=archivo_log
        )

        # Mostramos los resultados detallados
        print("\n\n")
        print("╔═══════════════════════════════════════════════════════════════╗")
        print("║                    RESULTADOS FINALES                         ║")
        print("╚═══════════════════════════════════════════════════════════════╝")
        print()

        if resultados['total_descargados'] > 0:
            print(f"✅ ¡Proceso completado exitosamente!")
            print()
            print(f"📊 Documentos encontrados: {resultados['total_encontrados']}")
            print(f"✅ PDFs descargados: {resultados['total_descargados']}")
            print()
            print("📄 Archivos descargados:")
            print("-" * 60)

            for i, archivo in enumerate(resultados['archivos'], 1):
                ruta_completa = os.path.join(carpeta_destino, archivo)
                tamanio = os.path.getsize(ruta_completa) / 1024  # KB
                print(f"{i:2d}. {archivo}")
                print(f"    📁 Ubicación: {ruta_completa}")
                print(f"    📏 Tamaño: {tamanio:.2f} KB")
                print()

            print("-" * 60)
            print()
            print(f"📝 Registro completo guardado en: {archivo_log}")
            print(f"📁 Todos los PDFs están en: {carpeta_destino}/")

        else:
            print("⚠️  No se pudo descargar ningún documento.")
            print()
            print("Posibles causas:")
            print("- El sitio web puede estar temporalmente fuera de servicio")
            print("- La estructura de la página puede haber cambiado")
            print("- Puede haber problemas de conexión a internet")
            print()
            print("Intenta nuevamente más tarde o verifica la URL.")

    except KeyboardInterrupt:
        print("\n\n⚠️  Proceso interrumpido por el usuario.")
        print("Los archivos descargados hasta ahora se han guardado correctamente.")

    except Exception as e:
        print(f"\n\n❌ Error inesperado: {e}")
        print("Por favor, revisa los logs para más detalles.")

    print("\n")
    print("=" * 60)
    print("Fin del programa")
    print("=" * 60)
    print("\n")


if __name__ == "__main__":
    # Este bloque solo se ejecuta si corremos este archivo directamente
    # (no si lo importamos desde otro archivo)
    main()
