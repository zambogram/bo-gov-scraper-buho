"""
Scraper para Tribunal Constitucional Plurinacional - Jurisprudencia
Extrae sentencias constitucionales usando Selenium para navegar por el HTML dinámico

Sitios cubiertos:
- https://jurisprudencia.tcpbolivia.bo/
- https://buscador.tcpbolivia.bo/busqueda-jurisprudencia
"""

import time
import hashlib
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import re
import logging

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException,
    StaleElementReferenceException, WebDriverException
)
from webdriver_manager.chrome import ChromeDriverManager

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TCPJurisprudenciaScraper:
    """
    Scraper especializado para jurisprudencia del TCP usando Selenium
    """

    def __init__(self, output_dir: str = "data/raw/tcp_jurisprudencia",
                 headless: bool = True,
                 timeout: int = 30,
                 retry_attempts: int = 3):
        """
        Inicializa el scraper del TCP

        Args:
            output_dir: Directorio para guardar archivos descargados
            headless: Si se debe ejecutar el navegador sin interfaz gráfica
            timeout: Timeout en segundos para esperar elementos
            retry_attempts: Número de intentos para reintentar operaciones fallidas
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.headless = headless
        self.timeout = timeout
        self.retry_attempts = retry_attempts

        # URLs del TCP
        self.urls = [
            "https://jurisprudencia.tcpbolivia.bo/",
            "https://buscador.tcpbolivia.bo/busqueda-jurisprudencia"
        ]

        self.driver = None
        self.wait = None

        # Estadísticas
        self.estadisticas = {
            'sentencias_encontradas': 0,
            'sentencias_procesadas': 0,
            'pdfs_descargados': 0,
            'errores': []
        }

        # Session para descargas
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })

    def inicializar_driver(self):
        """Inicializa el driver de Selenium con Chrome"""
        try:
            chrome_options = Options()

            if self.headless:
                chrome_options.add_argument('--headless')
                chrome_options.add_argument('--disable-gpu')

            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)

            # User agent
            chrome_options.add_argument('user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

            # Instalar y configurar ChromeDriver
            service = Service(ChromeDriverManager().install())

            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.set_page_load_timeout(self.timeout)

            # WebDriverWait para esperar elementos
            self.wait = WebDriverWait(self.driver, self.timeout)

            logger.info("✅ Driver de Selenium inicializado correctamente")

        except Exception as e:
            logger.error(f"❌ Error al inicializar Selenium: {e}")
            raise

    def cerrar_driver(self):
        """Cierra el driver de Selenium"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("✅ Driver cerrado correctamente")
            except Exception as e:
                logger.error(f"⚠️  Error al cerrar driver: {e}")

    def scrapear_todo(self) -> Dict:
        """
        Ejecuta el scraping completo de todas las URLs del TCP

        Returns:
            Diccionario con resultados del scraping
        """
        logger.info("🚀 Iniciando scraping del TCP - Jurisprudencia")

        resultados = {
            'exitoso': False,
            'sentencias': [],
            'total_procesadas': 0,
            'total_descargadas': 0,
            'errores': []
        }

        try:
            self.inicializar_driver()

            # Intentar con cada URL
            for url in self.urls:
                logger.info(f"\n📡 Scrapeando: {url}")

                try:
                    sentencias = self._scrapear_sitio(url)
                    resultados['sentencias'].extend(sentencias)
                    logger.info(f"✅ {len(sentencias)} sentencias extraídas de {url}")

                except Exception as e:
                    error_msg = f"Error scrapeando {url}: {e}"
                    logger.error(f"❌ {error_msg}")
                    resultados['errores'].append(error_msg)

            resultados['total_procesadas'] = len(resultados['sentencias'])
            resultados['exitoso'] = resultados['total_procesadas'] > 0

            logger.info(f"\n✅ Scraping completado: {resultados['total_procesadas']} sentencias")

        except Exception as e:
            error_msg = f"Error general en scraping: {e}"
            logger.error(f"❌ {error_msg}")
            resultados['errores'].append(error_msg)

        finally:
            self.cerrar_driver()

        return resultados

    def _scrapear_sitio(self, url: str) -> List[Dict]:
        """
        Scrapea un sitio específico del TCP

        Args:
            url: URL del sitio a scrapear

        Returns:
            Lista de sentencias extraídas
        """
        sentencias_totales = []

        try:
            # Navegar a la página
            logger.info(f"🌐 Navegando a {url}")
            self.driver.get(url)

            # Esperar a que la página cargue
            time.sleep(3)

            # Realizar búsqueda vacía para listar todo
            if not self._realizar_busqueda_vacia():
                logger.warning("⚠️  No se pudo realizar búsqueda vacía, intentando scraping directo")

            # Esperar a que se cargue la tabla de resultados
            time.sleep(3)

            pagina_actual = 1
            tiene_mas_paginas = True

            while tiene_mas_paginas:
                logger.info(f"📄 Procesando página {pagina_actual}")

                # Extraer sentencias de la página actual
                sentencias = self._extraer_sentencias_pagina()

                if sentencias:
                    sentencias_totales.extend(sentencias)
                    logger.info(f"   ✅ {len(sentencias)} sentencias extraídas de página {pagina_actual}")
                else:
                    logger.warning(f"   ⚠️  No se encontraron sentencias en página {pagina_actual}")

                # Intentar ir a la siguiente página
                tiene_mas_paginas = self._ir_siguiente_pagina()

                if tiene_mas_paginas:
                    pagina_actual += 1
                    time.sleep(2)  # Esperar entre páginas
                else:
                    logger.info(f"   ℹ️  No hay más páginas. Total: {pagina_actual} páginas procesadas")

        except Exception as e:
            logger.error(f"❌ Error scrapeando sitio {url}: {e}")

        return sentencias_totales

    def _realizar_busqueda_vacia(self) -> bool:
        """
        Realiza una búsqueda vacía para listar todas las sentencias

        Returns:
            True si la búsqueda fue exitosa, False en caso contrario
        """
        try:
            # Buscar el botón de búsqueda o formulario
            # Intentar varios selectores posibles
            selectores_buscar = [
                "button[type='submit']",
                "input[type='submit']",
                "button.btn-buscar",
                "button.buscar",
                "#btnBuscar",
                "//button[contains(text(), 'Buscar')]",
                "//button[contains(text(), 'BUSCAR')]",
                "//input[@type='submit']"
            ]

            for selector in selectores_buscar:
                try:
                    if selector.startswith('//'):
                        # XPath
                        boton = self.wait.until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                    else:
                        # CSS Selector
                        boton = self.wait.until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )

                    boton.click()
                    logger.info("✅ Búsqueda vacía realizada")
                    time.sleep(2)
                    return True

                except (TimeoutException, NoSuchElementException):
                    continue

            logger.warning("⚠️  No se encontró botón de búsqueda, continuando sin hacer click")
            return False

        except Exception as e:
            logger.error(f"❌ Error en búsqueda vacía: {e}")
            return False

    def _extraer_sentencias_pagina(self) -> List[Dict]:
        """
        Extrae todas las sentencias de la página actual

        Returns:
            Lista de diccionarios con información de sentencias
        """
        sentencias = []

        try:
            # Esperar a que aparezca la tabla
            time.sleep(2)

            # Buscar filas de la tabla con varios selectores posibles
            selectores_filas = [
                "table tbody tr",
                "tr.sentencia",
                "tr[data-id]",
                ".table-row",
                "//table//tbody//tr",
                "//tr[contains(@class, 'sentencia')]"
            ]

            filas = []
            for selector in selectores_filas:
                try:
                    if selector.startswith('//'):
                        filas = self.driver.find_elements(By.XPATH, selector)
                    else:
                        filas = self.driver.find_elements(By.CSS_SELECTOR, selector)

                    if filas:
                        logger.info(f"✅ Encontradas {len(filas)} filas con selector: {selector}")
                        break
                except Exception:
                    continue

            if not filas:
                logger.warning("⚠️  No se encontraron filas en la tabla")
                return sentencias

            # Procesar cada fila
            for i, fila in enumerate(filas, 1):
                try:
                    sentencia = self._extraer_datos_fila(fila, i)
                    if sentencia:
                        sentencias.append(sentencia)

                except Exception as e:
                    logger.error(f"❌ Error procesando fila {i}: {e}")
                    continue

        except Exception as e:
            logger.error(f"❌ Error extrayendo sentencias de página: {e}")

        return sentencias

    def _extraer_datos_fila(self, fila, numero_fila: int) -> Optional[Dict]:
        """
        Extrae datos de una fila de la tabla

        Args:
            fila: Elemento WebDriver de la fila
            numero_fila: Número de fila para logging

        Returns:
            Diccionario con datos de la sentencia o None
        """
        try:
            # Extraer datos visibles en la tabla
            celdas = fila.find_elements(By.TAG_NAME, "td")

            if len(celdas) < 3:
                return None

            sentencia_data = {
                'numero_resolucion': None,
                'tipo_jurisprudencia': None,
                'tipo_resolutivo': None,
                'fecha': None,
                'url_ficha': None,
                'sumilla': None,
                'magistrados': [],
                'area_materia': None,
                'url_pdf': None,
                'archivo_local': None
            }

            # Intentar extraer información de las celdas
            # La estructura puede variar, así que ser flexible
            try:
                # Buscar número de resolución
                if len(celdas) > 0:
                    sentencia_data['numero_resolucion'] = celdas[0].text.strip()

                # Tipo jurisprudencia
                if len(celdas) > 1:
                    sentencia_data['tipo_jurisprudencia'] = celdas[1].text.strip()

                # Tipo resolutivo
                if len(celdas) > 2:
                    sentencia_data['tipo_resolutivo'] = celdas[2].text.strip()

                # Fecha
                if len(celdas) > 3:
                    sentencia_data['fecha'] = celdas[3].text.strip()

            except Exception as e:
                logger.warning(f"⚠️  Error extrayendo datos básicos de fila {numero_fila}: {e}")

            # Buscar enlace "Ver Ficha"
            try:
                enlaces = fila.find_elements(By.TAG_NAME, "a")
                for enlace in enlaces:
                    texto = enlace.text.strip().lower()
                    if 'ficha' in texto or 'ver' in texto or 'detalle' in texto:
                        sentencia_data['url_ficha'] = enlace.get_attribute('href')

                        # Hacer click en "Ver Ficha" para obtener detalles
                        detalles = self._extraer_detalles_ficha(enlace)
                        if detalles:
                            sentencia_data.update(detalles)

                        break

            except Exception as e:
                logger.warning(f"⚠️  Error buscando enlace 'Ver Ficha' en fila {numero_fila}: {e}")

            # Si tenemos al menos número de resolución, considerarlo válido
            if sentencia_data['numero_resolucion']:
                logger.debug(f"   ✅ Fila {numero_fila}: {sentencia_data['numero_resolucion']}")
                return sentencia_data

            return None

        except Exception as e:
            logger.error(f"❌ Error extrayendo datos de fila {numero_fila}: {e}")
            return None

    def _extraer_detalles_ficha(self, enlace_ficha) -> Optional[Dict]:
        """
        Hace click en "Ver Ficha" y extrae los detalles completos

        Args:
            enlace_ficha: Elemento WebDriver del enlace

        Returns:
            Diccionario con detalles de la ficha
        """
        detalles = {}
        ventana_original = self.driver.current_window_handle

        try:
            # Guardar el URL antes de hacer click
            url_ficha = enlace_ficha.get_attribute('href')

            # Click en el enlace (puede abrir nueva ventana o navegar)
            enlace_ficha.click()
            time.sleep(2)

            # Verificar si se abrió una nueva ventana
            ventanas = self.driver.window_handles
            if len(ventanas) > 1:
                # Cambiar a la nueva ventana
                self.driver.switch_to.window(ventanas[-1])

            # Esperar a que cargue la ficha
            time.sleep(2)

            # Extraer información de la ficha
            try:
                # Buscar sumilla
                selectores_sumilla = [
                    "//div[contains(@class, 'sumilla')]",
                    "//div[contains(text(), 'Sumilla')]//following-sibling::div",
                    "//*[contains(text(), 'SUMILLA')]//following-sibling::*",
                    ".sumilla",
                    "#sumilla"
                ]

                for selector in selectores_sumilla:
                    try:
                        if selector.startswith('//'):
                            elemento = self.driver.find_element(By.XPATH, selector)
                        else:
                            elemento = self.driver.find_element(By.CSS_SELECTOR, selector)

                        detalles['sumilla'] = elemento.text.strip()
                        break
                    except NoSuchElementException:
                        continue

                # Buscar magistrados
                selectores_magistrados = [
                    "//div[contains(text(), 'Magistrado')]//following-sibling::div",
                    "//*[contains(text(), 'MAGISTRADO')]//following-sibling::*",
                    ".magistrados",
                    "#magistrados"
                ]

                for selector in selectores_magistrados:
                    try:
                        if selector.startswith('//'):
                            elementos = self.driver.find_elements(By.XPATH, selector)
                        else:
                            elementos = self.driver.find_elements(By.CSS_SELECTOR, selector)

                        magistrados = [elem.text.strip() for elem in elementos if elem.text.strip()]
                        if magistrados:
                            detalles['magistrados'] = magistrados
                            break
                    except NoSuchElementException:
                        continue

                # Buscar área/materia
                selectores_area = [
                    "//div[contains(text(), 'Área')]//following-sibling::div",
                    "//div[contains(text(), 'Materia')]//following-sibling::div",
                    "//*[contains(text(), 'ÁREA')]//following-sibling::*",
                    ".area",
                    ".materia"
                ]

                for selector in selectores_area:
                    try:
                        if selector.startswith('//'):
                            elemento = self.driver.find_element(By.XPATH, selector)
                        else:
                            elemento = self.driver.find_element(By.CSS_SELECTOR, selector)

                        detalles['area_materia'] = elemento.text.strip()
                        break
                    except NoSuchElementException:
                        continue

                # Buscar enlace al PDF
                enlaces_pdf = self.driver.find_elements(By.TAG_NAME, "a")
                for enlace in enlaces_pdf:
                    href = enlace.get_attribute('href')
                    if href and '.pdf' in href.lower():
                        detalles['url_pdf'] = href

                        # Descargar el PDF
                        archivo_descargado = self._descargar_pdf(href)
                        if archivo_descargado:
                            detalles['archivo_local'] = archivo_descargado
                            self.estadisticas['pdfs_descargados'] += 1

                        break

            except Exception as e:
                logger.warning(f"⚠️  Error extrayendo detalles de ficha: {e}")

            # Volver a la ventana original
            if len(ventanas) > 1:
                self.driver.close()
                self.driver.switch_to.window(ventana_original)
            else:
                # Si no se abrió nueva ventana, volver atrás
                self.driver.back()
                time.sleep(1)

        except Exception as e:
            logger.error(f"❌ Error procesando ficha: {e}")

            # Intentar volver a la ventana original
            try:
                if len(self.driver.window_handles) > 1:
                    self.driver.close()
                self.driver.switch_to.window(ventana_original)
            except Exception:
                pass

        return detalles if detalles else None

    def _descargar_pdf(self, url: str) -> Optional[str]:
        """
        Descarga un PDF desde una URL

        Args:
            url: URL del PDF

        Returns:
            Ruta al archivo descargado o None
        """
        try:
            # Intentar con reintentos
            for intento in range(self.retry_attempts):
                try:
                    respuesta = self.session.get(url, timeout=30, stream=True)
                    respuesta.raise_for_status()

                    # Generar nombre de archivo único
                    hash_url = hashlib.md5(url.encode()).hexdigest()[:8]
                    nombre_archivo = f"tcp_sentencia_{hash_url}.pdf"

                    ruta_archivo = self.output_dir / nombre_archivo

                    # Guardar archivo
                    with open(ruta_archivo, 'wb') as f:
                        for chunk in respuesta.iter_content(chunk_size=8192):
                            f.write(chunk)

                    logger.debug(f"   ✅ PDF descargado: {nombre_archivo}")
                    return str(ruta_archivo)

                except requests.RequestException as e:
                    logger.warning(f"   ⚠️  Intento {intento + 1}/{self.retry_attempts} falló: {e}")
                    if intento < self.retry_attempts - 1:
                        time.sleep(2 ** intento)  # Backoff exponencial
                    else:
                        logger.error(f"   ❌ No se pudo descargar PDF: {url}")
                        return None

        except Exception as e:
            logger.error(f"❌ Error descargando PDF {url}: {e}")
            return None

    def _ir_siguiente_pagina(self) -> bool:
        """
        Intenta ir a la siguiente página de resultados

        Returns:
            True si se pudo ir a la siguiente página, False en caso contrario
        """
        try:
            # Buscar botón "Siguiente" o paginación
            selectores_siguiente = [
                "a.next",
                "button.next",
                "a[rel='next']",
                "//a[contains(text(), 'Siguiente')]",
                "//a[contains(text(), 'SIGUIENTE')]",
                "//button[contains(text(), 'Siguiente')]",
                "//a[contains(@class, 'next')]",
                "//li[@class='next']/a",
                ".pagination .next",
                "a[aria-label='Next']",
                "button[aria-label='Next']"
            ]

            for selector in selectores_siguiente:
                try:
                    if selector.startswith('//'):
                        boton_siguiente = self.wait.until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                    else:
                        boton_siguiente = self.wait.until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )

                    # Verificar si el botón está habilitado
                    if 'disabled' in boton_siguiente.get_attribute('class') or '':
                        continue

                    # Scroll al elemento
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", boton_siguiente)
                    time.sleep(0.5)

                    # Click
                    boton_siguiente.click()
                    logger.info("   ➡️  Navegando a siguiente página")
                    time.sleep(2)
                    return True

                except (TimeoutException, NoSuchElementException, StaleElementReferenceException):
                    continue

            logger.info("   ℹ️  No se encontró botón de siguiente página")
            return False

        except Exception as e:
            logger.error(f"❌ Error navegando a siguiente página: {e}")
            return False

    def obtener_estadisticas(self) -> Dict:
        """
        Retorna estadísticas del scraping

        Returns:
            Diccionario con estadísticas
        """
        return self.estadisticas

    def exportar_resultados(self, sentencias: List[Dict], formato: str = 'json') -> str:
        """
        Exporta los resultados a un archivo

        Args:
            sentencias: Lista de sentencias extraídas
            formato: Formato de exportación ('json' o 'csv')

        Returns:
            Ruta al archivo exportado
        """
        import json
        import csv

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if formato == 'json':
            archivo = self.output_dir / f"tcp_sentencias_{timestamp}.json"
            with open(archivo, 'w', encoding='utf-8') as f:
                json.dump(sentencias, f, ensure_ascii=False, indent=2)

        elif formato == 'csv':
            archivo = self.output_dir / f"tcp_sentencias_{timestamp}.csv"

            if sentencias:
                campos = list(sentencias[0].keys())

                with open(archivo, 'w', encoding='utf-8', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=campos)
                    writer.writeheader()

                    for sentencia in sentencias:
                        # Convertir listas a strings
                        row = sentencia.copy()
                        for key, value in row.items():
                            if isinstance(value, list):
                                row[key] = ', '.join(str(v) for v in value)
                        writer.writerow(row)

        logger.info(f"✅ Resultados exportados a: {archivo}")
        return str(archivo)


