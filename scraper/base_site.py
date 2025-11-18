"""
Clase base para scrapers de sitios gubernamentales.
Proporciona la estructura común que deben implementar todos los scrapers específicos.
"""

import json
import os
import time
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException


class BaseSiteScraper(ABC):
    """
    Clase base abstracta para todos los scrapers de sitios gubernamentales.

    Cada sitio específico debe heredar de esta clase e implementar los métodos abstractos.
    """

    def __init__(self, config_path: str = "config/sites.json", site_id: str = None):
        """
        Inicializa el scraper con la configuración del sitio.

        Args:
            config_path: Ruta al archivo de configuración JSON
            site_id: Identificador del sitio en el archivo de configuración
        """
        self.site_id = site_id
        self.config = self._load_config(config_path)
        self.site_config = self.config.get('sites', {}).get(site_id, {})

        if not self.site_config:
            raise ValueError(f"No se encontró configuración para el sitio: {site_id}")

        # Configuración del sitio
        self.nombre = self.site_config.get('nombre', '')
        self.url_listado = self.site_config.get('url_listado', '')
        self.selectores = self.site_config.get('selectores_css', {})
        self.tipo_paginacion = self.site_config.get('tipo_paginacion', 'simple')
        self.requiere_selenium = self.site_config.get('requiere_selenium', False)
        self.reglas_extraccion = self.site_config.get('reglas_extraccion', {})
        self.rate_limit = self.site_config.get('rate_limit', {})
        self.output_folder = self.site_config.get('output_folder', f'outputs/{site_id}')

        # Crear carpetas de salida
        self._crear_carpetas_salida()

        # Configurar logging
        self.logger = self._setup_logger()

        # Estadísticas
        self.stats = {
            'documentos_encontrados': 0,
            'documentos_descargados': 0,
            'articulos_extraidos': 0,
            'errores': 0,
            'inicio': datetime.now()
        }

        # Driver de Selenium (si se requiere)
        self.driver = None

        # Session de requests
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def _load_config(self, config_path: str) -> Dict:
        """Carga el archivo de configuración JSON."""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"No se encontró el archivo de configuración: {config_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Error al parsear el archivo de configuración: {e}")

    def _crear_carpetas_salida(self):
        """Crea las carpetas necesarias para guardar los outputs."""
        folders = [
            self.output_folder,
            f"{self.output_folder}/pdfs",
            f"{self.output_folder}/csv",
            f"{self.output_folder}/json",
            "logs"
        ]
        for folder in folders:
            Path(folder).mkdir(parents=True, exist_ok=True)

    def _setup_logger(self) -> logging.Logger:
        """Configura el sistema de logging."""
        logger = logging.getLogger(f"{self.site_id}_scraper")
        logger.setLevel(logging.INFO)

        # Evitar duplicados
        if logger.handlers:
            logger.handlers.clear()

        # Handler para archivo
        fecha = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = f"logs/{self.site_id}_{fecha}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)

        # Handler para consola
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # Formato
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        return logger

    def _init_selenium(self):
        """Inicializa el driver de Selenium si es necesario."""
        if not self.requiere_selenium or self.driver:
            return

        selenium_opts = self.site_config.get('selenium_options', {})

        options = Options()
        if selenium_opts.get('headless', True):
            options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')

        try:
            self.driver = webdriver.Chrome(options=options)
            self.logger.info("Selenium WebDriver inicializado correctamente")
        except Exception as e:
            self.logger.error(f"Error al inicializar Selenium: {e}")
            raise

    def _close_selenium(self):
        """Cierra el driver de Selenium."""
        if self.driver:
            self.driver.quit()
            self.driver = None
            self.logger.info("Selenium WebDriver cerrado")

    def _wait_rate_limit(self):
        """Espera según el rate limit configurado."""
        delay = self.rate_limit.get('delay_entre_requests', 3)
        time.sleep(delay)

    def _normalizar_fecha(self, fecha_str: str) -> Optional[str]:
        """
        Normaliza fechas a formato ISO (YYYY-MM-DD).
        Debe ser sobrescrito por las clases hijas si tienen formato específico.
        """
        return fecha_str

    @abstractmethod
    def fetch_listing(self, limite: int = None) -> List[Dict[str, Any]]:
        """
        Obtiene el listado de documentos del sitio.

        Args:
            limite: Número máximo de documentos a obtener

        Returns:
            Lista de diccionarios con metadata de documentos
        """
        pass

    @abstractmethod
    def extract_links(self, html_content: str) -> List[str]:
        """
        Extrae los enlaces a documentos del HTML.

        Args:
            html_content: Contenido HTML de la página

        Returns:
            Lista de URLs de documentos
        """
        pass

    @abstractmethod
    def download_document(self, url: str, metadata: Dict[str, Any]) -> Optional[str]:
        """
        Descarga un documento específico.

        Args:
            url: URL del documento
            metadata: Metadata asociada al documento

        Returns:
            Ruta local del archivo descargado o None si falla
        """
        pass

    @abstractmethod
    def normalize_metadata(self, raw_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normaliza la metadata extraída del sitio.

        Args:
            raw_metadata: Metadata en formato crudo del sitio

        Returns:
            Metadata normalizada con campos estándar
        """
        pass

    def extract_text_from_pdf(self, pdf_path: str) -> Optional[str]:
        """
        Extrae texto de un archivo PDF.
        Puede ser sobrescrito por las clases hijas.

        Args:
            pdf_path: Ruta al archivo PDF

        Returns:
            Texto extraído o None si falla
        """
        try:
            import PyPDF2
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ''
                for page in reader.pages:
                    text += page.extract_text() + '\n'
                return text
        except Exception as e:
            self.logger.error(f"Error al extraer texto del PDF {pdf_path}: {e}")
            return None

    def extract_articles(self, text: str) -> List[Dict[str, str]]:
        """
        Extrae artículos del texto usando el patrón configurado.

        Args:
            text: Texto del documento

        Returns:
            Lista de artículos encontrados
        """
        import re

        patron = self.reglas_extraccion.get('patron_articulos', r'Art[ií]culo\s+\d+[°º]?')

        try:
            articulos = []
            matches = list(re.finditer(patron, text, re.IGNORECASE))

            for i, match in enumerate(matches):
                inicio = match.start()
                fin = matches[i + 1].start() if i + 1 < len(matches) else len(text)

                articulo_texto = text[inicio:fin].strip()
                articulos.append({
                    'numero': match.group(),
                    'texto': articulo_texto
                })

            self.stats['articulos_extraidos'] += len(articulos)
            return articulos

        except Exception as e:
            self.logger.error(f"Error al extraer artículos: {e}")
            return []

    def save_to_csv(self, datos: List[Dict[str, Any]], filename: str = None):
        """
        Guarda datos en formato CSV.

        Args:
            datos: Lista de diccionarios con los datos
            filename: Nombre del archivo (opcional)
        """
        import csv

        if not datos:
            self.logger.warning("No hay datos para guardar en CSV")
            return

        if not filename:
            fecha = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{self.output_folder}/csv/{self.site_id}_{fecha}.csv"

        try:
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=datos[0].keys())
                writer.writeheader()
                writer.writerows(datos)

            self.logger.info(f"Datos guardados en CSV: {filename}")
        except Exception as e:
            self.logger.error(f"Error al guardar CSV: {e}")
            self.stats['errores'] += 1

    def save_to_json(self, datos: List[Dict[str, Any]], filename: str = None):
        """
        Guarda datos en formato JSON.

        Args:
            datos: Lista de diccionarios con los datos
            filename: Nombre del archivo (opcional)
        """
        if not filename:
            fecha = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{self.output_folder}/json/{self.site_id}_{fecha}.json"

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(datos, f, ensure_ascii=False, indent=2)

            self.logger.info(f"Datos guardados en JSON: {filename}")
        except Exception as e:
            self.logger.error(f"Error al guardar JSON: {e}")
            self.stats['errores'] += 1

    def log_stats(self):
        """Registra las estadísticas del scraping."""
        duracion = datetime.now() - self.stats['inicio']

        self.logger.info("=" * 60)
        self.logger.info(f"ESTADÍSTICAS DE SCRAPING - {self.nombre}")
        self.logger.info("=" * 60)
        self.logger.info(f"Documentos encontrados: {self.stats['documentos_encontrados']}")
        self.logger.info(f"Documentos descargados: {self.stats['documentos_descargados']}")
        self.logger.info(f"Artículos extraídos: {self.stats['articulos_extraidos']}")
        self.logger.info(f"Errores: {self.stats['errores']}")
        self.logger.info(f"Duración: {duracion}")
        self.logger.info("=" * 60)

    def run(self, limite: int = None, reprocesar: bool = False):
        """
        Ejecuta el proceso completo de scraping.

        Args:
            limite: Número máximo de documentos a procesar
            reprocesar: Si True, reprocesa documentos ya descargados
        """
        try:
            self.logger.info(f"Iniciando scraping de {self.nombre}")
            self.logger.info(f"URL: {self.url_listado}")
            self.logger.info(f"Límite: {limite if limite else 'Sin límite'}")

            # Inicializar Selenium si es necesario
            if self.requiere_selenium:
                self._init_selenium()

            # Obtener listado de documentos
            documentos = self.fetch_listing(limite=limite)
            self.stats['documentos_encontrados'] = len(documentos)

            self.logger.info(f"Encontrados {len(documentos)} documentos")

            # Procesar cada documento
            resultados = []
            for i, doc in enumerate(documentos, 1):
                try:
                    self.logger.info(f"Procesando documento {i}/{len(documentos)}")

                    # Normalizar metadata
                    metadata = self.normalize_metadata(doc)

                    # Descargar documento
                    if 'url_pdf' in metadata or 'url_documento' in metadata:
                        url = metadata.get('url_pdf') or metadata.get('url_documento')
                        archivo = self.download_document(url, metadata)

                        if archivo:
                            metadata['archivo_local'] = archivo
                            self.stats['documentos_descargados'] += 1

                    resultados.append(metadata)

                    # Respetar rate limit
                    self._wait_rate_limit()

                except Exception as e:
                    self.logger.error(f"Error procesando documento {i}: {e}")
                    self.stats['errores'] += 1
                    continue

            # Guardar resultados
            if resultados:
                self.save_to_csv(resultados)
                self.save_to_json(resultados)

            # Mostrar estadísticas
            self.log_stats()

        except Exception as e:
            self.logger.error(f"Error en el proceso de scraping: {e}")
            self.stats['errores'] += 1
            raise

        finally:
            # Cerrar Selenium
            if self.requiere_selenium:
                self._close_selenium()

    def __enter__(self):
        """Context manager entry."""
        if self.requiere_selenium:
            self._init_selenium()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self.requiere_selenium:
            self._close_selenium()
