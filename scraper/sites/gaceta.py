"""
Scraper específico para la Gaceta Oficial de Bolivia.
Implementa la lógica específica para extraer información de la Gaceta.
"""

import re
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import requests

from ..base_site import BaseSiteScraper


class GacetaScraper(BaseSiteScraper):
    """
    Scraper para la Gaceta Oficial de Bolivia.
    Hereda de BaseSiteScraper e implementa métodos específicos para este sitio.
    """

    def __init__(self, config_path: str = "config/sites.json"):
        """Inicializa el scraper de la Gaceta."""
        super().__init__(config_path=config_path, site_id='gaceta')
        self.logger.info("GacetaScraper inicializado")

    def fetch_listing(self, limite: int = None) -> List[Dict[str, Any]]:
        """
        Obtiene el listado de gacetas oficiales.

        Args:
            limite: Número máximo de documentos a obtener

        Returns:
            Lista de diccionarios con metadata de las gacetas
        """
        documentos = []

        try:
            if self.requiere_selenium:
                documentos = self._fetch_with_selenium(limite)
            else:
                documentos = self._fetch_with_requests(limite)

            self.logger.info(f"Se obtuvieron {len(documentos)} documentos del listado")
            return documentos

        except Exception as e:
            self.logger.error(f"Error al obtener el listado: {e}")
            self.stats['errores'] += 1
            return []

    def _fetch_with_selenium(self, limite: int = None) -> List[Dict[str, Any]]:
        """Obtiene el listado usando Selenium (para sitios con JavaScript)."""
        documentos = []

        try:
            self.driver.get(self.url_listado)
            self.logger.info(f"Navegando a: {self.url_listado}")

            # Esperar a que cargue el contenido
            wait_time = self.site_config.get('selenium_options', {}).get('wait_time', 5)
            WebDriverWait(self.driver, wait_time).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            # Si usa scroll infinito
            if self.tipo_paginacion == 'scroll_infinito':
                documentos = self._scroll_infinito(limite)
            # Si usa paginación numérica
            elif self.tipo_paginacion == 'paginado_numerico':
                documentos = self._paginacion_numerica(limite)
            # Si tiene botón siguiente
            elif self.tipo_paginacion == 'boton_siguiente':
                documentos = self._boton_siguiente(limite)
            else:
                # Extraer de la página actual
                html = self.driver.page_source
                documentos = self._parse_listing_html(html, limite)

        except TimeoutException:
            self.logger.error("Timeout esperando que cargue la página")
            self.stats['errores'] += 1
        except Exception as e:
            self.logger.error(f"Error en fetch con Selenium: {e}")
            self.stats['errores'] += 1

        return documentos

    def _scroll_infinito(self, limite: int = None) -> List[Dict[str, Any]]:
        """Maneja sitios con scroll infinito."""
        documentos = []
        scroll_pause = self.site_config.get('selenium_options', {}).get('scroll_pause', 2)

        last_height = self.driver.execute_script("return document.body.scrollHeight")

        while True:
            # Scroll hacia abajo
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            # Esperar a que cargue nuevo contenido
            import time
            time.sleep(scroll_pause)

            # Parsear documentos actuales
            html = self.driver.page_source
            docs_actuales = self._parse_listing_html(html)

            # Añadir solo documentos nuevos
            for doc in docs_actuales:
                if doc not in documentos:
                    documentos.append(doc)

            # Verificar si se alcanzó el límite
            if limite and len(documentos) >= limite:
                documentos = documentos[:limite]
                break

            # Calcular nueva altura
            new_height = self.driver.execute_script("return document.body.scrollHeight")

            # Salir si no hay más contenido
            if new_height == last_height:
                break

            last_height = new_height

        return documentos

    def _paginacion_numerica(self, limite: int = None) -> List[Dict[str, Any]]:
        """Maneja sitios con paginación numérica."""
        documentos = []
        pagina = 1

        while True:
            self.logger.info(f"Procesando página {pagina}")

            # Parsear documentos de la página actual
            html = self.driver.page_source
            docs_pagina = self._parse_listing_html(html)
            documentos.extend(docs_pagina)

            # Verificar si se alcanzó el límite
            if limite and len(documentos) >= limite:
                documentos = documentos[:limite]
                break

            # Buscar botón de siguiente página
            try:
                next_button = self.driver.find_element(By.CSS_SELECTOR,
                    "a.siguiente, a.next, button.siguiente, button.next, a[rel='next']")
                next_button.click()

                import time
                time.sleep(2)  # Esperar a que cargue
                pagina += 1

            except:
                self.logger.info("No hay más páginas disponibles")
                break

        return documentos

    def _boton_siguiente(self, limite: int = None) -> List[Dict[str, Any]]:
        """Maneja sitios con botón 'Siguiente'."""
        return self._paginacion_numerica(limite)

    def _fetch_with_requests(self, limite: int = None) -> List[Dict[str, Any]]:
        """Obtiene el listado usando requests (para sitios estáticos)."""
        try:
            response = self.session.get(self.url_listado, timeout=30)
            response.raise_for_status()

            documentos = self._parse_listing_html(response.text, limite)
            return documentos

        except requests.RequestException as e:
            self.logger.error(f"Error en la petición HTTP: {e}")
            self.stats['errores'] += 1
            return []

    def _parse_listing_html(self, html: str, limite: int = None) -> List[Dict[str, Any]]:
        """
        Parsea el HTML del listado y extrae información de los documentos.

        Args:
            html: HTML de la página
            limite: Límite de documentos a extraer

        Returns:
            Lista de documentos con metadata
        """
        documentos = []
        soup = BeautifulSoup(html, 'html.parser')

        # Buscar filas de documentos usando los selectores configurados
        selector_fila = self.selectores.get('fila_documento', 'tr.documento')

        filas = soup.select(selector_fila)

        if not filas:
            # Intentar con selectores alternativos comunes
            filas = soup.select('tr') or soup.select('div.item') or soup.select('article')

        self.logger.info(f"Encontradas {len(filas)} filas en el HTML")

        for i, fila in enumerate(filas):
            if limite and i >= limite:
                break

            try:
                doc = self._parse_documento_fila(fila)
                if doc:
                    documentos.append(doc)

            except Exception as e:
                self.logger.error(f"Error parseando fila {i}: {e}")
                continue

        return documentos

    def _parse_documento_fila(self, fila) -> Optional[Dict[str, Any]]:
        """
        Extrae información de una fila individual del listado.

        Args:
            fila: Elemento BeautifulSoup de la fila

        Returns:
            Diccionario con metadata del documento o None
        """
        try:
            # Extraer link al PDF
            link_pdf = fila.select_one(self.selectores.get('link_pdf', 'a[href$=".pdf"]'))
            if not link_pdf:
                # Intentar buscar cualquier enlace con PDF
                link_pdf = fila.find('a', href=re.compile(r'\.pdf', re.I))

            if not link_pdf:
                return None

            url_pdf = link_pdf.get('href', '')
            if not url_pdf.startswith('http'):
                url_pdf = urljoin(self.url_listado, url_pdf)

            # Extraer otros campos
            titulo = self._extract_text(fila, self.selectores.get('titulo', '.titulo'))
            fecha = self._extract_text(fila, self.selectores.get('fecha', '.fecha'))
            numero_gaceta = self._extract_text(fila, self.selectores.get('numero_gaceta', '.numero'))
            tipo_norma = self._extract_text(fila, self.selectores.get('tipo_norma', '.tipo'))

            return {
                'url_pdf': url_pdf,
                'titulo': titulo,
                'fecha_publicacion': fecha,
                'numero_gaceta': numero_gaceta,
                'tipo_norma': tipo_norma,
                'fecha_scraping': datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error extrayendo datos de la fila: {e}")
            return None

    def _extract_text(self, element, selector: str) -> str:
        """Extrae texto de un elemento usando un selector CSS."""
        try:
            found = element.select_one(selector)
            return found.get_text(strip=True) if found else ''
        except:
            return ''

    def extract_links(self, html_content: str) -> List[str]:
        """
        Extrae enlaces a PDFs del HTML.

        Args:
            html_content: Contenido HTML

        Returns:
            Lista de URLs de PDFs
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        links = []

        # Buscar todos los enlaces a PDFs
        pdf_links = soup.find_all('a', href=re.compile(r'\.pdf', re.I))

        for link in pdf_links:
            url = link.get('href', '')
            if not url.startswith('http'):
                url = urljoin(self.url_listado, url)
            links.append(url)

        return links

    def download_document(self, url: str, metadata: Dict[str, Any]) -> Optional[str]:
        """
        Descarga un documento PDF.

        Args:
            url: URL del PDF
            metadata: Metadata del documento

        Returns:
            Ruta local del archivo descargado
        """
        try:
            # Generar nombre de archivo único
            numero = metadata.get('numero_gaceta', '').replace('/', '-')
            fecha = metadata.get('fecha_publicacion', '').replace('/', '-')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

            filename = f"gaceta_{numero}_{fecha}_{timestamp}.pdf".replace(' ', '_')
            filepath = os.path.join(self.output_folder, 'pdfs', filename)

            # Descargar el archivo
            self.logger.info(f"Descargando: {url}")
            response = self.session.get(url, timeout=60, stream=True)
            response.raise_for_status()

            # Guardar el archivo
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            self.logger.info(f"Descargado: {filepath}")

            # Opcionalmente extraer texto y artículos
            if self.reglas_extraccion.get('extraer_texto', False):
                texto = self.extract_text_from_pdf(filepath)
                if texto and self.reglas_extraccion.get('extraer_articulos', False):
                    articulos = self.extract_articles(texto)
                    self.logger.info(f"Extraídos {len(articulos)} artículos")

            return filepath

        except requests.RequestException as e:
            self.logger.error(f"Error descargando {url}: {e}")
            self.stats['errores'] += 1
            return None
        except Exception as e:
            self.logger.error(f"Error guardando archivo: {e}")
            self.stats['errores'] += 1
            return None

    def normalize_metadata(self, raw_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normaliza la metadata de la Gaceta a un formato estándar.

        Args:
            raw_metadata: Metadata en formato crudo

        Returns:
            Metadata normalizada
        """
        normalized = {
            'sitio': self.site_id,
            'nombre_sitio': self.nombre,
            'tipo': self.site_config.get('tipo', 'gaceta'),
            'fecha_scraping': datetime.now().isoformat()
        }

        # Mapear campos específicos de la Gaceta
        campo_mapping = {
            'titulo': 'titulo',
            'fecha_publicacion': 'fecha_publicacion',
            'numero_gaceta': 'numero_gaceta',
            'tipo_norma': 'tipo_norma',
            'url_pdf': 'url_pdf',
            'archivo_local': 'archivo_local'
        }

        for raw_key, norm_key in campo_mapping.items():
            if raw_key in raw_metadata:
                normalized[norm_key] = raw_metadata[raw_key]

        # Normalizar fecha
        if 'fecha_publicacion' in normalized:
            normalized['fecha_publicacion_iso'] = self._normalizar_fecha(
                normalized['fecha_publicacion']
            )

        return normalized

    def _normalizar_fecha(self, fecha_str: str) -> Optional[str]:
        """
        Normaliza fechas de la Gaceta al formato ISO.

        Formatos comunes en Bolivia:
        - DD/MM/YYYY
        - DD-MM-YYYY
        - DD de Mes de YYYY
        """
        if not fecha_str:
            return None

        try:
            # Intentar formato DD/MM/YYYY
            if '/' in fecha_str:
                parts = fecha_str.split('/')
                if len(parts) == 3:
                    return f"{parts[2]}-{parts[1].zfill(2)}-{parts[0].zfill(2)}"

            # Intentar formato DD-MM-YYYY
            if '-' in fecha_str and len(fecha_str.split('-')) == 3:
                parts = fecha_str.split('-')
                if len(parts[0]) <= 2:  # DD-MM-YYYY
                    return f"{parts[2]}-{parts[1].zfill(2)}-{parts[0].zfill(2)}"

            # Intentar parsear con dateutil si está disponible
            from dateutil import parser
            dt = parser.parse(fecha_str, dayfirst=True)
            return dt.strftime('%Y-%m-%d')

        except Exception as e:
            self.logger.warning(f"No se pudo normalizar fecha '{fecha_str}': {e}")
            return fecha_str