def main():
    """Función principal para ejecutar el scraper"""
    logger.info("🦉 TCP Jurisprudencia Scraper - Iniciando...")

    # Crear scraper
    scraper = TCPJurisprudenciaScraper(
        output_dir="data/raw/tcp_jurisprudencia",
        headless=True,
        timeout=30
    )

    # Ejecutar scraping
    resultados = scraper.scrapear_todo()

    # Mostrar resultados
    logger.info("\n" + "="*60)
    logger.info("📊 RESUMEN DEL SCRAPING")
    logger.info("="*60)
    logger.info(f"✅ Sentencias procesadas: {resultados['total_procesadas']}")
    logger.info(f"📄 PDFs descargados: {scraper.estadisticas['pdfs_descargados']}")
    logger.info(f"❌ Errores: {len(resultados['errores'])}")

    # Exportar resultados
    if resultados['sentencias']:
        archivo_json = scraper.exportar_resultados(resultados['sentencias'], formato='json')
        archivo_csv = scraper.exportar_resultados(resultados['sentencias'], formato='csv')

        logger.info(f"\n📁 Archivos generados:")
        logger.info(f"   - JSON: {archivo_json}")
        logger.info(f"   - CSV: {archivo_csv}")

    logger.info("\n✅ Scraping completado")


if __name__ == "__main__":
    main()
