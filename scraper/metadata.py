"""
Scraper de metadatos de la Gaceta Oficial de Bolivia
Usa Selenium con Chromium y Chromedriver
"""
import os
import time
import json
from datetime import datetime
from typing import List, Dict, Optional
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException


# URL de la Gaceta Oficial de Bolivia
GACETA_URL = "https://gacetaoficialdebolivia.gob.bo/index.php/normas/lista"


def crear_driver() -> webdriver.Chrome:
    """
    Crea y configura el driver de Chrome/Chromium con las rutas correctas
    """
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-software-rasterizer')
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-setuid-sandbox')
    options.add_argument('--single-process')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36')

    # Configurar proxy si está disponible
    http_proxy = os.environ.get('HTTP_PROXY') or os.environ.get('http_proxy')
    if http_proxy:
        # Extraer host y puerto del proxy
        proxy_server = http_proxy.replace('http://', '').replace('https://', '')
        options.add_argument(f'--proxy-server={http_proxy}')
        print(f"Configurando proxy: {http_proxy[:50]}...")

    # Configurar ruta del binario de Chromium
    options.binary_location = "/root/.cache/ms-playwright/chromium-1194/chrome-linux/chrome"

    # Configurar servicio con la ruta de chromedriver
    service = Service("/home/user/bo-gov-scraper-buho/bin/chromedriver")

    # Crear el driver
    driver = webdriver.Chrome(service=service, options=options)
    return driver


def scrapear_gaceta(limit: int = 10) -> List[Dict]:
    """
    Scrapea la Gaceta Oficial de Bolivia y extrae metadatos

    Args:
        limit: Número máximo de documentos a scrapear

    Returns:
        Lista de diccionarios con metadatos de cada documento
    """
    print(f"Iniciando scraper de Gaceta Oficial de Bolivia...")
    print(f"URL: {GACETA_URL}")

    driver = crear_driver()
    documentos = []

    try:
        print(f"\nAccediendo a la página...")
        driver.get(GACETA_URL)

        # Esperar a que la página cargue
        wait = WebDriverWait(driver, 20)
        print("Esperando que la página cargue...")

        # Tomar screenshot para debug
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = f"/home/user/bo-gov-scraper-buho/data/screenshot_{timestamp}.png"
        driver.save_screenshot(screenshot_path)
        print(f"Screenshot guardado en: {screenshot_path}")

        # Obtener el título de la página
        print(f"\nTítulo de la página: {driver.title}")

        # Obtener el HTML de la página
        html_content = driver.page_source
        print(f"Longitud del HTML: {len(html_content)} caracteres")

        # Guardar HTML para análisis
        html_path = f"/home/user/bo-gov-scraper-buho/data/page_{timestamp}.html"
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"HTML guardado en: {html_path}")

        # Intentar encontrar elementos de documentos
        # Esto es un ejemplo, necesitaremos ajustar los selectores según la estructura real
        try:
            # Esperar a que haya contenido en la página
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

            # Intentar encontrar tablas, listas o elementos comunes
            elementos_encontrados = {
                "tables": len(driver.find_elements(By.TAG_NAME, "table")),
                "divs": len(driver.find_elements(By.TAG_NAME, "div")),
                "links": len(driver.find_elements(By.TAG_NAME, "a")),
                "forms": len(driver.find_elements(By.TAG_NAME, "form")),
            }
            print(f"\nElementos HTML encontrados:")
            for elem_type, count in elementos_encontrados.items():
                print(f"  {elem_type}: {count}")

            # Buscar enlaces de documentos (ajustar selector según estructura real)
            enlaces = driver.find_elements(By.TAG_NAME, "a")
            print(f"\nAnalizando {len(enlaces)} enlaces...")

            for i, enlace in enumerate(enlaces[:limit]):
                try:
                    texto = enlace.text.strip()
                    href = enlace.get_attribute('href')

                    if texto and href:
                        doc = {
                            'id': i + 1,
                            'titulo': texto,
                            'url': href,
                            'fecha_scraping': datetime.now().isoformat(),
                            'fuente': 'Gaceta Oficial de Bolivia'
                        }
                        documentos.append(doc)
                        print(f"  Doc {i+1}: {texto[:80]}...")

                except Exception as e:
                    print(f"  Error procesando enlace {i+1}: {e}")
                    continue

        except TimeoutException:
            print("Timeout esperando elementos de la página")

    except Exception as e:
        print(f"Error durante el scraping: {e}")
        import traceback
        traceback.print_exc()

    finally:
        driver.quit()
        print(f"\nScraping completado. {len(documentos)} documentos extraídos.")

    return documentos


def guardar_resultados(documentos: List[Dict], filename: str = "gaceta_metadata.json"):
    """
    Guarda los resultados en un archivo JSON
    """
    filepath = f"/home/user/bo-gov-scraper-buho/data/{filename}"
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(documentos, f, ensure_ascii=False, indent=2)
    print(f"Resultados guardados en: {filepath}")
    return filepath


def run_full_pipeline(limit: int = 10, forzar_reprocesar: bool = False):
    """
    Ejecuta el pipeline completo de scraping

    Args:
        limit: Número máximo de documentos a scrapear
        forzar_reprocesar: Si True, reprocesa todo aunque ya existan datos
    """
    print("=" * 80)
    print("PIPELINE DE SCRAPING - GACETA OFICIAL DE BOLIVIA")
    print("=" * 80)
    print(f"Configuración:")
    print(f"  - Límite de documentos: {limit}")
    print(f"  - Forzar reprocesar: {forzar_reprocesar}")
    print(f"  - Chromium: /root/.cache/ms-playwright/chromium-1194/chrome-linux/chrome")
    print(f"  - ChromeDriver: /home/user/bo-gov-scraper-buho/bin/chromedriver")
    print("=" * 80)

    # Ejecutar scraping
    documentos = scrapear_gaceta(limit=limit)

    # Guardar resultados
    if documentos:
        guardar_resultados(documentos)
        print(f"\n✓ Pipeline completado exitosamente")
        print(f"  Total de documentos: {len(documentos)}")
    else:
        print(f"\n⚠ No se extrajeron documentos")

    return documentos


if __name__ == "__main__":
    # Prueba básica
    run_full_pipeline(limit=5, forzar_reprocesar=False)
