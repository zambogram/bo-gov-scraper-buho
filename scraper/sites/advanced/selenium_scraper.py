"""
Scraper base con Selenium para sitios gubernamentales que requieren JavaScript
"""
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
from typing import List, Optional
from pathlib import Path
import logging

from ..base_scraper import BaseScraper


class SeleniumScraper(BaseScraper):
    """Scraper base para sitios gubernamentales que usan JavaScript"""

    def __init__(self, site_id: str):
        super().__init__(site_id)
        self.driver = None

    def _init_driver(self):
        """Inicializar Chrome headless"""
        if self.driver:
            return

        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

        # Deshabilitar imágenes para velocidad
        prefs = {'profile.managed_default_content_settings.images': 2}
        chrome_options.add_experimental_option('prefs', prefs)

        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.set_page_load_timeout(30)
            logger.info("✅ Selenium inicializado")
        except Exception as e:
            logger.error(f"❌ Error iniciando Selenium: {e}")
            raise

    def _close_driver(self):
        """Cerrar driver de Selenium"""
        if self.driver:
            self.driver.quit()
            self.driver = None

    def _get_page(self, url: str, wait_selector: Optional[str] = None, wait_time: int = 10) -> BeautifulSoup:
        """Cargar página con JavaScript y retornar BeautifulSoup"""
        self._init_driver()

        try:
            self.driver.get(url)

            if wait_selector:
                WebDriverWait(self.driver, wait_time).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, wait_selector))
                )
            else:
                time.sleep(2)

            html = self.driver.page_source
            return BeautifulSoup(html, 'html.parser')

        except Exception as e:
            logger.error(f"Error cargando {url}: {e}")
            raise

    def __del__(self):
        """Limpiar recursos al destruir el objeto"""
        self._close_driver()


# Configurar logger
logger = logging.getLogger(__name__)
