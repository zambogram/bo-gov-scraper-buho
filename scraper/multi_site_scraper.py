"""
Scraper Multi-Sitio para Páginas del Gobierno Boliviano
Scrapea múltiples sitios gubernamentales simultáneamente con procesamiento completo
"""

import requests
from bs4 import BeautifulSoup
import yaml
import time
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import hashlib


class MultiSiteScraper:
    """Scraper inteligente para múltiples sitios gubernamentales"""

    def __init__(self, config_path: str = "config/sites_config.yaml",
                 output_dir: str = "data/raw"):
        """
        Inicializa el scraper multi-sitio

        Args:
            config_path: Ruta al archivo de configuración
            output_dir: Directorio para archivos descargados
        """
        self.config_path = Path(config_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.config = self._cargar_configuracion()
        self.session = requests.Session()
        self._configurar_session()

        self.estadisticas = {
            'sitios_scrapeados': 0,
            'documentos_descargados': 0,
            'errores': []
        }

    def _cargar_configuracion(self) -> Dict:
        """Carga la configuración desde el archivo YAML"""
        if self.config_path.exists():
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        else:
            print(f"⚠️  Archivo de configuración no encontrado: {self.config_path}")
            return {'sites': [], 'scraping_settings': {}}

    def _configurar_session(self):
        """Configura la sesión HTTP con headers y parámetros"""
        settings = self.config.get('scraping_settings', {})

        self.session.headers.update({
            'User-Agent': settings.get('user_agent',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })

        self.timeout = settings.get('timeout', 30)
        self.retry_attempts = settings.get('retry_attempts', 3)
        self.delay = settings.get('delay_between_requests', 2)

    def scrapear_todos_los_sitios(self, max_workers: int = 5) -> Dict:
        """
        Scrapea todos los sitios configurados de manera concurrente

        Args:
            max_workers: Número de hilos concurrentes

        Returns:
            Diccionario con resultados del scraping
        """
        sitios_habilitados = [s for s in self.config.get('sites', [])
                             if s.get('enabled', True)]

        print(f"🚀 Iniciando scraping de {len(sitios_habilitados)} sitios...")

        resultados = {
            'exitosos': [],
            'fallidos': [],
            'total_documentos': 0
        }

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futuros = {
                executor.submit(self.scrapear_sitio, sitio): sitio
                for sitio in sitios_habilitados
            }

            for futuro in tqdm(as_completed(futuros), total=len(futuros),
                             desc="Scraping sitios"):
                sitio = futuros[futuro]
                try:
                    resultado = futuro.result()
                    if resultado['exito']:
                        resultados['exitosos'].append(resultado)
                        resultados['total_documentos'] += resultado['documentos_encontrados']
                    else:
                        resultados['fallidos'].append(resultado)

                except Exception as e:
                    print(f"❌ Error procesando {sitio['name']}: {e}")
                    resultados['fallidos'].append({
                        'sitio': sitio['name'],
                        'error': str(e)
                    })

        return resultados

    def scrapear_sitio(self, sitio_config: Dict) -> Dict:
        """
        Scrapea un sitio individual

        Args:
            sitio_config: Configuración del sitio

        Returns:
            Diccionario con resultados del scraping
        """
        nombre_sitio = sitio_config['name']
        url_base = sitio_config['url']

        print(f"\n📡 Scrapeando: {nombre_sitio}")

        resultado = {
            'sitio': nombre_sitio,
            'url': url_base,
            'exito': False,
            'documentos_encontrados': 0,
            'documentos_descargados': 0,
            'enlaces_documentos': [],
            'errores': []
        }

        try:
            # Crear directorio para este sitio
            sitio_dir = self.output_dir / self._limpiar_nombre(nombre_sitio)
            sitio_dir.mkdir(parents=True, exist_ok=True)

            # Obtener la configuración de scraping
            scraping_cfg = sitio_config.get('scraping_config', {})

            # Construir URL de la página de listado
            list_page = scraping_cfg.get('list_page', '')
            url_listado = f"{url_base}{list_page}" if list_page else url_base

            # Obtener la página
            html = self._obtener_pagina(url_listado)
            if not html:
                resultado['errores'].append("No se pudo obtener la página principal")
                return resultado

            # Parsear HTML
            soup = BeautifulSoup(html, 'lxml')

            # Buscar enlaces a documentos legales
            enlaces = self._extraer_enlaces_documentos(soup, scraping_cfg, url_base)

            resultado['documentos_encontrados'] = len(enlaces)
            resultado['enlaces_documentos'] = enlaces

            print(f"   📄 {len(enlaces)} documentos encontrados")

            # Descargar documentos
            for enlace in tqdm(enlaces[:50], desc=f"   Descargando de {nombre_sitio}"):
                try:
                    archivo_descargado = self._descargar_documento(
                        enlace['url'],
                        sitio_dir,
                        prefijo=enlace.get('numero_ley', 'doc')
                    )

                    if archivo_descargado:
                        enlace['archivo_local'] = archivo_descargado
                        resultado['documentos_descargados'] += 1

                    time.sleep(self.delay)  # Delay entre descargas

                except Exception as e:
                    resultado['errores'].append(f"Error descargando {enlace['url']}: {e}")

            resultado['exito'] = resultado['documentos_descargados'] > 0

        except Exception as e:
            resultado['errores'].append(f"Error general: {str(e)}")
            print(f"   ❌ Error en {nombre_sitio}: {e}")

        return resultado

    def _obtener_pagina(self, url: str) -> Optional[str]:
        """Obtiene el HTML de una página con reintentos"""
        for intento in range(self.retry_attempts):
            try:
                respuesta = self.session.get(url, timeout=self.timeout)
                respuesta.raise_for_status()
                return respuesta.text

            except requests.RequestException as e:
                print(f"   ⚠️  Intento {intento + 1}/{self.retry_attempts} falló: {e}")
                if intento < self.retry_attempts - 1:
                    time.sleep(2 ** intento)  # Backoff exponencial
                else:
                    print(f"   ❌ No se pudo obtener: {url}")
                    return None

        return None

    def _extraer_enlaces_documentos(self, soup: BeautifulSoup,
                                   config: Dict, url_base: str) -> List[Dict]:
        """
        Extrae enlaces a documentos legales de la página

        Args:
            soup: BeautifulSoup object
            config: Configuración de selectores
            url_base: URL base del sitio

        Returns:
            Lista de documentos encontrados
        """
        documentos = []

        try:
            # Buscar enlaces a PDFs directamente
            enlaces_pdf = soup.find_all('a', href=lambda href: href and
                                       ('.pdf' in href.lower() or
                                        '.doc' in href.lower() or
                                        '.docx' in href.lower()))

            for enlace in enlaces_pdf:
                url = enlace.get('href', '')

                # Convertir a URL absoluta
                if url.startswith('http'):
                    url_completa = url
                elif url.startswith('/'):
                    url_completa = f"{url_base}{url}"
                else:
                    url_completa = f"{url_base}/{url}"

                # Intentar extraer información del enlace
                texto_enlace = enlace.get_text(strip=True)
                numero_ley = self._extraer_numero_ley_de_texto(texto_enlace)

                documento = {
                    'url': url_completa,
                    'titulo': texto_enlace[:200] if texto_enlace else 'Sin título',
                    'numero_ley': numero_ley,
                    'tipo': self._detectar_tipo_archivo(url_completa)
                }

                documentos.append(documento)

            # Si hay selectores específicos configurados, usarlos
            if config.get('selectors'):
                documentos_cfg = self._extraer_con_selectores(soup, config['selectors'], url_base)
                documentos.extend(documentos_cfg)

        except Exception as e:
            print(f"   ⚠️  Error extrayendo enlaces: {e}")

        # Eliminar duplicados
        urls_unicas = set()
        documentos_unicos = []

        for doc in documentos:
            if doc['url'] not in urls_unicas:
                urls_unicas.add(doc['url'])
                documentos_unicos.append(doc)

        return documentos_unicos

    def _extraer_con_selectores(self, soup: BeautifulSoup,
                               selectores: Dict, url_base: str) -> List[Dict]:
        """Extrae documentos usando selectores CSS personalizados"""
        documentos = []

        try:
            # Selector para enlaces de leyes
            law_links = selectores.get('law_links', '')
            if law_links:
                elementos = soup.select(law_links)

                for elemento in elementos:
                    url = elemento.get('href', '')
                    if not url:
                        continue

                    # Convertir a URL absoluta
                    if url.startswith('http'):
                        url_completa = url
                    elif url.startswith('/'):
                        url_completa = f"{url_base}{url}"
                    else:
                        url_completa = f"{url_base}/{url}"

                    documento = {
                        'url': url_completa,
                        'titulo': elemento.get_text(strip=True),
                        'numero_ley': None,
                        'tipo': self._detectar_tipo_archivo(url_completa)
                    }

                    documentos.append(documento)

        except Exception as e:
            print(f"   ⚠️  Error con selectores: {e}")

        return documentos

    def _descargar_documento(self, url: str, directorio: Path,
                            prefijo: str = "documento") -> Optional[str]:
        """
        Descarga un documento y lo guarda localmente

        Args:
            url: URL del documento
            directorio: Directorio de destino
            prefijo: Prefijo para el nombre del archivo

        Returns:
            Ruta al archivo descargado o None si falló
        """
        try:
            respuesta = self.session.get(url, timeout=self.timeout, stream=True)
            respuesta.raise_for_status()

            # Determinar extensión
            extension = self._detectar_tipo_archivo(url)

            # Generar nombre de archivo único
            hash_url = hashlib.md5(url.encode()).hexdigest()[:8]
            prefijo_limpio = self._limpiar_nombre(prefijo)
            nombre_archivo = f"{prefijo_limpio}_{hash_url}.{extension}"

            ruta_archivo = directorio / nombre_archivo

            # Guardar archivo
            with open(ruta_archivo, 'wb') as f:
                for chunk in respuesta.iter_content(chunk_size=8192):
                    f.write(chunk)

            return str(ruta_archivo)

        except Exception as e:
            print(f"   ⚠️  Error descargando {url}: {e}")
            return None

    def _extraer_numero_ley_de_texto(self, texto: str) -> Optional[str]:
        """Extrae el número de ley de un texto"""
        import re

        patrones = [
            r'Ley\s+N?[°º]?\s*(\d+)',
            r'D\.?S\.?\s+N?[°º]?\s*(\d+)',
            r'Resolución\s+N?[°º]?\s*(\d+)',
        ]

        for patron in patrones:
            match = re.search(patron, texto, re.IGNORECASE)
            if match:
                return match.group(0)

        return None

    def _detectar_tipo_archivo(self, url: str) -> str:
        """Detecta el tipo de archivo desde la URL"""
        url_lower = url.lower()

        if '.pdf' in url_lower:
            return 'pdf'
        elif '.docx' in url_lower:
            return 'docx'
        elif '.doc' in url_lower:
            return 'doc'
        elif any(ext in url_lower for ext in ['.png', '.jpg', '.jpeg']):
            return 'jpg'
        else:
            return 'pdf'  # Asumir PDF por defecto

    def _limpiar_nombre(self, texto: str) -> str:
        """Limpia un texto para usarlo como nombre de archivo/directorio"""
        import re
        # Eliminar caracteres especiales
        texto = re.sub(r'[^\w\s-]', '', texto)
        # Reemplazar espacios con guiones bajos
        texto = re.sub(r'\s+', '_', texto)
        return texto[:50].lower()

    def obtener_estadisticas(self) -> Dict:
        """Devuelve estadísticas del scraping"""
        return self.estadisticas


if __name__ == "__main__":
    # Ejemplo de uso
    scraper = MultiSiteScraper()

    # Scrapear todos los sitios
    resultados = scraper.scrapear_todos_los_sitios(max_workers=3)

    print("\n" + "="*50)
    print("📊 RESUMEN DEL SCRAPING")
    print("="*50)
    print(f"✅ Sitios exitosos: {len(resultados['exitosos'])}")
    print(f"❌ Sitios fallidos: {len(resultados['fallidos'])}")
    print(f"📄 Total documentos: {resultados['total_documentos']}")
